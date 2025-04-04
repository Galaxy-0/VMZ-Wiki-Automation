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

# 删除应用部署
echo "删除应用部署..."
$KUBECTL delete -f deployment.yaml --ignore-not-found

# 删除服务
echo "删除服务..."
$KUBECTL delete -f services.yaml --ignore-not-found

# 删除数据库
echo "删除数据库..."
$KUBECTL delete -f database.yaml --ignore-not-found

# 删除命名空间和RBAC
echo "删除命名空间和RBAC..."
$KUBECTL delete -f namespace.yaml --ignore-not-found

# 删除持久化存储
echo "删除持久化存储..."
$KUBECTL delete pvc -l app=vmz-wiki-mongodb -n $NAMESPACE --ignore-not-found
$KUBECTL delete pvc -l app=vmz-wiki-redis -n $NAMESPACE --ignore-not-found
$KUBECTL delete pvc -l app=vmz-wiki -n $NAMESPACE --ignore-not-found

# 检查清理结果
echo "检查清理结果..."
$KUBECTL get all -n $NAMESPACE --ignore-not-found
$KUBECTL get pvc -n $NAMESPACE --ignore-not-found

echo "清理完成！" 