# BiliNote Docker YouTube Proxy Edition

这是基于原开源项目 [BiliNote](https://github.com/JefferyHcool/BiliNote) 调整的本地 Docker 部署版本，主要补充了在国内网络环境下部署和使用 YouTube 的相关配置。

## 项目简介

BiliNote 是一个 AI 视频笔记助手，支持通过哔哩哔哩、YouTube、抖音等视频链接生成结构化 Markdown 笔记。

本仓库在原项目基础上，重点整理和调整了以下内容：

- Docker 本地部署流程
- Docker Hub 国内镜像源配置
- npm/pnpm 国内镜像源配置
- YouTube 下载代理配置
- YouTube Cookie 配置
- AI 代理与 YouTube 代理分开配置
- Docker 环境下访问宿主机代理

## 安装与配置

Docker 本地部署、国内镜像源、YouTube 代理与 Cookie 配置请看：

[Docker 部署与 YouTube 配置说明](./INSTALL_DOCKER_YOUTUBE_PROXY.md)

## 本仓库说明

这个仓库主要用于保存我自己的 BiliNote Docker 本地部署配置和调试后的改动，方便后续重新部署、迁移机器或同步到自己的 GitHub 仓库。

本地敏感配置不会提交到 Git：

- `.env`
- `backend/config/downloader.json`
- `backend/config/proxy.json`
- `backend/config/transcriber.json`

这些文件可能包含端口、代理、Cookie、模型配置等本机信息。

## 原项目 README

原项目说明请查看：

[README_ORIGINAL.md](./README_ORIGINAL.md)

## License

原项目采用 MIT License。使用、修改和分发时请保留原项目的版权与许可证说明。
