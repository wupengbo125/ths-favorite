#!/bin/bash

PROJECT_DIR="$github_dir/ths-favorite"
INPUT_FILE="$1"

if [ -z "$INPUT_FILE" ]; then
    echo "用法: $0 <csv或txt文件路径> [并发数]"
    exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
    echo "错误: 文件不存在: $INPUT_FILE"
    exit 1
fi

WORKERS="${2:-10}"

GROUP_NAME=$(basename "$INPUT_FILE")
GROUP_NAME="${GROUP_NAME%.csv}"
GROUP_NAME="${GROUP_NAME%.txt}"

echo "=== 开始处理: $GROUP_NAME ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
PYTHON_BIN="python3"
if [ -d "$PROJECT_DIR/.venv" ]; then
    PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
fi

if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

AUTH_ARGS=""
if [ -n "$USERNAME" ] && [ -n "$PASSWORD" ]; then
    AUTH_ARGS="--username=$USERNAME --password=$PASSWORD"
fi

output=$($PYTHON_BIN main.py $AUTH_ARGS 2>&1)
echo "$output"

if echo "$output" | grep -q "auth failed" && [ -n "$USERNAME" ] && [ -n "$PASSWORD" ]; then
    $PYTHON_BIN main.py --username="$USERNAME" --password="$PASSWORD"
fi

$PYTHON_BIN "$PROJECT_DIR/batch_add.py" "$INPUT_FILE" --workers "$WORKERS" $AUTH_ARGS

echo "=== 完成 ==="