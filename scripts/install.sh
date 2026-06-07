#!/usr/bin/env bash
# scripts/install.sh — ai-write-flow Skill 安装脚本
# 只复制 skill/ 目录内容到目标 Skills 目录，不复制 workspace/、docs/、evals/

set -e

SKILL_NAME="ai-write-flow"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$SCRIPT_DIR/../skill"

echo "========================================="
echo " ai-write-flow Skill 安装向导"
echo "========================================="
echo ""

# ─── 验证 Skill 源目录 ──────────────────────────────────────────────────────
if [ ! -f "$SKILL_SRC/SKILL.md" ]; then
    echo "错误：在 $SKILL_SRC 下找不到 SKILL.md"
    echo "请确保从项目根目录或 scripts/ 目录内执行此脚本"
    exit 1
fi

# ─── 选择安装模式 ────────────────────────────────────────────────────────────
echo "请选择安装模式："
echo "  1) 个人本地模式（默认 workspace: /Users/zhaodonglin/Documents/ai-write-flow/workspace）"
echo "  2) 开源通用模式（自定义 workspace 路径）"
echo ""
read -r MODE_CHOICE

WORKSPACE_PATH=""
case "$MODE_CHOICE" in
    2)
        # 开源通用模式：优先读取环境变量，否则询问
        if [ -n "$AI_WRITE_FLOW_WORKSPACE" ]; then
            WORKSPACE_PATH="$AI_WRITE_FLOW_WORKSPACE"
            echo "检测到环境变量 AI_WRITE_FLOW_WORKSPACE，使用：$WORKSPACE_PATH"
        else
            echo "请输入你的 workspace 路径（或设置环境变量 AI_WRITE_FLOW_WORKSPACE 后重新运行）："
            read -r WORKSPACE_PATH
            WORKSPACE_PATH="${WORKSPACE_PATH/#\~/$HOME}"
            if [ -z "$WORKSPACE_PATH" ]; then
                echo "错误：未提供 workspace 路径"
                echo "提示：可在 shell 配置中添加：export AI_WRITE_FLOW_WORKSPACE=/your/workspace"
                exit 1
            fi
        fi
        ;;
    *)
        # 个人本地模式（默认）
        WORKSPACE_PATH="/Users/zhaodonglin/Documents/ai-write-flow/workspace"
        echo "个人本地模式，workspace 固定为：$WORKSPACE_PATH"
        ;;
esac

echo ""

# ─── 初始化 workspace 目录 ──────────────────────────────────────────────────
echo "正在初始化 workspace 目录..."
mkdir -p "$WORKSPACE_PATH/briefs"
mkdir -p "$WORKSPACE_PATH/research"
mkdir -p "$WORKSPACE_PATH/output"
mkdir -p "$WORKSPACE_PATH/images"

echo "  ✓ briefs/    已就绪（放入写作素材）"
echo "  ✓ research/  已就绪（调研 JSON 输出）"
echo "  ✓ output/    已就绪（成品文章输出）"
echo "  ✓ images/    已就绪（配图输出，可选）"
echo ""

# ─── 安装 Skill 到工具目录 ──────────────────────────────────────────────────
echo "请选择要安装到哪个工具的 Skills 目录："
echo "  1) Claude Code  (~/.claude/skills/)"
echo "  2) 手动指定路径"
echo "  3) 跳过（仅初始化 workspace）"
echo ""
read -r TOOL_CHOICE

DEST=""
case "$TOOL_CHOICE" in
    1)
        SKILLS_DIR="$HOME/.claude/skills"
        mkdir -p "$SKILLS_DIR"
        DEST="$SKILLS_DIR/$SKILL_NAME"
        ;;
    2)
        echo "请输入目标 Skills 目录路径："
        read -r CUSTOM_SKILLS_DIR
        CUSTOM_SKILLS_DIR="${CUSTOM_SKILLS_DIR/#\~/$HOME}"
        if [ ! -d "$CUSTOM_SKILLS_DIR" ]; then
            echo "错误：目录不存在：$CUSTOM_SKILLS_DIR"
            exit 1
        fi
        DEST="$CUSTOM_SKILLS_DIR/$SKILL_NAME"
        ;;
    3)
        echo "  跳过 Skill 安装，仅完成 workspace 初始化。"
        ;;
    *)
        echo "  无效选择，跳过 Skill 安装。"
        ;;
esac

if [ -n "$DEST" ]; then
    if [ -d "$DEST" ]; then
        echo "检测到已安装的旧版本，是否覆盖？(y/n)"
        read -r OVERWRITE
        if [ "$OVERWRITE" != "y" ]; then
            echo "已取消覆盖，保留旧版本。"
            DEST=""
        fi
    fi
fi

if [ -n "$DEST" ]; then
    rsync -a --delete \
        --exclude='.git/' \
        --exclude='.DS_Store' \
        "$SKILL_SRC/" "$DEST/"
    echo "  ✓ Skill 已安装到：$DEST"
fi

# ─── 完成提示 ────────────────────────────────────────────────────────────────
echo ""
echo "========================================="
echo " 安装完成！"
echo "========================================="
echo ""
echo "下一步："
echo ""
if [ -n "$DEST" ]; then
    echo "  1. 根据需要调整作者画像（可选）："
    echo "     $DEST/references/persona.md"
    echo ""
    echo "  2. 将写作素材放入 workspace/briefs/："
    echo "     $WORKSPACE_PATH/briefs/"
else
    echo "  1. 手动复制 Skill 后再配置 persona.md"
fi
echo ""
echo "  3. 在 Claude Code 中说："
echo "     '帮我写一篇关于 [主题] 的文章'"
echo "     或 '帮我审校这篇文章，降低AI味'"
echo ""
