# 使用CUDA基础镜像
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 安装Python依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 创建必要的目录
RUN mkdir -p data/{audio,transcripts,markdown,hot,cold,temp} logs

# 设置环境变量
ENV PYTHONPATH=/app/src

# 设置入口点
ENTRYPOINT ["python3", "src/main.py"] 