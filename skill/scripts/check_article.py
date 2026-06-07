#!/usr/bin/env python3
# check_article.py -- check final Markdown article quality
# Banned expressions and thresholds are derived from style-guide.md (single source of truth).

import re
import sys
from pathlib import Path

# style-guide.md § 禁用表达清单 — AI 腔套话 + 书面词汇 + 空洞表达 + 夸张美学 + 模糊归因 + 助手感开场白
BANNED_EXPRESSIONS = [
    # AI 腔套话
    "在当今时代", "综上所述", "总的来说", "归根结底",
    "值得注意的是", "不难发现", "显而易见", "毋庸置疑", "毫无疑问", "可以说",
    "有助于", "使得", "从而实现",
    "首先", "其次", "最后",
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

REVIEW_REPORT_MARKERS = ["【审校报告】", "【第一遍】", "【第二遍】", "【第三遍】"]


def check(path):
    content = Path(path).read_text(encoding="utf-8")
    issues = []

    for expr in BANNED_EXPRESSIONS:
        count = content.count(expr)
        if count > 0:
            issues.append("含禁用表达「" + expr + "」（出现 " + str(count) + " 次）→ 建议替换为更自然的口语表达")
            print("[WARN] Banned expression '" + expr + "' found " + str(count) + " time(s)", file=sys.stderr)

    for marker in REVIEW_REPORT_MARKERS:
        if marker in content:
            issues.append("文件含审校报告标记「" + marker + "」→ 审校报告不得写入最终稿件，请删除")
            print("[ERROR] Review report marker '" + marker + "' found in article file", file=sys.stderr)

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
            print("  x " + issue)
        print("\n共发现 " + str(len(issues)) + " 个问题，请按建议修改后再发布。")
        return False

    print("【文章质量检查通过】" + path)
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python check_article.py <article_md_path>")
        sys.exit(1)
    ok = check(sys.argv[1])
    sys.exit(0 if ok else 1)
