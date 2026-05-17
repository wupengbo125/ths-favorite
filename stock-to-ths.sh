#!/bin/bash

PROJECT_DIR="/home/pengbo/home/github/ths-favorite"
TXT_FILE="$1"

if [ -z "$TXT_FILE" ]; then
    echo "用法: $0 <txt文件路径> [并发数]"
    exit 1
fi

if [ ! -f "$TXT_FILE" ]; then
    echo "错误: 文件不存在: $TXT_FILE"
    exit 1
fi

WORKERS="${2:-10}"

GROUP_NAME=$(basename "$TXT_FILE" .txt)

echo "=== 开始处理: $GROUP_NAME ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
set -a
source "$SCRIPT_DIR/.env"
set +a

output=$(python main.py 2>&1)
echo "$output"

if echo "$output" | grep -q "auth failed"; then
    python main.py --username="$USERNAME" --password="$PASSWORD"
fi

python "$PROJECT_DIR/batch_add.py" "$TXT_FILE" --workers "$WORKERS" --username "$USERNAME" --password "$PASSWORD"

echo "=== 完成 ==="