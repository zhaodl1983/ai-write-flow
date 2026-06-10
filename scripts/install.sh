#!/usr/bin/env bash
# scripts/install.sh — ai-write-flow Agent Skill 安装脚本
# 支持 Hermes / Claude Code / Codex / Custom 目录
# 只复制 skill/ 目录内容，不复制 workspace/、docs/、evals/
#
# 用法：
#   bash scripts/install.sh --tool hermes
#   bash scripts/install.sh --tool claude-code
#   bash scripts/install.sh --tool codex
#   bash scripts/install.sh --tool custom --skills-dir /path/to/skills
#   bash scripts/install.sh --tool hermes --workspace ~/Documents/workspace/ai-write-flow
#   bash scripts/install.sh --tool auto
#   bash scripts/install.sh          # 交互式选择

set -e

SKILL_NAME="ai-write-flow"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$SCRIPT_DIR/../skill"

# ─── 解析参数 ────────────────────────────────────────────────────────────────

TOOL=""
WORKSPACE_ARG=""
SKILLS_DIR_ARG=""

VALID_TOOLS="hermes claude-code codex custom auto skip"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --tool)
            TOOL="$2"
            if [[ ! " $VALID_TOOLS " =~ " $TOOL " ]]; then
                echo "错误：不支持的 --tool 值：$TOOL"
                echo "支持的值：hermes | claude-code | codex | custom | auto"
                echo "用法：bash scripts/install.sh [--tool hermes|claude-code|codex|custom|auto] [--workspace PATH] [--skills-dir PATH]"
                exit 1
            fi
            shift 2
            ;;
        --workspace)
            WORKSPACE_ARG="${2/#\~/$HOME}"
            shift 2
            ;;
        --skills-dir)
            SKILLS_DIR_ARG="${2/#\~/$HOME}"
            shift 2
            ;;
        *)
            echo "未知参数：$1"
            echo "用法：bash scripts/install.sh [--tool hermes|claude-code|codex|custom|auto] [--workspace PATH] [--skills-dir PATH]"
            exit 1
            ;;
    esac
done

echo "========================================="
echo " ai-write-flow Agent Skill 安装向导"
echo "========================================="
echo ""

# ─── 验证 Skill 源目录 ──────────────────────────────────────────────────────
if [ ! -f "$SKILL_SRC/SKILL.md" ]; then
    echo "错误：在 $SKILL_SRC 下找不到 SKILL.md"
    echo "请确保从项目根目录或 scripts/ 目录内执行此脚本"
    exit 1
fi

# ─── 目录检测函数 ────────────────────────────────────────────────────────────

detect_tools() {
    local found=()
    [ -d "${HERMES_SKILLS_DIR:-$HOME/.hermes/skills}" ] && found+=("hermes")
    [ -d "${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}" ] && found+=("claude-code")
    [ -d "${CODEX_HOME:-$HOME/.codex}/skills" ] && found+=("codex")
    echo "${found[@]}"
}

resolve_skills_dir() {
    local tool="$1"
    case "$tool" in
        hermes)
            echo "${HERMES_SKILLS_DIR:-$HOME/.hermes/skills}"
            ;;
        claude-code)
            echo "${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
            ;;
        codex)
            echo "${CODEX_HOME:-$HOME/.codex}/skills"
            ;;
        custom)
            echo "$SKILLS_DIR_ARG"
            ;;
    esac
}

tool_display_name() {
    case "$1" in
        hermes)      echo "Hermes" ;;
        claude-code) echo "Claude Code" ;;
        codex)       echo "Codex" ;;
        custom)      echo "Custom" ;;
        *)           echo "$1" ;;
    esac
}

# ─── 选择安装工具 ────────────────────────────────────────────────────────────

if [ -z "$TOOL" ]; then
    echo "请选择安装目标："
    echo "  1) Hermes        (~/.hermes/skills)"
    echo "  2) Claude Code   (~/.claude/skills)"
    echo "  3) Codex         (~/.codex/skills)"
    echo "  4) Custom        （手动指定 Skills 目录）"
    echo "  5) 仅初始化 workspace，跳过 Skill 安装"
    echo ""
    printf "请输入编号："
    read -r MENU_CHOICE
    case "$MENU_CHOICE" in
        1) TOOL="hermes" ;;
        2) TOOL="claude-code" ;;
        3) TOOL="codex" ;;
        4) TOOL="custom" ;;
        5) TOOL="skip" ;;
        *)
            echo "无效选择，退出。"
            exit 1
            ;;
    esac
    echo ""
fi

