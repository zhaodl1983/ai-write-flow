#!/usr/bin/env bash
# scripts/package-skill.sh — 将 skill/ 打包为可分发的 zip 文件
# zip 内根目录为 ai-write-flow/，与 SKILL.md name 字段一致

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$SCRIPT_DIR/../skill"
OUTPUT_DIR="${1:-$SCRIPT_DIR/../dist}"
VERSION="${2:-$(date +%Y%m%d)}"
ARCHIVE_NAME="ai-write-flow-skill-$VERSION.zip"

if [ ! -f "$SKILL_SRC/SKILL.md" ]; then
    echo "错误：在 $SKILL_SRC 下找不到 SKILL.md"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
OUTPUT_PATH="$OUTPUT_DIR/$ARCHIVE_NAME"

# 创建临时目录，以 ai-write-flow/ 为根目录名打包
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

cp -r "$SKILL_SRC" "$TEMP_DIR/ai-write-flow"

cd "$TEMP_DIR"
zip -r "$OUTPUT_PATH" ai-write-flow/ \
    --exclude "*.DS_Store" \
    --exclude "*__pycache__*" \
    --exclude "*.pyc"

echo "已打包：$OUTPUT_PATH"
echo "包含内容："
unzip -l "$OUTPUT_PATH" | grep -v "^Archive" | grep -v "^---" | grep -v "^[0-9]* file"
