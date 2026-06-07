#!/usr/bin/env python3
"""run_evals.py — 将 evals.json 从说明文件变为可执行质量门禁

检查内容：
1. evals.json 结构完整性（必填字段、scenario 格式）
2. briefs_files 引用的文件实际存在
3. expected_behavior / expected_not 均为非空列表
4. 每个 scenario 的触发路径可识别（包含已知关键词）

用法：python evals/run_evals.py [evals.json 路径]
"""

import json
import sys
from pathlib import Path

EVALS_PATH = Path(__file__).parent / "evals.json"

REQUIRED_TOP_FIELDS = ["version", "skill", "scenarios"]
REQUIRED_SCENARIO_FIELDS = ["id", "name", "description", "input", "expected_behavior", "expected_not"]
REQUIRED_INPUT_FIELDS = ["user_message", "briefs_files"]

# 用于识别触发路径的关键词
TRIGGER_KEYWORDS = [
    "Step 1", "Step 2", "Step 3", "Step 4", "Step 5", "Step 6",
    "审校", "降AI味", "降ai味", "briefs", "阻断",
]


def _check_trigger_path(scenario: dict) -> list[str]:
    """检查 expected_behavior 是否包含可识别的触发路径关键词。"""
    behaviors = scenario.get("expected_behavior", [])
    text = " ".join(behaviors)
    if not any(kw.lower() in text.lower() for kw in TRIGGER_KEYWORDS):
        return [f"scenario '{scenario.get('id')}' 的 expected_behavior 不包含任何已知触发路径关键词，无法自动识别流程"]
    return []


def _check_file_refs(scenario: dict, base_dir: Path) -> list[str]:
    """校验 briefs_files 中引用的文件实际存在。"""
    errors = []
    for ref in scenario.get("input", {}).get("briefs_files", []):
        target = base_dir / ref
        if not target.exists():
            errors.append(f"scenario '{scenario.get('id')}' 引用文件不存在：{ref}")
            print(f"[ERROR] Referenced file not found: {target}", file=sys.stderr)
    return errors


def run(evals_path: Path) -> bool:
    try:
        with open(evals_path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] evals.json not found: {evals_path}", file=sys.stderr)
        print(f"错误：找不到 evals.json：{evals_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON: {e}", file=sys.stderr)
        print(f"错误：JSON 格式错误：{e}")
        return False

    errors = []
    base_dir = evals_path.parent.parent  # 项目根目录

    for field in REQUIRED_TOP_FIELDS:
        if field not in data:
            errors.append(f"缺少顶层必填字段：{field}")
            print(f"[ERROR] Missing top-level field: {field}", file=sys.stderr)

    scenarios = data.get("scenarios", [])
    if not isinstance(scenarios, list) or len(scenarios) == 0:
        errors.append("scenarios 列表为空，请至少添加一个场景")
        print("[ERROR] scenarios list is empty", file=sys.stderr)

    for i, sc in enumerate(scenarios):
        sc_id = sc.get("id", f"[{i}]")

        for field in REQUIRED_SCENARIO_FIELDS:
            if field not in sc:
                errors.append(f"scenario '{sc_id}' 缺少必填字段：{field}")
                print(f"[ERROR] scenario '{sc_id}' missing field: {field}", file=sys.stderr)

        for field in REQUIRED_INPUT_FIELDS:
            if field not in sc.get("input", {}):
                errors.append(f"scenario '{sc_id}'.input 缺少字段：{field}")
                print(f"[ERROR] scenario '{sc_id}'.input missing field: {field}", file=sys.stderr)

        if not sc.get("expected_behavior"):
            errors.append(f"scenario '{sc_id}' 的 expected_behavior 为空列表")
            print(f"[ERROR] scenario '{sc_id}' has empty expected_behavior", file=sys.stderr)

        if not sc.get("expected_not"):
            errors.append(f"scenario '{sc_id}' 的 expected_not 为空列表")
            print(f"[ERROR] scenario '{sc_id}' has empty expected_not", file=sys.stderr)

        errors.extend(_check_trigger_path(sc))
        errors.extend(_check_file_refs(sc, base_dir))

    if errors:
        print("\n【Eval 质量门禁检查失败】")
        for e in errors:
            print(f"  ✗ {e}")
        print(f"\n共发现 {len(errors)} 个问题，请修复 evals.json 或补充缺失文件。")
        return False

    print(f"【Eval 质量门禁检查通过】{evals_path}")
    print(f"  已验证 {len(scenarios)} 个场景")
    return True


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else EVALS_PATH
    ok = run(path)
    sys.exit(0 if ok else 1)
