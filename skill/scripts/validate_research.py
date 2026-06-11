#!/usr/bin/env python3
"""validate_research.py — 校验 research JSON 是否符合 schema 与质量门禁"""

import json
import sys
from datetime import datetime, timedelta, timezone

REQUIRED_FIELDS = ["topic", "research_date", "claims", "quality_check"]
MAX_AGE_DAYS = 30

# 仅 Tier 1 / 2a 可将 claim 标记为 supported；其余 tier 一律不支撑
SUPPORTING_TIERS = {1, "1", "2a"}


def _check_date(date_str: str, label: str, errors: list) -> None:
    """校验日期字段是否存在、格式合法、未超过时效门禁。"""
    if not date_str:
        return
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        # 若解析结果为 naive datetime（如 YYYY-MM-DD），补充 UTC 时区
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age = datetime.now(tz=timezone.utc) - dt
        if age > timedelta(days=MAX_AGE_DAYS):
            errors.append(f"{label} 来源已超过 {MAX_AGE_DAYS} 天时效门禁（{date_str}），请重新调研")
            print(f"[ERROR] {label} is {age.days} days old, exceeds {MAX_AGE_DAYS}-day limit", file=sys.stderr)
    except ValueError:
        errors.append(f"{label} 日期格式无法解析：{date_str}（期望 ISO 8601）")
        print(f"[ERROR] Cannot parse {label} date: {date_str}", file=sys.stderr)


def validate(path: str) -> bool:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        print(f"错误：找不到文件 {path}")
        return False
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON in {path}: {e}", file=sys.stderr)
        print(f"错误：JSON 格式错误，请检查文件 {path}")
        return False

    errors = []

    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"缺少必填字段：{field}")
            print(f"[ERROR] Missing required field: {field}", file=sys.stderr)

    # 顶层 research_date 时效校验
    _check_date(data.get("research_date", ""), "research_date", errors)

    # 逐条校验 sources[].source_date
    sources = data.get("sources", [])
    if isinstance(sources, list):
        for i, source in enumerate(sources):
            if "source_date" not in source:
                errors.append(f"sources[{i}] 缺少 source_date 字段：{source.get('title', '未命名来源')[:40]}")
                print(f"[ERROR] sources[{i}] missing source_date: {source.get('title', '')}", file=sys.stderr)
            else:
                _check_date(source["source_date"], f"sources[{i}]", errors)

    # 逐条校验 claims[].status、tier 门禁 和 claims[].source_date
    claims = data.get("claims", [])
    if isinstance(claims, list):
        for i, claim in enumerate(claims):
            status = claim.get("status", "")
            claim_text = claim.get("claim_text", "")
            tier = claim.get("tier")
            if status in ("unverified", "contradicted"):
                errors.append(f"claims[{i}] 状态为 '{status}'，未完成核查：{claim_text[:60]}")
                print(f"[ERROR] claims[{i}] has status '{status}': {claim_text[:60]}", file=sys.stderr)
            # Tier 门禁：只有 Tier 1 / 2a 可以标记为 supported
            if status == "supported" and tier not in SUPPORTING_TIERS:
                errors.append(
                    f"claims[{i}] tier '{tier}' 不得标记为 supported（仅允许 Tier 1 / 2a）：{claim_text[:60]}"
                )
                print(
                    f"[ERROR] claims[{i}] tier '{tier}' cannot be 'supported' (only Tier 1/2a allowed): {claim_text[:60]}",
                    file=sys.stderr,
                )
            if "source_date" not in claim:
                errors.append(f"claims[{i}] 缺少 source_date 字段：{claim_text[:40]}")
                print(f"[ERROR] claims[{i}] missing source_date", file=sys.stderr)
            else:
                _check_date(claim["source_date"], f"claims[{i}]", errors)

    qc = data.get("quality_check", {})
    if not qc.get("passed", False):
        reason = qc.get("reason", "未说明原因")
        errors.append(f"quality_check.passed 为 false：{reason}")
        print(f"[ERROR] quality_check.passed is false: {reason}", file=sys.stderr)

    if errors:
        print("\n【调研质量校验失败】")
        for e in errors:
            print(f"  ✗ {e}")
        print(f"\n共发现 {len(errors)} 个问题，请修复后再进入写作阶段。")
        return False

    print(f"【调研质量校验通过】{path}")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python validate_research.py <research_json_path>")
        sys.exit(1)
    ok = validate(sys.argv[1])
    sys.exit(0 if ok else 1)
