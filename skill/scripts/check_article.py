#!/usr/bin/env python3
# check_article.py -- check final Markdown article quality
# Style rules derived from style-guide.md; structure rules from ai-write-flow article spec.

import re
import sys
from pathlib import Path

# Circled number sequence for #### subheadings
NUMBERED_CIRCLES = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨']

CONCLUSION_TITLE = "写在最后"

# style-guide.md § 禁用表达清单 — AI 腔套话 + 书面词汇 + 空洞表达 + 夸张美学 + 模糊归因 + 助手感开场白
BANNED_EXPRESSIONS = [
    # AI 腔套话
    "在当今时代", "综上所述", "总的来说", "归根结底",
    "值得注意的是", "不难发现", "显而易见", "毋庸置疑", "毫无疑问", "可以说",
    "有助于", "使得", "从而实现",
    "首先…其次", "其次…最后",
    # 书面词汇
    "显著提升", "充分利用", "进行操作", "获取结果", "实现功能", "相关方案",
    # 空洞表达
    "具有显著优势", "效果非常好", "值得推荐使用",
    # 夸张美学
    "充满活力", "蓬勃发展", "里程碑", "革命性", "重塑",
    # 模糊归因
    "专家认为", "研究表明", "据统计", "众所周知",
    # 助手感开场白
    "当然可以", "很高兴为您", "没问题", "作为一名AI",
    # 原有条目保留
    "不得不说", "总结一下", "本文将", "笔者认为", "由此可见", "因此，我们",
]

# style-guide.md § 句子长度：参考范围 15-25 字；单句超过 35 字优先断开（warning）；120 字视为严重过长（error）
SENTENCE_WARN = 35
SENTENCE_ERROR = 120

REVIEW_REPORT_MARKERS = ["【审校报告】", "【第一遍】", "【第二遍】", "【第三遍】", "【第四遍】"]

CHATBOT_ARTIFACTS = [
    "希望这对你有帮助", "如果你需要我可以继续", "以下是", "当然可以",
]

GENERIC_FUTURE_CLOSERS = [
    "未来可期", "让我们拭目以待", "拭目以待", "只有时间会给出答案", "未来值得期待",
]

PROMO_INFLATION = [
    "史诗级", "全网最强", "革命性", "颠覆式", "重新定义", "极致体验", "不容错过",
]

FALSE_DEPTH_PATTERNS = [
    re.compile(r'不是[^。！？\n]{1,40}而是[^。！？\n]{1,60}'),
    re.compile(r'与其说[^。！？\n]{1,40}不如说[^。！？\n]{1,60}'),
    re.compile(r'重要的不是[^。！？\n]{1,40}而是[^。！？\n]{1,60}'),
]

SHORT_SENTENCE_BURST = re.compile(r'(?:[^。！？\n]{2,8}[。！？]){4,}')


def _strip_fenced_code(text):
    """Remove fenced code block content to avoid false positives in heading checks."""
    return re.sub(r'```[\s\S]*?```', '', text)


def _parse_structure(content):
    """
    Parse article heading structure, skipping fenced code blocks.
    Returns:
      h1_count: int
      has_h3: bool
      opening_has_h4: bool  (#### appears before first ##)
      sections: list of {'title': str, 'h4s': list[str], 'h4_blocks': list[dict], 'is_conclusion': bool}
    """
    clean = _strip_fenced_code(content)
    lines = clean.split('\n')

    h1_count = 0
    has_h3 = False
    opening_has_h4 = False
    first_h2_seen = False
    sections = []
    current_section = None

    for line in lines:
        s = line.rstrip()
        if re.match(r'^# (?!#)', s):
            h1_count += 1
        elif re.match(r'^## (?!#)', s):
            first_h2_seen = True
            title = s[3:].strip()
            is_conclusion = (title == CONCLUSION_TITLE)
            current_section = {'title': title, 'h4s': [], 'h4_blocks': [], 'is_conclusion': is_conclusion}
            sections.append(current_section)
        elif re.match(r'^### (?!#)', s):
            has_h3 = True
        elif re.match(r'^#### (?!#)', s):
            if not first_h2_seen:
                opening_has_h4 = True
            elif current_section is not None:
                h4_text = s[5:].strip()
                current_section['h4s'].append(h4_text)
                current_section['h4_blocks'].append({'title': h4_text, 'has_body': False})
        elif current_section is not None and current_section.get('h4_blocks') and s.strip():
            # Any non-heading content after the latest #### belongs to that subheading block.
            if not re.match(r'^#{1,6} ', s):
                current_section['h4_blocks'][-1]['has_body'] = True

    return h1_count, has_h3, opening_has_h4, sections


