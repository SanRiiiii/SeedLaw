#!/bin/bash
echo "正在关闭Docker Compose服务..."
cd "$(dirname "$0")"
docker-compose down
echo "Docker Compose服务已关闭"

echo "正在关闭MySQL服务..."
brew services stop mysql
echo "MySQL服务已关闭"

echo "所有服务已成功关闭!"