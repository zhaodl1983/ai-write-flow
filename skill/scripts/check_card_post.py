#!/usr/bin/env python3
# check_card_post.py — validate card_post output file for image-card generation systems
#
# Usage:
#   python3 check_card_post.py <card.txt>
#   python3 check_card_post.py <card.txt> --research <research.json>
#
# With --research: additionally verifies that excluded_claims keywords are not
# present in publishable content (【发布配文】 + 【图卡内容排版】), and that
# card_safe_claims is non-empty.

import json
import re
import sys
from pathlib import Path
from typing import Optional

RISK_WORDS = [
    "史诗级", "全网最强", "完全免费", "无限",
    "100%",
    "首个",
    "唯一",
]

CARD_WORD_LIMIT = 1000

REQUIRED_SECTIONS = [
    "【事实核查摘要】",
    "【卡片数量决策】",
    "【发布配文】",
    "【图卡内容排版】",
    "【封面图卡】",
]

# Numeric / currency fact patterns
_FACT_PATTERN = re.compile(
    r"v\d+[\d.]+|"          # version numbers: v0.16.0, v2.1
    r"\d+(?:\.\d+)?%|"      # percentages: 40%, 99.9%
    r"\d+(?:\.\d+)?\s*倍|"  # multipliers: 3倍, 180 倍
    r"\$\d+|"               # USD prices: $20
    r"¥\d+"                 # CNY prices: ¥99
)

# English/mixed-case product tokens: model names, package names, camelCase
_ENGLISH_MIXED_PATTERN = re.compile(
    # Hyphenated / dotted identifiers: DeepSeek-V4, hermes-agent, Qwen3.7, v0.16.0
    r"[a-zA-Z][a-zA-Z0-9]*(?:[-_.][a-zA-Z0-9]+)+"
    # lowerCamelCase: macOS, iPhone, macBook
    r"|[a-z]+[A-Z][a-zA-Z0-9]+"
    # UpperCamelCase with internal caps: DeepSeek, ChatGPT (no separator but mixed case)
    r"|[A-Z][a-z]+[A-Z][a-zA-Z0-9]+"
)


def _extract_card_layout(text: str) -> str:
    """Extract 【图卡内容排版】 section — used for word counting only."""
    match = re.search(r"【图卡内容排版】(.*?)$", text, re.DOTALL)
    return match.group(1) if match else ""


def _extract_public_output(text: str) -> str:
    """Extract publishable content: 【发布配文】 + 【图卡内容排版】.
    Excludes process sections (事实核查摘要, 卡片数量决策) which are internal docs."""
    peizhi_match = re.search(
        r"【发布配文】(.*?)(?=【图卡内容排版】|$)", text, re.DOTALL
    )
    peizhi_text = peizhi_match.group(1) if peizhi_match else ""

    layout_match = re.search(r"【图卡内容排版】(.*?)$", text, re.DOTALL)
    layout_text = layout_match.group(1) if layout_match else ""

    return peizhi_text + "\n" + layout_text


def _count_chinese_chars(text: str) -> int:
    return len(re.findall(r"[一-鿿]", text))


def _parse_cards(text: str) -> list:
    cards = []

    cover_match = re.search(r"【封面图卡】(.*?)(?=【Card \d+】|$)", text, re.DOTALL)
    if cover_match:
        cards.append({"label": "封面图卡", "is_cover": True, "content": cover_match.group(1)})

    for m in re.finditer(r"【(Card \d+)】(.*?)(?=【Card \d+】|$)", text, re.DOTALL):
        cards.append({"label": m.group(1), "is_cover": False, "content": m.group(2)})

    for card in cards:
        card["bullet_count"] = len(re.findall(r"🟢", card["content"]))
        title_match = re.search(r"^\s*\|\s*\d+\s+(.+)", card["content"], re.MULTILINE)
        card["has_title"] = bool(title_match)

    return cards


def _parse_card_numbers(text: str) -> list:
    return [int(m) for m in re.findall(r"【Card (\d+)】", text)]


def _extract_key_tokens(claim_text: str) -> list:
    """Extract high-signal tokens from a claim for soft-match checking.
    Covers: numeric facts, Chinese proper nouns, English/mixed identifiers."""
    tokens = []
    tokens.extend(_FACT_PATTERN.findall(claim_text))
    tokens.extend(_ENGLISH_MIXED_PATTERN.findall(claim_text))
    # Chinese phrases >= 4 chars (likely proper nouns)
    tokens.extend(re.findall(r"[一-鿿]{4,}", claim_text))
    return [t.strip() for t in tokens if t.strip()]


