
# B站UP主视频内容采集与Dify知识库集成系统 - MVP版

## 1. 项目概述

### 1.1 项目目标
采集B站指定UP主的视频内容，提取字幕或语音内容，转换为结构化文本，并集成到Dify本地部署版的知识库中，实现基于UP主视频内容的智能问答系统。

### 1.2 核心功能（MVP阶段）
- UP主视频信息批量采集
- 视频字幕/语音内容提取
- 文本结构化处理
- Dify知识库集成
- 基于知识库的问答服务

## 2. 技术实现方案

### 2.1 整体架构
```
b站UP主视频采集系统
├── 视频采集模块 (B站API接口封装)
├── 内容处理模块 (字幕提取/语音识别)
├── 文本结构化模块 (格式化处理)
└── Dify集成模块 (知识库API)
```

### 2.2 Dify本地部署
使用Docker Compose方式部署Dify平台，提供完整的知识库和问答能力：

```yaml
# docker-compose.yml
version: '3'
services:
  dify:
    image: langgenius/dify:latest
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/dify
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - dify-data:/data
    depends_on:
      - postgres
      - redis
      - weaviate
      
  postgres:
    image: postgres:14
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=dify
    volumes:
      - postgres-data:/var/lib/postgresql/data
      
  redis:
    image: redis:6
    volumes:
      - redis-data:/data
      
  weaviate:
    image: semitechnologies/weaviate:1.18.3
    volumes:
      - weaviate-data:/var/lib/weaviate

volumes:
  dify-data:
  postgres-data:
  redis-data:
  weaviate-data:
```

### 2.3 数据采集流程

#### 2.3.1 B站UP主视频采集
利用bilibili-api-python库实现对指定UP主视频的批量采集（或某个别的爬虫框架）：

1. 获取UP主信息和视频列表
2. 筛选目标视频（支持时间范围、播放量等条件）
3. 获取视频详情（标题、描述、发布时间等）
4. 下载字幕文件（如有）或视频文件（用于语音识别）

#### 2.3.2 内容提取处理
优先级处理方式：
1. 获取官方字幕（CC字幕）
2. 获取UP主自制字幕（如有）
3. 对无字幕视频进行音频提取和语音识别：
   - 提取音频使用FFmpeg
   - 语音识别使用Whisper（可本地部署或调用API）

#### 2.3.3 文本结构化处理
将提取的内容进行标准化处理：
1. 文本清洗（去除无意义内容、标点符号规范化）
2. 时间戳对齐
3. 格式转换（Markdown格式）
4. 分段处理（根据时间或语义进行合理分段）

### 2.4 Dify知识库集成

#### 2.4.1 知识库创建与管理
通过Dify API进行知识库管理：

#### 2.4.2 视频内容导入流程
1. 创建按UP主或主题分类的知识库
2. 将处理后的视频内容分批导入
3. 设置合适的分段和索引策略
4. 建立视频元数据（发布时间、播放量等信息）

### 2.5 应用集成与交互

#### 2.5.1 创建Dify应用
在Dify平台创建一个聊天助手应用：
1. 关联上述创建的知识库
2. 配置合适的LLM模型（可使用OpenAI、本地部署模型等）
3. 设置应用提示词（针对视频内容检索和解读进行优化）

#### 2.5.2 交互方式
1. Web界面直接访问
2. API接口调用
3. 可选集成到微信等聊天平台

## 3. 技术实施步骤

### 3.1 环境准备
1. Python 3.8+环境
2. Docker和Docker Compose
3. 本地服务器（推荐8GB+内存）

