import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ProxyConfigManager:
    """分场景代理配置，存 JSON 文件，支持前端动态修改。

    作用范围：
      - ai: LLM API + 转写 API（Groq 等）
      - youtube: yt-dlp 下载 + YouTube 字幕

    兼容旧配置：旧版 {enabled, url} 会作为 youtube 配置读取，避免升级后
    YouTube 下载代理失效。环境变量仍作为兜底代理。
    """

    def __init__(self, filepath: str = "config/proxy.json"):
        self.path = Path(filepath)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write(self, data: Dict[str, Any]):
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _empty_config() -> Dict[str, str | bool]:
        return {"enabled": False, "url": ""}

    def _section_config(self, data: Dict[str, Any], section: str) -> Dict[str, str | bool]:
        cfg = data.get(section)
        if isinstance(cfg, dict):
            return {
                "enabled": bool(cfg.get("enabled", False)),
                "url": cfg.get("url", "") or "",
            }
        if section == "youtube" and ("enabled" in data or "url" in data):
            return {
                "enabled": bool(data.get("enabled", False)),
                "url": data.get("url", "") or "",
            }
        return self._empty_config()

    def get_config(self) -> Dict[str, Any]:
        data = self._read()
        return {
            "ai": self._section_config(data, "ai"),
            "youtube": self._section_config(data, "youtube"),
        }

    def update_config(
        self,
        *,
        ai: Optional[Dict[str, Any]] = None,
        youtube: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        data = self._read()
        for section, cfg in (("ai", ai), ("youtube", youtube)):
            if cfg is None:
                continue
            current = self._section_config(data, section)
            current["enabled"] = bool(cfg.get("enabled", current["enabled"]))
            if "url" in cfg:
                current["url"] = (cfg.get("url") or "").strip()
            data[section] = current
        data.pop("enabled", None)
        data.pop("url", None)
        self._write(data)
        return self.get_config()

    @staticmethod
    def _env_proxy_url() -> Optional[str]:
        for key in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"):
            val = os.environ.get(key)
            if val:
                return val
        return None

    def get_proxy_url(self, section: str = "youtube") -> Optional[str]:
        """返回当前生效的代理 URL；没有则 None。

        - 指定 section 配置文件 enabled=true 且 url 非空 → 用配置的 url
        - 否则回退到环境变量（标准的 HTTP_PROXY / HTTPS_PROXY / ALL_PROXY，大小写都认）
        """
        cfg = self.get_config().get(section) or self._empty_config()
        if cfg["enabled"] and cfg["url"]:
            return cfg["url"]
        return self._env_proxy_url()

    def get_ai_proxy_url(self) -> Optional[str]:
        return self.get_proxy_url("ai")

    def get_youtube_proxy_url(self) -> Optional[str]:
        return self.get_proxy_url("youtube")