def _check_numbering(h4s, section_title):
    """Verify h4 subheadings start with ①②③ consecutively. Returns list of error strings."""
    errs = []
    for i, h4 in enumerate(h4s):
        if i >= len(NUMBERED_CIRCLES):
            errs.append(f"章节「{section_title}」第 {i + 1} 个 #### 超出编号范围（最多 9 个）")
            break
        expected = NUMBERED_CIRCLES[i]
        if not h4.startswith(expected):
            errs.append(
                f"章节「{section_title}」第 {i + 1} 个 #### 编号应为 {expected}，实际开头：「{h4[:20]}」"
            )
    return errs


def _check_structure(content):
    """
    Check Markdown structure against article spec.
    Returns (errors: list[str], warnings: list[str]).
    Errors block publishing; warnings are advisory only.
    """
    errors = []
    warnings = []
    h1_count, has_h3, opening_has_h4, sections = _parse_structure(content)

    if h1_count == 0:
        errors.append("缺少文章标题（#）→ 全文必须有且仅有一个 # 标题")
        print("[ERROR] No H1 title (#) found", file=sys.stderr)
    elif h1_count > 1:
        errors.append(f"# 标题出现了 {h1_count} 次 → 只能出现一次")
        print(f"[ERROR] H1 (#) appears {h1_count} times, must be exactly 1", file=sys.stderr)

    if has_h3:
        errors.append("文中存在 ### 标题 → 禁止使用 ### 层级，请改用 ## 或 ####")
        print("[ERROR] H3 (###) headings found; ### is forbidden", file=sys.stderr)

    if opening_has_h4:
        errors.append("开头段落（# 后、第一个 ## 前）不允许出现 ####")
        print("[ERROR] #### found in opening section before first ##", file=sys.stderr)

    regular = [s for s in sections if not s['is_conclusion']]
    conclusions = [s for s in sections if s['is_conclusion']]

    if not conclusions:
        errors.append("缺少固定结尾章节「## 写在最后」")
        print("[ERROR] Missing required conclusion section '## 写在最后'", file=sys.stderr)
    else:
        if len(conclusions) > 1:
            errors.append(f"「## 写在最后」出现了 {len(conclusions)} 次 → 只允许出现一次")
            print(f"[ERROR] '## 写在最后' appears {len(conclusions)} times, must be exactly 1", file=sys.stderr)

        if sections and not sections[-1]['is_conclusion']:
            errors.append("「## 写在最后」后面还有其他章节 → 必须是文章最后一个 ## 章节")
            print("[ERROR] '## 写在最后' is not the last ## section", file=sys.stderr)

        for conclusion in conclusions:
            if conclusion['h4s']:
                errors.append("「## 写在最后」下包含 #### 小标题 → 结尾章节不得包含 ####")
                print("[ERROR] '## 写在最后' contains #### subheadings; none allowed", file=sys.stderr)

    for sec in regular:
        h4s = sec['h4s']
        title = sec['title']
        if not h4s:
            errors.append(f"章节「## {title}」缺少 #### ① 小标题 → 普通章节必须包含 #### 编号小标题组")
            print(f"[ERROR] Section '## {title}' has no #### subheadings", file=sys.stderr)
        else:
            for err in _check_numbering(h4s, title):
                errors.append(err)
                print(f"[ERROR] Numbering error in section '## {title}'", file=sys.stderr)
            for block in sec.get('h4_blocks', []):
                if not block.get('has_body'):
                    errors.append(
                        f"章节「## {title}」的「#### {block['title']}」后缺少正文段落 → 标准结构要求每个 #### 后接对应正文"
                    )
                    print(f"[ERROR] H4 block in section '## {title}' has no body: {block['title']}", file=sys.stderr)
            count = len(h4s)
            if count < 2 or count > 3:
                warnings.append(f"章节「## {title}」有 {count} 个 #### 小标题，建议 2-3 个")
                print(f"[WARN] Section '## {title}' has {count} #### heading(s); recommend 2-3", file=sys.stderr)

    return errors, warnings


