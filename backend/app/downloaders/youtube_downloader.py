import os
import logging
import re
import tempfile
from abc import ABC
from typing import Union, Optional, List

import yt_dlp

from app.downloaders.base import Downloader, DownloadQuality
from app.downloaders.youtube_subtitle import YouTubeSubtitleFetcher
from app.models.notes_model import AudioDownloadResult
from app.models.transcriber_model import TranscriptResult
from app.services.cookie_manager import CookieConfigManager
from app.services.proxy_config_manager import ProxyConfigManager
from app.utils.path_helper import get_data_dir
from app.utils.url_parser import extract_video_id

logger = logging.getLogger(__name__)


def _apply_proxy(ydl_opts: dict) -> dict:
    """YouTube 在国内需要代理。配置了全局代理就塞进 yt-dlp opts。"""
    proxy = ProxyConfigManager().get_youtube_proxy_url()
    if proxy:
        ydl_opts['proxy'] = proxy
        logger.info(f"yt-dlp 走代理: {proxy}")
    return ydl_opts


def _write_youtube_cookie_file() -> Optional[str]:
    """Write configured YouTube cookies as a Netscape cookie file for yt-dlp."""
    cookie = CookieConfigManager().get('youtube')
    if not cookie:
        logger.warning("YouTube Cookie 未配置，下载可能触发登录/风控校验")
        return None

    cookie = cookie.strip()
    if "\t" in cookie and (cookie.startswith("# Netscape") or ".youtube.com" in cookie):
        lines = cookie.splitlines(keepends=True)
        if len(lines) <= 1:
            lines = ["# Netscape HTTP Cookie File\n"]
            pattern = r"\.youtube\.com\t(?:TRUE|FALSE)\t[^\t]+\t(?:TRUE|FALSE)\t\d+\t[^\t]+\t[^\s]+"
            lines.extend(match.group(0) + "\n" for match in re.finditer(pattern, cookie))
    else:
        lines = ["# Netscape HTTP Cookie File\n"]
        for pair in cookie.split(";"):
            pair = pair.strip()
            if "=" not in pair:
                continue
            key, value = pair.split("=", 1)
            key = key.strip()
            if not key:
                continue
            lines.append(f".youtube.com\tTRUE\t/\tTRUE\t0\t{key}\t{value.strip()}\n")

    if len(lines) == 1:
        return None

    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
    tmp.writelines(lines)
    tmp.close()
    logger.info("已生成 YouTube Netscape Cookie 文件: %s (条目: %d)", tmp.name, len(lines) - 1)
    return tmp.name


def _apply_cookiefile(ydl_opts: dict) -> dict:
    cookiefile = _write_youtube_cookie_file()
    if cookiefile:
        ydl_opts['cookiefile'] = cookiefile
    return ydl_opts


def _youtube_base_opts() -> dict:
    return {
        'noplaylist': True,
        'quiet': False,
        'js_runtimes': {'deno': {}, 'node': {}},
        'remote_components': ['ejs:github'],
    }


class YoutubeDownloader(Downloader, ABC):
    def __init__(self):

        super().__init__()

    def download(
        self,
        video_url: str,
        output_dir: Union[str, None] = None,
        quality: DownloadQuality = "fast",
        need_video: Optional[bool] = False,
        skip_download: bool = False,
    ) -> AudioDownloadResult:
        if output_dir is None:
            output_dir = get_data_dir()
        if not output_dir:
            output_dir = self.cache_data
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, "%(id)s.%(ext)s")

        ydl_opts = {
            **_youtube_base_opts(),
            'format': 'bestaudio/best',
            'outtmpl': output_path,
        }

        if skip_download:
            ydl_opts['skip_download'] = True

        _apply_cookiefile(ydl_opts)
        _apply_proxy(ydl_opts)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=not skip_download)
            video_id = info.get("id")
            title = info.get("title")
            duration = info.get("duration", 0)
            cover_url = info.get("thumbnail")
            ext = info.get("ext", "m4a")
            audio_path = os.path.join(output_dir, f"{video_id}.{ext}")

        return AudioDownloadResult(
            file_path=audio_path,
            title=title,
            duration=duration,
            cover_url=cover_url,
            platform="youtube",
            video_id=video_id,
            raw_info={'tags': info.get('tags')},
            video_path=None,
        )

    def download_video(
        self,
        video_url: str,
        output_dir: Union[str, None] = None,
    ) -> str:
        """
        下载视频，返回视频文件路径
        """
        if output_dir is None:
            output_dir = get_data_dir()
        video_id = extract_video_id(video_url, "youtube")
        video_path = os.path.join(output_dir, f"{video_id}.mp4")
        if os.path.exists(video_path):
            return video_path
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "%(id)s.%(ext)s")

        ydl_opts = {
            **_youtube_base_opts(),
            'format': 'bestvideo*+bestaudio/best',
            'outtmpl': output_path,
            'merge_output_format': 'mp4',  # 确保合并成 mp4
        }

        _apply_cookiefile(ydl_opts)
        _apply_proxy(ydl_opts)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            video_id = info.get("id")
            video_path = os.path.join(output_dir, f"{video_id}.mp4")

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件未找到: {video_path}")

        return video_path

    def download_subtitles(self, video_url: str, output_dir: str = None,
                           langs: List[str] = None) -> Optional[TranscriptResult]:
        """
        通过 YouTube InnerTube API 直接获取字幕（优先人工字幕，其次自动生成）。
        比 yt_dlp 方式更轻量，无需写临时文件到磁盘。

        :param video_url: 视频链接
        :param output_dir: 未使用（保留接口兼容）
        :param langs: 优先语言列表
        :return: TranscriptResult 或 None
        """
        if langs is None:
            langs = ['zh-Hans', 'zh', 'zh-CN', 'zh-TW', 'en', 'en-US', 'ja']

        video_id = extract_video_id(video_url, "youtube")
        fetcher = YouTubeSubtitleFetcher()
        print(
            f"尝试获取字幕，video_id={video_id}, langs={langs}"
        )
        return fetcher.fetch_subtitles(video_id, langs)
