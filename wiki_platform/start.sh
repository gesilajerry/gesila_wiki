#!/bin/bash
# Jerry Wiki Platform - 启动脚本
# 用法: ./start.sh [port]
# 先配置 ngrok_token.txt 启用公网访问

PORT=${1:-5001}
WIKI_DIR="$(dirname "$0")"

echo "============================================"
echo " Jerry Wiki Platform 启动中..."
echo " 本地地址: http://localhost:$PORT"
echo "============================================"

cd "$WIKI_DIR"

# 检查 ngrok token
if [ -f ngrok_token.txt ]; then
    TOKEN=$(cat ngrok_token.txt | tr -d ' \n')
    if [ -n "$TOKEN" ]; then
        echo "[Ngrok] Token 已配置，启用公网访问..."
    else
        echo "[Ngrok] Token 文件为空，跳过公网访问"
    fi
else
    echo "[Ngrok] ngrok_token.txt 不存在，跳过公网访问"
    echo "        配置方法: echo 'YOUR_TOKEN' > ngrok_token.txt"
fi

# 杀掉旧进程
lsof -ti:$PORT | xargs kill -9 2>/dev/null
sleep 1

# 启动
nohup python3 app.py > wiki.log 2>&1 &
PID=$!
echo "PID: $PID"
echo "日志: $WIKI_DIR/wiki.log"
sleep 3

# 检查是否成功
if curl -s http://localhost:$PORT/ > /dev/null; then
    echo "✅ 启动成功: http://localhost:$PORT"
    echo "============================================"
else
    echo "❌ 启动失败，请查看 wiki.log"
fi