if [ "$TOOL" = "auto" ]; then
    read -ra FOUND_TOOLS <<< "$(detect_tools)"
    if [ ${#FOUND_TOOLS[@]} -eq 0 ]; then
        echo "未检测到已安装的 Agent 工具目录（hermes / claude-code / codex）。"
        echo "请使用 --tool custom --skills-dir /path/to/skills 指定目标目录。"
        exit 1
    elif [ ${#FOUND_TOOLS[@]} -eq 1 ]; then
        TOOL="${FOUND_TOOLS[0]}"
        echo "检测到工具：$(tool_display_name "$TOOL")，将安装到对应目录。"
        echo ""
    else
        echo "检测到多个已安装工具，请选择安装目标："
        for i in "${!FOUND_TOOLS[@]}"; do
            dir="$(resolve_skills_dir "${FOUND_TOOLS[$i]}")"
            echo "  $((i+1))) $(tool_display_name "${FOUND_TOOLS[$i]}")  ($dir)"
        done
        echo ""
        printf "请输入编号："
        read -r AUTO_CHOICE
        idx=$((AUTO_CHOICE - 1))
        if [ "$idx" -lt 0 ] || [ "$idx" -ge ${#FOUND_TOOLS[@]} ]; then
            echo "无效选择，退出。"
            exit 1
        fi
        TOOL="${FOUND_TOOLS[$idx]}"
        echo ""
    fi
fi

# ─── 解析目标 Skills 目录 ────────────────────────────────────────────────────

DEST=""
if [ "$TOOL" != "skip" ]; then
    if [ "$TOOL" = "custom" ]; then
        if [ -z "$SKILLS_DIR_ARG" ]; then
            printf "请输入目标 Skills 目录路径："
            read -r SKILLS_DIR_ARG
            SKILLS_DIR_ARG="${SKILLS_DIR_ARG/#\~/$HOME}"
        fi
        if [ -z "$SKILLS_DIR_ARG" ]; then
            echo "错误：未指定 --skills-dir，退出。"
            exit 1
        fi
        SKILLS_BASE="$SKILLS_DIR_ARG"
    else
        SKILLS_BASE="$(resolve_skills_dir "$TOOL")"
    fi

    mkdir -p "$SKILLS_BASE"
    DEST="$SKILLS_BASE/$SKILL_NAME"
fi

# ─── 解析 workspace 路径 ─────────────────────────────────────────────────────

if [ -n "$WORKSPACE_ARG" ]; then
    WORKSPACE_PATH="$WORKSPACE_ARG"
elif [ -n "$AI_WRITE_FLOW_WORKSPACE" ]; then
    WORKSPACE_PATH="$AI_WRITE_FLOW_WORKSPACE"
    echo "检测到环境变量 AI_WRITE_FLOW_WORKSPACE，workspace：$WORKSPACE_PATH"
else
    printf "请输入 workspace 路径（存放 briefs/research/output 的目录）：\n> "
    read -r WORKSPACE_PATH
    WORKSPACE_PATH="${WORKSPACE_PATH/#\~/$HOME}"
    if [ -z "$WORKSPACE_PATH" ]; then
        echo "错误：未提供 workspace 路径。"
        echo "提示：可设置环境变量 AI_WRITE_FLOW_WORKSPACE 后重新运行，或使用 --workspace 参数。"
        exit 1
    fi
fi

echo ""

# ─── 初始化 workspace ────────────────────────────────────────────────────────

echo "正在初始化 workspace..."
mkdir -p "$WORKSPACE_PATH/briefs"
mkdir -p "$WORKSPACE_PATH/research"
mkdir -p "$WORKSPACE_PATH/output"
mkdir -p "$WORKSPACE_PATH/images"

echo "  ✓ briefs/    已就绪（放入写作素材）"
echo "  ✓ research/  已就绪（调研 JSON 输出）"
echo "  ✓ output/    已就绪（成品文章输出）"
echo "  ✓ images/    已就绪（配图输出，可选）"
echo ""

# ─── 安装 Skill ──────────────────────────────────────────────────────────────

if [ -n "$DEST" ]; then
    if [ -d "$DEST" ]; then
        printf "检测到已安装的旧版本 %s，是否覆盖？(y/n) " "$DEST"
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
    echo "Skill installed: $DEST"

    # 写入本次安装的 workspace 路径，供 Step 1 优先读取
    cat > "$DEST/references/workspace-local.md" <<EOF
# workspace-local.md

This file is generated by the install script. Step 1 reads this file first
to resolve the workspace path without prompting the user.

Do not edit this file manually — re-run install.sh to update the path.

## Resolved Workspace

\`\`\`
workspace_path: $WORKSPACE_PATH
\`\`\`
EOF
    echo "  ✓ workspace-local.md 已写入：$DEST/references/workspace-local.md"
fi

# ─── 完成提示 ────────────────────────────────────────────────────────────────

echo ""
echo "========================================="
echo " 安装完成！"
echo "========================================="
echo ""
echo "Workspace initialized: $WORKSPACE_PATH"
echo ""
echo "下一步："
echo ""
if [ -n "$DEST" ]; then
    echo "  1. 按需调整作者画像："
    echo "     $DEST/references/persona.md"
    echo ""
    echo "  2. 将写作素材放入 workspace/briefs/："
    echo "     $WORKSPACE_PATH/briefs/"
    echo ""
    echo "  3. 在 Agent 中说："
    echo "     '帮我写一篇关于 [主题] 的文章'"
    echo "     或 '帮我审校这篇文章，降低 AI 味'"
else
    echo "  已跳过 Skill 安装，仅完成 workspace 初始化。"
    echo "  如需安装，请重新运行并选择安装目标。"
fi
echo ""
