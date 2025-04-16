#!/bin/bash

# MySQL凭证 - 请替换为您的实际用户名和密码
MYSQL_USER="root"
MYSQL_PASSWORD="WJmysql123"

# 检查MySQL是否已运行
if pgrep mysqld >/dev/null; then
    echo "MySQL服务已在运行中，跳过启动步骤"
else
    echo "正在启动MySQL服务..."
    # 使用Homebrew启动MySQL（因为您是在Mac上用Homebrew安装的）
    brew services start mysql
    sleep 3  # 等待服务启动
    echo "MySQL服务启动命令已执行"
fi

# 测试连接
echo "正在测试MySQL连接..."
if mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" --skip-column-names -e "" 2>/dev/null; then
    echo "MySQL连接成功!"
else
    echo "MySQL连接失败。请检查以下可能的问题："
    echo "1. 用户名或密码不正确"
    echo "2. 该用户可能没有足够权限"
    echo "3. 可能需要指定主机（如果不是localhost）"
    
    # 尝试使用不同的方式连接
    echo "尝试使用交互方式测试连接..."
    echo "请手动输入MySQL密码："
    mysql -u"$MYSQL_USER" -p
    
    read -p "连接测试是否成功？(y/n): " connection_success
    if [ "$connection_success" != "y" ]; then
        echo "MySQL连接问题未解决，退出脚本"
        exit 1
    fi
fi

echo "正在启动Docker Compose服务..."
cd "$(dirname "$0")"  # 切换到脚本所在目录
docker-compose up -d
echo "Docker Compose服务已启动"

echo "所有服务已成功启动!"