#!/usr/bin/env python3
"""Non-destructive Korean humanization audit. No external dependencies.

Checks literal preservation and reports weak style signals. This is not a
semantic equivalence checker or an AI-detector score.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

FENCE = re.compile(r"(?ms)^([ \t]*)(`{3,}|~{3,})[^\n]*\n.*?^\1\2[ \t]*$")
INLINE_CODE = re.compile(r"(?<!`)`[^`\n]+`(?!`)")
URL = re.compile(r"https?://[^\s)>\]]+")
TEMPLATE = re.compile(r"\{\{[^{}\n]+\}\}|\$\{[^}\n]+\}")
NUMBER = re.compile(
    r"(?<![A-Za-z0-9_])[-+]?\d+(?:,\d{3})*(?:\.\d+)?"
    r"(?:%|％|개월|시간|만원|억원|GB|MB|TB|KB|km|kg|ms|Hz|년|월|일|시|분|초|개|명|회|건|원|배|억|만|m)?"
    r"(?![A-Za-z0-9_])"
)
ACRONYM = re.compile(r"(?<![A-Za-z0-9])[A-Z][A-Z0-9_-]{1,}(?![A-Za-z0-9])")

# Style matches are only a review cue, never proof of AI authorship.
SIGNALS = {
    "staged-introduction": r"(?:먼저|우선)\s+.*?(?:살펴보겠습니다|알아보겠습니다)",
    "empty-conclusion": r"(?:결론적으로|요약하자면)[,，]?\s*(?:이는|이것은)?.{0,20}(?:시사하는 바가 크다|중요한 의미를 가진다)",
    "translationese": r"(?:에 있어서|에 대한 논의를 진행|할 수 있는 가능성이 있다)",
    "inflated-language": r"(?:새로운 패러다임|시너지를 창출|획기적인|효율성을 극대화)",
    "staged-contrast": r"단순히.{1,70}(?:가|이)?\s*아니라",
    "generic-importance": r"(?:매우 중요한 역할을 수행|중요한 역할을 수행)",
    "verbose-causative": r"(?:자동적으로|포괄적으로|종합적으로)\s*(?:검토|확인|생성|수행)",
}


def protected(text: str) -> dict[str, list[str]]:
    """Extract literal regions which should not change when editing prose."""
    blocks = [m.group(0) for m in FENCE.finditer(text)]
    stripped = FENCE.sub(lambda m: " " * len(m.group(0)), text)
    vals = {
        "fenced_code": blocks,
        "inline_code": [m.group(0) for m in INLINE_CODE.finditer(stripped)],
        "urls": [m.group(0) for m in URL.finditer(stripped)],
        "templates": [m.group(0) for m in TEMPLATE.finditer(stripped)],
    }
    return vals


def mask_nonprose(text: str) -> str:
    for regex in (FENCE, INLINE_CODE, URL, TEMPLATE):
        text = regex.sub(lambda m: " " * len(m.group(0)), text)
    return text


def signals(text: str) -> dict[str, int]:
    prose = mask_nonprose(text)
    return {key: len(re.findall(pattern, prose)) for key, pattern in SIGNALS.items()}


def _counter_diff(a: list[str], b: list[str]) -> tuple[list[str], list[str]]:
    left, right = Counter(a), Counter(b)
    return list((left - right).elements()), list((right - left).elements())


def audit(original: str, revised: str | None = None) -> dict:
    report: dict = {"passed_literal_checks": True, "violations": [], "style_signals_before": signals(original)}
    if revised is None:
        return report
    report["style_signals_after"] = signals(revised)
    a, b = protected(original), protected(revised)
    for category in a:
        missing, added = _counter_diff(a[category], b[category])
        if missing or added:
            report["violations"].append({"type": category, "removed": missing, "added": added})
    # Numeric text outside already-protected regions must remain unchanged.
    na = NUMBER.findall(mask_nonprose(original))
    nb = NUMBER.findall(mask_nonprose(revised))
    missing, added = _counter_diff(na, nb)
    if missing or added:
        report["violations"].append({"type": "numbers", "removed": missing, "added": added})
    # Technical acronyms are warnings, since ordinary words can be removed.
    ta = ACRONYM.findall(mask_nonprose(original))
    tb = ACRONYM.findall(mask_nonprose(revised))
    missing, added = _counter_diff(ta, tb)
    if missing or added:
        report["review_acronyms"] = {"removed": missing, "added": added}
    report["passed_literal_checks"] = not report["violations"]
    report["limitations"] = "숫자·코드·URL·템플릿만 기계적으로 비교합니다. 의미·고유명사·논리 보존은 별도 대조가 필요합니다."
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="원문 UTF-8 텍스트/Markdown 파일")
    parser.add_argument("--output", type=Path, help="수정본 파일. 생략 시 스타일 신호만 보고")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()
    source = args.input.read_text(encoding="utf-8")
    revised = args.output.read_text(encoding="utf-8") if args.output else None
    result = audit(source, revised)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if revised is not None:
            print("리터럴 보존:", "PASS" if result["passed_literal_checks"] else "FAIL")
            for item in result["violations"]:
                print("  위반:", item)
            if "review_acronyms" in result:
                print("  기술 식별자 수동 확인:", result["review_acronyms"])
        print("스타일 검토 신호 (전):", {k: v for k, v in result["style_signals_before"].items() if v})
        if revised is not None:
            print("스타일 검토 신호 (후):", {k: v for k, v in result["style_signals_after"].items() if v})
        print("주의: 의미 보존 여부는 자동 판정하지 않습니다.")
    return 0 if result["passed_literal_checks"] else 2


if __name__ == "__main__":
    sys.exit(main())
