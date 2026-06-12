#!/usr/bin/env python3
"""run_evals.py — 将 evals.json 从说明文件变为可执行质量门禁

支持两类场景：
  workflow  — 写作流场景，input 含 user_message + briefs_files
  script    — 脚本校验场景，input 含 article_file + check_command

检查内容：
1. evals.json 结构完整性（必填字段、scenario 格式）
2. 文件引用实际存在（briefs_files / article_file）
3. expected_behavior / expected_not 均为非空列表
4. 每个 scenario 的触发路径可识别
5. script 场景：实际执行 check_command 并校验期望退出码

用法：python evals/run_evals.py [evals.json 路径]
"""

import json
import subprocess
import sys
from pathlib import Path

EVALS_PATH = Path(__file__).parent / "evals.json"

REQUIRED_TOP_FIELDS = ["version", "skill", "scenarios"]
REQUIRED_SCENARIO_FIELDS = ["id", "name", "description", "input", "expected_behavior", "expected_not"]

# workflow 类场景必须有的 input 字段
REQUIRED_WORKFLOW_INPUT = ["user_message", "briefs_files"]
# script 类场景必须有的 input 字段
REQUIRED_SCRIPT_INPUT = ["article_file", "check_command"]

# 用于识别触发路径的关键词（workflow 类）
WORKFLOW_TRIGGER_KEYWORDS = [
    "Step 1", "Step 2", "Step 3", "Step 4", "Step 5", "Step 6",
    "审校", "降AI味", "降ai味", "briefs", "阻断",
    "card_post", "图卡", "卡片", "贴图",
    "事实核查", "核查", "excluded_claims", "card_safe_claims",
    "配图", "illustration", "svg-architect", "diagram_type", "flowchart",
]

# 用于识别触发路径的关键词（script 类）
SCRIPT_TRIGGER_KEYWORDS = [
    "check_article", "check_card_post", "exit", "ERROR", "通过", "失败", "校验",
]


def _detect_scenario_type(scenario: dict) -> str:
    """
    Detect scenario type based on input fields.
    Returns 'workflow', 'script', or 'unknown'.
    """
    inp = scenario.get("input", {})
    if "user_message" in inp or "briefs_files" in inp:
        return "workflow"
    if "article_file" in inp or "check_command" in inp:
        return "script"
    return "unknown"


def _check_trigger_path(scenario: dict, sc_type: str) -> list[str]:
    """检查 expected_behavior 是否包含可识别的触发路径关键词。"""
    behaviors = scenario.get("expected_behavior", [])
    text = " ".join(behaviors)
    keywords = WORKFLOW_TRIGGER_KEYWORDS if sc_type == "workflow" else SCRIPT_TRIGGER_KEYWORDS
    if not any(kw.lower() in text.lower() for kw in keywords):
        return [f"scenario '{scenario.get('id')}' 的 expected_behavior 不包含任何已知触发路径关键词"]
    return []


def _check_file_refs(scenario: dict, base_dir: Path, sc_type: str) -> list[str]:
    """校验场景引用的文件实际存在。"""
    errors = []
    inp = scenario.get("input", {})

    if sc_type == "workflow":
        for ref in inp.get("briefs_files", []):
            target = base_dir / ref
            if not target.exists():
                errors.append(f"scenario '{scenario.get('id')}' 引用文件不存在：{ref}")
                print(f"[ERROR] Referenced file not found: {target}", file=sys.stderr)

    if sc_type == "script":
        article = inp.get("article_file", "")
        if article:
            target = base_dir / article
            if not target.exists():
                errors.append(f"scenario '{scenario.get('id')}' article_file 不存在：{article}")
                print(f"[ERROR] article_file not found: {target}", file=sys.stderr)

    return errors


