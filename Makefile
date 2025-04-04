 .PHONY: install test lint format clean docker-build docker-push k8s-deploy k8s-cleanup

# 设置Python解释器
PYTHON = python3
PIP = pip3

# 设置目录
SRC_DIR = src
TEST_DIR = tests
VENV_DIR = .venv

# 安装依赖
install:
	$(PYTHON) -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && $(PIP) install -r requirements.txt

# 运行测试
test:
	. $(VENV_DIR)/bin/activate && pytest $(TEST_DIR)/ --cov=$(SRC_DIR) --cov-report=term-missing

# 代码检查
lint:
	. $(VENV_DIR)/bin/activate && black . --check
	. $(VENV_DIR)/bin/activate && isort . --check-only
	. $(VENV_DIR)/bin/activate && pylint $(SRC_DIR)/ $(TEST_DIR)/
	. $(VENV_DIR)/bin/activate && mypy $(SRC_DIR)/
	. $(VENV_DIR)/bin/activate && flake8

# 代码格式化
format:
	. $(VENV_DIR)/bin/activate && black .
	. $(VENV_DIR)/bin/activate && isort .

# 清理
clean:
	rm -rf $(VENV_DIR)
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf .tox
	rm -rf .eggs
	rm -rf *.egg-info
	rm -rf build
	rm -rf dist
	rm -rf data
	rm -rf logs

# Docker构建
docker-build:
	docker build -t vmz-wiki-automation .

# Docker推送
docker-push:
	docker tag vmz-wiki-automation yourusername/vmz-wiki-automation:latest
	docker push yourusername/vmz-wiki-automation:latest

# Kubernetes部署
k8s-deploy:
	chmod +x k8s/deploy.sh
	./k8s/deploy.sh

# Kubernetes清理
k8s-cleanup:
	chmod +x k8s/cleanup.sh
	./k8s/cleanup.sh

# 开发环境设置
dev: install format lint test

# 生产环境部署
prod: docker-build docker-push k8s-deploy