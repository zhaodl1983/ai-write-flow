#!/usr/bin/env python3
# check_illustration_plan.py -- validate illustration plan JSON before SVG generation

import json
import os
import re
import sys
from pathlib import PurePath

VALID_DIAGRAM_TYPES = {
    "flowchart",
    "comparison",
    "layered_architecture",
    "relationship_map",
    "concept_diagram",
    "timeline",
    "bento_summary",
}

VALID_SVG_STYLES = {
    "tech_dark",
    "bento_info",
    "minimal_clean",
    "glass_premium",
    "neubrutalism",
    "clay_soft",
}

CONCLUSION_TITLE = "写在最后"
UNIT_ID_PATTERN = re.compile(r"^section-\d{2}$")
FILENAME_PATTERN = re.compile(r"^\d{2}-.+\.svg$")
HASHTAG_TOKEN_PATTERN = re.compile(r"^#")
HASHTAG_IN_TEXT_PATTERN = re.compile(r"(?:^|\s)(#[\w一-鿿]+)", re.MULTILINE)


def _normpath(p: str) -> str:
    return os.path.normpath(p).replace("\\", "/")


def validate(plan: dict) -> tuple[list[str], list[str]]:
    errors = []
    warnings = []

    if not plan.get("article_path", "").strip():
        errors.append("article_path 未设置 → 必须指定目标文章路径")
        print("[ERROR] article_path is missing or empty", file=sys.stderr)

    output_dir = plan.get("output_dir", "").strip()
    if not output_dir:
        errors.append("output_dir 未设置")
        print("[ERROR] output_dir is missing", file=sys.stderr)

    items = plan.get("items")
    if not isinstance(items, list) or len(items) == 0:
        errors.append("items[] 为空或缺失 → 至少需要一个配图项")
        print("[ERROR] items[] is empty or missing", file=sys.stderr)
        return errors, warnings

    seen_unit_ids = set()

    for i, item in enumerate(items):
        prefix = f"items[{i}]"

        section_title = item.get("section_title", "")
        if CONCLUSION_TITLE in section_title:
            errors.append(f"{prefix} section_title 包含「写在最后」→ 该章节不参与配图")
            print(f"[ERROR] {prefix} section_title contains conclusion section '写在最后'", file=sys.stderr)

        unit_id = item.get("unit_id", "")
        if not unit_id:
            errors.append(f"{prefix} unit_id 未设置")
            print(f"[ERROR] {prefix} unit_id is missing", file=sys.stderr)
        elif not UNIT_ID_PATTERN.match(unit_id):
            errors.append(f"{prefix} unit_id 格式无效：{unit_id!r} → 必须匹配 section-\\d{{2}}（如 section-01）")
            print(f"[ERROR] {prefix} unit_id '{unit_id}' does not match section-\\d{{2}}", file=sys.stderr)
        elif unit_id in seen_unit_ids:
            errors.append(f"{prefix} unit_id 重复：{unit_id!r}")
            print(f"[ERROR] {prefix} duplicate unit_id '{unit_id}'", file=sys.stderr)
        else:
            seen_unit_ids.add(unit_id)

        output_path_str = item.get("output_path", "").strip()
        if not output_path_str:
            errors.append(f"{prefix} output_path 未设置 → 必须指定 SVG 输出路径")
            print(f"[ERROR] {prefix} output_path is missing", file=sys.stderr)
        else:
            has_traversal = ".." in PurePath(output_path_str).parts
            if has_traversal:
                errors.append(f"{prefix} output_path 含非法 '..' 路径段 → 禁止路径穿越：{output_path_str!r}")
                print(f"[ERROR] {prefix} output_path contains '..' traversal: '{output_path_str}'", file=sys.stderr)

            if not output_path_str.endswith(".svg"):
                errors.append(f"{prefix} output_path 必须以 .svg 结尾：{output_path_str!r}")
                print(f"[ERROR] {prefix} output_path must end with .svg: '{output_path_str}'", file=sys.stderr)
            else:
                filename = PurePath(output_path_str).name
                if not FILENAME_PATTERN.match(filename):
                    warnings.append(
                        f"{prefix} output_path 文件名建议格式为 NN-section-slug.svg，实际：{filename!r}"
                    )
                    print(
                        f"[WARN] {prefix} output_path filename '{filename}' does not match NN-section-slug.svg pattern",
                        file=sys.stderr,
                    )

            if not has_traversal and output_dir:
                norm_path = _normpath(output_path_str)
                norm_dir = _normpath(output_dir).rstrip("/") + "/"
                if not norm_path.startswith(norm_dir):
                    errors.append(
                        f"{prefix} output_path 必须位于 output_dir 下："
                        f"{output_path_str!r} 不在 {output_dir!r}"
                    )
                    print(
                        f"[ERROR] {prefix} output_path '{output_path_str}' is not under output_dir '{output_dir}'",
                        file=sys.stderr,
                    )

        diagram_type = item.get("diagram_type", "")
        if diagram_type not in VALID_DIAGRAM_TYPES:
            errors.append(
                f"{prefix} diagram_type 无效：{diagram_type!r} → 允许值：{sorted(VALID_DIAGRAM_TYPES)}"
            )
            print(f"[ERROR] {prefix} invalid diagram_type '{diagram_type}'", file=sys.stderr)

        svg_style = item.get("svg_style", "")
        if svg_style not in VALID_SVG_STYLES:
            errors.append(
                f"{prefix} svg_style 无效：{svg_style!r} → 允许值：{sorted(VALID_SVG_STYLES)}"
            )
            print(f"[ERROR] {prefix} invalid svg_style '{svg_style}'", file=sys.stderr)

        platform = item.get("platform", "")
        if platform != "wechat_article":
            errors.append(f"{prefix} platform 必须为 'wechat_article'，实际：{platform!r}")
            print(f"[ERROR] {prefix} platform must be 'wechat_article', got '{platform}'", file=sys.stderr)

        labels = item.get("labels", [])
        if not isinstance(labels, list) or not (1 <= len(labels) <= 6):
            errors.append(
                f"{prefix} labels 数量应为 1-6 个，"
                f"实际：{len(labels) if isinstance(labels, list) else '非列表'}"
            )
            print(f"[ERROR] {prefix} labels must be a list of 1-6 items", file=sys.stderr)
        elif isinstance(labels, list):
            for label in labels:
                if isinstance(label, str) and HASHTAG_TOKEN_PATTERN.match(label.strip()):
                    errors.append(
                        f"{prefix} labels 包含 hashtag token {label!r} → hashtag 是发布元信息，不得作为画面标签"
                    )
                    print(f"[ERROR] {prefix} labels contain hashtag token '{label.strip()}' — publishing metadata must be excluded", file=sys.stderr)

        keywords = item.get("keywords", [])
        if isinstance(keywords, list):
            for kw in keywords:
                if isinstance(kw, str) and HASHTAG_TOKEN_PATTERN.match(kw.strip()):
                    errors.append(
                        f"{prefix} keywords 包含 hashtag token {kw!r} → hashtag 是发布元信息，不得作为关键词"
                    )
                    print(f"[ERROR] {prefix} keywords contain hashtag token '{kw.strip()}' — publishing metadata must be excluded", file=sys.stderr)

        visual_brief = item.get("visual_brief", "").strip()
        if not visual_brief:
            errors.append(f"{prefix} visual_brief 不得为空")
            print(f"[ERROR] {prefix} visual_brief is empty", file=sys.stderr)
        else:
            hashtag_hits = HASHTAG_IN_TEXT_PATTERN.findall(visual_brief)
            if len(hashtag_hits) >= 2:
                warnings.append(
                    f"{prefix} visual_brief 疑似包含发布 hashtag（{', '.join(hashtag_hits[:3])}）→ 请确认这些 tag 是画面语义而非发布元信息"
                )
                print(
                    f"[WARN] {prefix} visual_brief may contain publishing hashtags: {hashtag_hits[:3]}",
                    file=sys.stderr,
                )

        if not item.get("core_claim", "").strip():
            warnings.append(f"{prefix} core_claim 为空，建议补充一句话核心论断")
            print(f"[WARN] {prefix} core_claim is empty", file=sys.stderr)

    return errors, warnings


def main() -> int:
    if len(sys.argv) < 2:
        print("用法：python check_illustration_plan.py <plan_json_path>")
        return 1

    path_arg = sys.argv[1]
    if not os.path.exists(path_arg):
        print(f"[ERROR] 文件不存在：{path_arg}", file=sys.stderr)
        return 1

    try:
        plan = json.loads(open(path_arg, encoding="utf-8").read())
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON 解析失败：{e}", file=sys.stderr)
        return 1

    errors, warnings = validate(plan)

    if errors:
        print("\n【配图计划校验失败】")
        for e in errors:
            print(f"  ✗ {e}")
        if warnings:
            for w in warnings:
                print(f"  ⚠ {w}")
        print(f"\n共发现 {len(errors)} 个错误，请修复后重新生成配图计划。")
        return 1

    if warnings:
        print(f"【配图计划校验通过（含建议）】{path_arg}")
        for w in warnings:
            print(f"  ⚠ {w}")
    else:
        print(f"【配图计划校验通过】{path_arg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