def _check_research(public_output: str, research_path: str) -> tuple:
    """Cross-reference publishable content against research JSON.
    Returns (errors, warnings)."""
    errors = []
    warnings = []

    try:
        data = json.loads(Path(research_path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"research JSON 不存在：{research_path}")
        print(f"[ERROR] Research JSON not found: {research_path}", file=sys.stderr)
        return errors, warnings
    except json.JSONDecodeError as e:
        errors.append(f"research JSON 格式错误：{e}")
        print(f"[ERROR] Invalid JSON: {e}", file=sys.stderr)
        return errors, warnings

    # Check: card_safe_claims must be non-empty
    safe_claims = data.get("card_safe_claims", [])
    if not safe_claims:
        errors.append(
            "research JSON 的 card_safe_claims[] 为空 → "
            "图卡不应在无可信事实的情况下生成"
        )
        print("[ERROR] card_safe_claims[] is empty in research JSON", file=sys.stderr)

    # Check: excluded_claims tokens must not appear in publishable content
    excluded = data.get("excluded_claims", [])
    for exc in excluded:
        claim_text = exc.get("claim_text", "")
        tokens = _extract_key_tokens(claim_text)
        for token in tokens:
            if token in public_output:
                errors.append(
                    f"发布内容含已排除事实的关键词「{token}」"
                    f"（excluded_claims → '{claim_text[:50]}'）"
                )
                print(
                    f"[ERROR] Excluded claim token '{token}' found in public output",
                    file=sys.stderr,
                )
                break  # one error per excluded claim

    if excluded:
        print(
            f"[INFO] Checked {len(excluded)} excluded claim(s) against public output "
            f"(【发布配文】 + 【图卡内容排版】)",
            file=sys.stderr,
        )

    return errors, warnings


def check(path: str, research_path: Optional[str] = None) -> bool:
    content = Path(path).read_text(encoding="utf-8")
    errors = []
    warnings = []

    # Rule 1: Required structural sections
    for section in REQUIRED_SECTIONS:
        if section not in content:
            errors.append(f"缺少必要区块：{section}")
            print(f"[ERROR] Missing required section: {section}", file=sys.stderr)

    # Extraction targets
    layout_text = _extract_card_layout(content)   # word count scope
    public_output = _extract_public_output(content)  # fact/risk scanning scope

    # Rule 2: Card layout word count <= 1000 (图卡内容排版 only, not 发布配文)
    char_count = _count_chinese_chars(layout_text)
    if char_count > CARD_WORD_LIMIT:
        errors.append(f"图卡内容排版字数超限：{char_count} 字（限制 {CARD_WORD_LIMIT} 字）")
        print(
            f"[ERROR] Card layout word count {char_count} exceeds limit {CARD_WORD_LIMIT}",
            file=sys.stderr,
        )
    else:
        print(f"[INFO] Card layout word count: {char_count}/{CARD_WORD_LIMIT}", file=sys.stderr)

    # Rule 3: Total card count <= 9
    cards = _parse_cards(content)
    total_cards = len(cards)
    if total_cards == 0:
        errors.append("未找到任何卡片（缺少【封面图卡】或【Card NN】）")
        print("[ERROR] No cards found", file=sys.stderr)
    elif total_cards > 9:
        errors.append(f"卡片总数超限：{total_cards} 张（含封面，最多 9 张）")
        print(f"[ERROR] Total card count {total_cards} exceeds limit 9", file=sys.stderr)
    else:
        print(f"[INFO] Total cards: {total_cards} (cover + content)", file=sys.stderr)

    # Rule 4: Card numbers must be consecutive starting from 01
    card_nums = _parse_card_numbers(content)
    if card_nums:
        expected = list(range(1, len(card_nums) + 1))
        if card_nums != expected:
            errors.append(f"Card 编号不连续：{card_nums}（应为 {expected}）")
            print(f"[ERROR] Card numbers not consecutive: {card_nums}", file=sys.stderr)

    # Rule 5: Each content card must have a title and 3-4 bullet points
    for card in cards:
        if card["is_cover"]:
            continue
        label = card["label"]
        if not card.get("has_title", False):
            errors.append(f"{label}：缺少标题（格式应为 | NN 标题文字）")
            print(f"[ERROR] {label} has no title", file=sys.stderr)
        bullets = card["bullet_count"]
        if bullets < 3 or bullets > 4:
            errors.append(f"{label}：要点数量为 {bullets} 条（规范要求 3-4 条）")
            print(f"[ERROR] {label} has {bullets} bullet(s); expected 3-4", file=sys.stderr)

    # Rule 6: Risk words — scan public output (发布配文 + 图卡内容排版)
    found_risk = [w for w in RISK_WORDS if w in public_output]
    for w in found_risk:
        errors.append(f"发布内容含高风险绝对化词汇：「{w}」→ 请删除或改成弱化表达")
        print(f"[WARN] Risk word found in public output: '{w}'", file=sys.stderr)

    # Rule 7 (optional): Cross-reference against research JSON — scan public output
    if research_path:
        r_errors, r_warnings = _check_research(public_output, research_path)
        errors.extend(r_errors)
        warnings.extend(r_warnings)

    # Summary
    if errors:
        print("\n【图卡质量检查报告】")
        for e in errors:
            print(f"  ✗ {e}")
        if warnings:
            for w in warnings:
                print(f"  ⚠ {w}")
        print(f"\n共发现 {len(errors)} 个问题，请修复后再复制到图卡生成系统。")
        return False

    if warnings:
        print(f"【图卡质量检查通过（含建议）】{path}")
        for w in warnings:
            print(f"  ⚠ {w}")
    else:
        print(f"【图卡质量检查通过】{path}")
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="校验 card_post 输出文件是否符合图卡生成系统规范",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 基础结构校验
  python3 check_card_post.py output/20260611-card-hermes.txt

  # 结构校验 + 事实追溯（推荐）
  python3 check_card_post.py output/20260611-card-hermes.txt \\
      --research research/20260611-hermes-v016.json

  --research 模式额外检查：
    - card_safe_claims[] 不为空（无可信事实时直接失败）
    - excluded_claims[] 的关键词不出现在【发布配文】或【图卡内容排版】
      覆盖：版本号、百分比、倍数、模型名（如 DeepSeek-V4）、包名、camelCase 标识符
    - 后续可扩展：card_safe_claims 精确引用追溯
""",
    )
    parser.add_argument("card_file", help="图卡文案 .txt 文件路径")
    parser.add_argument(
        "--research",
        metavar="JSON",
        help="调研 JSON 文件路径（启用事实追溯检查）",
    )
    args = parser.parse_args()

    ok = check(args.card_file, research_path=args.research)
    sys.exit(0 if ok else 1)