def check(path):
    content = Path(path).read_text(encoding="utf-8")
    issues = []
    advisory = []

    # --- structure checks (style-guide.md § Markdown 标题层级规范) ---
    struct_errors, struct_warnings = _check_structure(content)
    issues.extend(struct_errors)
    advisory.extend(struct_warnings)

    # --- style checks (style-guide.md § 禁用表达清单) ---
    for expr in BANNED_EXPRESSIONS:
        count = content.count(expr)
        if count > 0:
            issues.append("含禁用表达「" + expr + "」（出现 " + str(count) + " 次）→ 建议替换为更自然的口语表达")
            print("[WARN] Banned expression '" + expr + "' found " + str(count) + " time(s)", file=sys.stderr)

    for marker in REVIEW_REPORT_MARKERS:
        if marker in content:
            issues.append("文件含审校报告标记「" + marker + "」→ 审校报告不得写入最终稿件，请删除")
            print("[ERROR] Review report marker '" + marker + "' found in article file", file=sys.stderr)

    double_dash_count = content.count("——")
    single_dash_count = content.replace("——", "").count("—")
    dash_count = double_dash_count + single_dash_count
    if dash_count > 1:
        issues.append(f"破折号 / em dash 出现 {dash_count} 次 → 每篇最多 1 处，优先改成句号、逗号或冒号")
        print(f"[WARN] Dash/em dash appears {dash_count} time(s)", file=sys.stderr)

    for expr in CHATBOT_ARTIFACTS:
        count = content.count(expr)
        if count > 0:
            issues.append(f"含聊天残留「{expr}」（出现 {count} 次）→ 删除，不得进入最终稿")
            print(f"[ERROR] Chatbot artifact '{expr}' found {count} time(s)", file=sys.stderr)

    for expr in GENERIC_FUTURE_CLOSERS:
        count = content.count(expr)
        if count > 0:
            issues.append(f"含万能展望结尾「{expr}」（出现 {count} 次）→ 改成具体事实或下一步行动")
            print(f"[WARN] Generic future closer '{expr}' found {count} time(s)", file=sys.stderr)

    for expr in PROMO_INFLATION:
        count = content.count(expr)
        if count > 0:
            issues.append(f"含宣传/夸张表达「{expr}」（出现 {count} 次）→ 改成可验证事实")
            print(f"[WARN] Promotional inflation '{expr}' found {count} time(s)", file=sys.stderr)

    for pattern in FALSE_DEPTH_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            issues.append(f"发现 {len(matches)} 处“不是 X 而是 Y / 与其说 X 不如说 Y”结构 → 只保留真正服务论证的一处，其余改成直接判断")
            for m in matches[:3]:
                issues.append("  …" + m[:60] + "…")
            print(f"[WARN] False-depth construction found {len(matches)} time(s)", file=sys.stderr)

    bursts = SHORT_SENTENCE_BURST.findall(content)
    if bursts:
        issues.append(f"发现 {len(bursts)} 处连续短句轰炸 → 合并成自然句，保留必要节奏点")
        print(f"[WARN] Short-sentence burst found {len(bursts)} time(s)", file=sys.stderr)

    reading_pattern = re.compile("(扩展阅读|延伸阅读|参考资料|相关链接)", re.IGNORECASE)
    if not reading_pattern.search(content):
        issues.append("缺少扩展阅读 / 参考资料章节 → 建议在文末添加 2-4 条延伸阅读链接")
        print("[WARN] No extended reading / references section found", file=sys.stderr)

    sentences = re.split("[。！？\n]", content)
    warn_sentences = [s.strip() for s in sentences if SENTENCE_WARN < len(s.strip()) <= SENTENCE_ERROR]
    error_sentences = [s.strip() for s in sentences if len(s.strip()) > SENTENCE_ERROR]

    if warn_sentences:
        issues.append("发现 " + str(len(warn_sentences)) + " 个偏长句（>" + str(SENTENCE_WARN) + " 字）→ 建议在逗号处断开")
        for s in warn_sentences[:3]:
            issues.append("  …" + s[:60] + "…")
        print("[WARN] " + str(len(warn_sentences)) + " sentence(s) exceed " + str(SENTENCE_WARN) + " chars", file=sys.stderr)

    if error_sentences:
        issues.append("发现 " + str(len(error_sentences)) + " 个严重超长句（>" + str(SENTENCE_ERROR) + " 字）→ 必须拆分")
        for s in error_sentences[:3]:
            issues.append("  …" + s[:60] + "…")
        print("[ERROR] " + str(len(error_sentences)) + " sentence(s) exceed " + str(SENTENCE_ERROR) + " chars", file=sys.stderr)

    if issues:
        print("\n【文章质量检查报告】")
        for issue in issues:
            print("  ✗ " + issue)
        if advisory:
            for w in advisory:
                print("  ⚠ " + w)
        print("\n共发现 " + str(len(issues)) + " 个问题，请按建议修改后再发布。")
        return False

    if advisory:
        print("【文章质量检查通过（含建议）】" + path)
        for w in advisory:
            print("  ⚠ " + w)
    else:
        print("【文章质量检查通过】" + path)
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python check_article.py <article_md_path>")
        sys.exit(1)
    ok = check(sys.argv[1])
    sys.exit(0 if ok else 1)