def _check_input_fields(scenario: dict, sc_type: str) -> list[str]:
    """校验 input 字段完整性（按场景类型分别验证）。"""
    errors = []
    inp = scenario.get("input", {})
    sc_id = scenario.get("id", "?")

    if sc_type == "workflow":
        for field in REQUIRED_WORKFLOW_INPUT:
            if field not in inp:
                errors.append(f"scenario '{sc_id}'.input 缺少字段：{field}")
                print(f"[ERROR] scenario '{sc_id}'.input missing field: {field}", file=sys.stderr)

    elif sc_type == "script":
        for field in REQUIRED_SCRIPT_INPUT:
            if field not in inp:
                errors.append(f"scenario '{sc_id}'.input 缺少字段：{field}")
                print(f"[ERROR] scenario '{sc_id}'.input missing field: {field}", file=sys.stderr)

    else:
        errors.append(
            f"scenario '{sc_id}' input 类型无法识别，需要包含 user_message/briefs_files（写作流）"
            " 或 article_file/check_command（脚本校验）"
        )
        print(f"[ERROR] scenario '{sc_id}' has unrecognized input type", file=sys.stderr)

    return errors


def _get_expected_exit_code(scenario: dict):
    """从 expected_behavior 中推断期望退出码，找不到返回 None。"""
    for line in scenario.get("expected_behavior", []):
        if "退出码为 0" in line:
            return 0
        if "退出码为 1" in line:
            return 1
    return None


def _run_script_command(scenario: dict, base_dir: Path) -> list[str]:
    """执行 script 场景的 check_command 并校验退出码，返回错误列表。"""
    sc_id = scenario.get("id", "?")
    cmd = scenario.get("input", {}).get("check_command", "")
    if not cmd:
        return []
    expected_code = _get_expected_exit_code(scenario)
    if expected_code is None:
        return []
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=str(base_dir),
            capture_output=True, text=True, timeout=30,
        )
        actual_code = result.returncode
        if actual_code != expected_code:
            print(
                f"[ERROR] scenario '{sc_id}' exit code mismatch: expected {expected_code}, got {actual_code}",
                file=sys.stderr,
            )
            print(f"  stdout: {result.stdout[:200].strip()}", file=sys.stderr)
            print(f"  stderr: {result.stderr[:200].strip()}", file=sys.stderr)
            return [
                f"scenario '{sc_id}' 命令退出码不符：期望 {expected_code}，实际 {actual_code}（cmd: {cmd[:80]}）"
            ]
    except subprocess.TimeoutExpired:
        print(f"[ERROR] scenario '{sc_id}' command timed out: {cmd[:80]}", file=sys.stderr)
        return [f"scenario '{sc_id}' 命令超时（30s）：{cmd[:80]}"]
    return []


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

    workflow_count = 0
    script_count = 0

    for i, sc in enumerate(scenarios):
        sc_id = sc.get("id", f"[{i}]")

        for field in REQUIRED_SCENARIO_FIELDS:
            if field not in sc:
                errors.append(f"scenario '{sc_id}' 缺少必填字段：{field}")
                print(f"[ERROR] scenario '{sc_id}' missing field: {field}", file=sys.stderr)

        sc_type = _detect_scenario_type(sc)
        if sc_type == "workflow":
            workflow_count += 1
        elif sc_type == "script":
            script_count += 1

        errors.extend(_check_input_fields(sc, sc_type))

        if not sc.get("expected_behavior"):
            errors.append(f"scenario '{sc_id}' 的 expected_behavior 为空列表")
            print(f"[ERROR] scenario '{sc_id}' has empty expected_behavior", file=sys.stderr)

        if not sc.get("expected_not"):
            errors.append(f"scenario '{sc_id}' 的 expected_not 为空列表")
            print(f"[ERROR] scenario '{sc_id}' has empty expected_not", file=sys.stderr)

        errors.extend(_check_trigger_path(sc, sc_type))
        errors.extend(_check_file_refs(sc, base_dir, sc_type))
        if sc_type == "script":
            errors.extend(_run_script_command(sc, base_dir))

    if errors:
        print("\n【Eval 质量门禁检查失败】")
        for e in errors:
            print(f"  ✗ {e}")
        print(f"\n共发现 {len(errors)} 个问题，请修复 evals.json 或补充缺失文件。")
        return False

    print(f"【Eval 质量门禁检查通过】{evals_path}")
    print(f"  已验证 {len(scenarios)} 个场景（workflow: {workflow_count}，script: {script_count}）")
    return True


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else EVALS_PATH
    ok = run(path)
    sys.exit(0 if ok else 1)
