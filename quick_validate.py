#!/usr/bin/env python3
"""quick_validate.py — Skill 安装包结构快速验证

检查 skill/ 目录的最小完整性：
  1. SKILL.md 存在且 frontmatter 包含必填字段（name、description）
  2. frontmatter 不包含非法字段（如 version）
  3. 必要的 references/ 文件均存在
  4. 必要的 scripts/ 文件均存在

用法：python quick_validate.py [skill目录路径]
      默认路径：./skill
"""

import sys
from pathlib import Path
from typing import Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

REQUIRED_FRONTMATTER = {"name", "description"}
FORBIDDEN_FRONTMATTER = {"version"}

REQUIRED_REFERENCES = [
    "research-config.md",
    "style-guide.md",
    "checklist.md",
    "persona.md",
    "workspace-config.md",
    "fact-policy.md",
    "card-post-config.md",
    "illustration-config.md",
]

REQUIRED_SCRIPTS = [
    "check_article.py",
    "validate_research.py",
    "check_card_post.py",
    "check_illustration_plan.py",
]


def parse_frontmatter(text: str) -> Optional[dict]:
    """Extract YAML frontmatter between --- delimiters."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = next((i for i, l in enumerate(lines[1:], 1) if l.strip() == "---"), None)
    if end is None:
        return None
    block = "\n".join(lines[1:end])
    if HAS_YAML:
        try:
            return yaml.safe_load(block) or {}
        except yaml.YAMLError:
            return None
    # Minimal fallback parser for key: value lines (no multiline support)
    result = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            result[k.strip()] = v.strip()
    return result


def validate(skill_dir: Path) -> list[str]:
    errors = []

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append(f"SKILL.md not found in {skill_dir}")
        return errors

    fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    if fm is None:
        errors.append("SKILL.md: missing or malformed frontmatter (expected --- delimiters)")
    else:
        for field in REQUIRED_FRONTMATTER:
            if not fm.get(field):
                errors.append(f"SKILL.md frontmatter: missing required field '{field}'")
        for field in FORBIDDEN_FRONTMATTER:
            if field in fm:
                errors.append(
                    f"SKILL.md frontmatter: forbidden field '{field}' present "
                    f"(version belongs in README badge / Git tag, not SKILL.md)"
                )

    for ref in REQUIRED_REFERENCES:
        path = skill_dir / "references" / ref
        if not path.exists():
            errors.append(f"references/{ref}: not found")

    for script in REQUIRED_SCRIPTS:
        path = skill_dir / "scripts" / script
        if not path.exists():
            errors.append(f"scripts/{script}: not found")

    return errors


def main() -> int:
    skill_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("skill")
    if not skill_dir.is_dir():
        print(f"[ERROR] Directory not found: {skill_dir}", file=sys.stderr)
        return 1

    errors = validate(skill_dir)
    if errors:
        print(f"[FAIL] quick_validate: {len(errors)} error(s) in {skill_dir}")
        for e in errors:
            print(f"  ✗ {e}")
        return 1

    print(f"[PASS] quick_validate: {skill_dir} OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
