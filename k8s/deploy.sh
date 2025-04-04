#!/bin/bash

# 设置错误时退出
set -e

# 设置变量
NAMESPACE="vmz-wiki"
KUBECTL="kubectl"

# 检查kubectl是否安装
if ! command -v $KUBECTL &> /dev/null; then
    echo "kubectl未安装，请先安装kubectl"
    exit 1
fi

# 检查kubectl是否连接到集群
if ! $KUBECTL cluster-info &> /dev/null; then
    echo "kubectl未连接到集群，请先配置kubectl"
    exit 1
fi

# 创建命名空间和RBAC
echo "创建命名空间和RBAC..."
$KUBECTL apply -f namespace.yaml

# 创建数据库
echo "部署数据库..."
$KUBECTL apply -f database.yaml

# 等待数据库就绪
echo "等待数据库就绪..."
$KUBECTL wait --for=condition=ready pod -l app=vmz-wiki-mongodb -n $NAMESPACE --timeout=300s
$KUBECTL wait --for=condition=ready pod -l app=vmz-wiki-redis -n $NAMESPACE --timeout=300s

# 创建服务
echo "创建服务..."
$KUBECTL apply -f services.yaml

# 部署应用
echo "部署应用..."
$KUBECTL apply -f deployment.yaml

# 等待应用就绪
echo "等待应用就绪..."
$KUBECTL wait --for=condition=ready pod -l app=vmz-wiki -n $NAMESPACE --timeout=300s

# 检查部署状态
echo "检查部署状态..."
$KUBECTL get pods -n $NAMESPACE

# 获取服务访问信息
echo "获取服务访问信息..."
$KUBECTL get svc -n $NAMESPACE

echo "部署完成！" 