### 3.2 实施流程
1. Dify本地部署
   - 部署准备：
     1. 创建持久化存储目录：`mkdir -p /data/dify/{postgres,redis,weaviate}`
     2. 下载官方docker-compose模板：
        `wget -O docker-compose-dify.yml https://raw.githubusercontent.com/langgenius/dify/main/docker/docker-compose-dify.yml`
   - 启动核心服务：
     ```bash
     docker compose -f docker-compose-dify.yml up -d \
       --build \
       --env-file .env \
       --scale worker=2
     ```
     包含组件：
     - dify-web: 主Web服务（端口5000）
     - dify-worker: 异步任务处理
     - postgres/redis/weaviate: 依赖服务
   - 配置模型接口（修改.env）：
     ```properties
     # OpenAI
     OPENAI_API_KEY=sk-xxx
     OPENAI_API_BASE=https://api.openai.com/v1
     
     # 或本地模型
     LOCAL_MODEL_ENABLED=true
     LOCAL_MODEL_PROVIDER=ollama  # 支持ollama/vllm/tongyi
     OLLAMA_API_BASE=http://host.docker.internal:11434/v1
     MODEL_NAME=llama3:70b
     ```
   - 初始化验证：
     1. 检查服务状态：`docker compose -f docker-compose-dify.yml ps`
     2. 查看日志：`docker compose -f docker-compose-dify.yml logs -f dify-web`
     3. 访问管理界面：http://localhost:5000/ 验证安装
   - 创建知识库和应用：
     1. 通过API创建知识库：
        ```bash
        curl -X POST "http://localhost:5000/api/v1/knowledge-base" \
          -H "Authorization: Bearer {API_KEY}" \
          -d '{
            "name": "B站视频知识库",
            "description": "存储处理后的视频内容",
            "permission": "private",
            "embedding_model": "text-embedding-3-small",
            "chunk_size": 1000,
            "chunk_overlap": 200
          }'
        ```
     2. 创建问答应用：
        ```bash
        curl -X POST "http://localhost:5000/api/v1/app" \
          -H "Authorization: Bearer {API_KEY}" \
          -d '{
            "name": "视频内容助手",
            "model_config": {
              "provider": "openai",
              "model": "gpt-4-turbo-preview",
              "temperature": 0.7
            },
            "prompt": "你是一个专业视频内容助手，基于用户提供的B站视频知识库回答问题..."
          }'
        ```
   - 注意事项：
     * 需要安装NVIDIA Container Toolkit以支持GPU加速
     * 生产环境需配置HTTPS和访问控制
     * 建议分配至少4核CPU/16GB内存/20GB存储

2. 视频采集程序开发
   - 实现B站API封装
   - 开发视频信息和字幕采集功能
   - 实现视频下载和音频提取

3. 语音识别集成
   - 部署Whisper模型或接入API
   - 开发批处理音频文件功能

4. 文本处理模块
   - 开发文本清洗和格式化功能
   - 实现时间戳对齐和分段

5. Dify集成模块
   - 实现知识库API封装
   - 开发批量导入处理功能

### 3.3 数据处理格式
视频内容处理为统一的Markdown格式：
```markdown
# {视频标题}

## 基本信息
- BV号: {bvid}
- 发布时间: {publish_time}
- 时长: {duration}
- 播放量: {view_count}
- UP主: {up_name}

## 视频描述
{description}

## 内容概要
{summary}

## 详细内容
### {timestamp1}
{content1}

### {timestamp2}
{content2}
...
```

## 4. MVP验证方案

### 4.1 验证流程
1. 选择1-2个活跃UP主，采集10-20个视频
2. 完成采集、处理、导入流程
3. 创建基于视频内容的问答应用
4. 验证问答效果和知识库质量

### 4.2 评估指标
1. 采集成功率（成功采集的视频数/总视频数）
2. 内容提取质量（字幕/语音识别准确率）
3. 知识库导入成功率
4. 问答相关性评分（抽样测试问题的答案相关性）

## 5. 后续扩展规划

### 5.1 功能扩展
1. Web管理界面开发
2. 增量更新机制
3. 多UP主内容对比分析
4. 多模态内容处理（图片、表格等）

### 5.2 性能优化
1. 分布式采集和处理
2. 大规模数据存储优化
3. 知识库检索性能优化

### 5.3 应用场景拓展
1. UP主内容精华总结
2. 多UP主观点对比
3. 主题聚焦的专题知识库
4. 教程类内容的结构化学习系统

## 6. 注意事项
1. 遵守B站API使用规范和版权规定
2. 控制采集频率，避免IP封禁
3. 确保Dify本地部署的安全性和稳定性
4. 视频内容用于个人学习研究，不用于商业用途
