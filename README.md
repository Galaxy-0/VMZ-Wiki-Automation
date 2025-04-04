# VMZ-Wiki
a automation framework about bili2text for VMZ-wiki.
# VMZ Wiki 自动化工具

这是一个用于自动化处理Bilibili视频并生成Wiki文档的工具。它可以自动下载视频、提取音频、进行语音识别，并生成结构化的Markdown文档。

## 功能特点

- 自动获取UP主视频列表
- 智能视频筛选
- 视频下载和音频提取
- 音频分段处理
- 语音识别转写
- Markdown文档生成
- 存储空间管理
- 任务队列管理
- 数据库持久化
- 完整的日志记录

## 系统要求

- Python 3.8+
- FFmpeg
- CUDA支持（用于语音识别）
- MongoDB
- Redis

## 安装步骤

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/VMZ-Wiki-Automation.git
cd VMZ-Wiki-Automation
```

2. 创建虚拟环境：
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境：
- 复制`config.yaml.example`为`config.yaml`
- 修改配置文件中的相关参数
- 设置必要的环境变量

## 使用方法

1. 运行主程序：
```bash
python src/main.py
```

2. 运行测试：
```bash
pytest
```

3. 代码格式化：
```bash
black .
isort .
```

4. 代码检查：
```bash
pylint src/
mypy src/
flake8
```

## 项目结构

```
VMZ-Wiki-Automation/
├── src/
│   ├── collectors/      # 视频采集模块
│   ├── processors/      # 处理模块
│   ├── generators/      # 文档生成模块
│   ├── managers/        # 管理模块
│   ├── filters/         # 过滤模块
│   └── main.py         # 主程序入口
├── tests/              # 测试目录
├── templates/          # 模板目录
├── data/              # 数据目录
├── logs/              # 日志目录
├── config.yaml        # 配置文件
├── requirements.txt   # 依赖文件
└── README.md         # 项目说明
```

## 配置说明

主要配置项包括：

- Bilibili API配置
- 音频处理配置
- 语音识别配置
- Markdown生成配置
- 存储管理配置
- 数据库配置
- 视频过滤配置
- 任务管理配置

详细配置说明请参考`config.yaml`文件中的注释。

## 开发计划

- [ ] 支持更多视频平台
- [ ] 优化语音识别准确率
- [ ] 添加更多文档模板
- [ ] 实现Web管理界面
- [ ] 添加API接口
- [ ] 支持分布式部署

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License

## 联系方式

- 作者：Your Name
- 邮箱：your.email@example.com
- 项目主页：https://github.com/yourusername/VMZ-Wiki-Automation