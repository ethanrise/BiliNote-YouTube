# BASE_REGISTRY 默认走 docker.io；国内拉不到 docker.io 时可换可用镜像源：
#   docker-compose build --build-arg BASE_REGISTRY=dockerproxy.net
# 或写到 docker-compose.yml 的 build.args / 环境变量里
ARG BASE_REGISTRY=docker.io
FROM ${BASE_REGISTRY}/library/python:3.11-slim

ARG APT_MIRROR=mirrors.tuna.tsinghua.edu.cn
ARG PIP_INDEX=https://pypi.tuna.tsinghua.edu.cn/simple
ARG DENO_DOWNLOAD_PROXY=

RUN rm -f /etc/apt/sources.list && \
    rm -rf /etc/apt/sources.list.d/* && \
    echo "deb https://${APT_MIRROR}/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://${APT_MIRROR}/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://${APT_MIRROR}/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl unzip ca-certificates && \
    curl -fsSL ${DENO_DOWNLOAD_PROXY:+-x ${DENO_DOWNLOAD_PROXY}} -o /tmp/deno.zip https://github.com/denoland/deno/releases/download/v2.9.2/deno-x86_64-unknown-linux-gnu.zip && \
    unzip /tmp/deno.zip -d /usr/local/bin && \
    chmod +x /usr/local/bin/deno && \
    rm -f /tmp/deno.zip && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/usr/bin:${PATH}"
ENV HF_ENDPOINT=https://hf-mirror.com

WORKDIR /app

# 先复制 requirements.txt 利用层缓存
COPY ./backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -i ${PIP_INDEX} -r requirements.txt

# 再复制应用代码（频繁变动不影响 pip 缓存层）
COPY ./backend /app

CMD ["python", "main.py"]
