"""
Compliance Gap Analyzer (RAG-based)

Takes a company's security policy document and compares each framework
control against the policy using:

  1. Keyword presence matching (rule-based)
  2. TF-IDF cosine similarity (semantic-lite RAG without embeddings)
  3. Negation detection (catches "we do NOT have MFA")

For each control, outputs:
  - coverage_score (0-100)
  - status (COVERED / PARTIAL / MISSING)
  - matched evidence snippets from the policy
  - remediation guidance

No external APIs, no vector DB - runs entirely locally in pure stdlib + regex.

Author: Adithya Vasamsetti (CyberEnthusiastic)
"""
import re
import os
import json
import math
import argparse
from collections import Counter
from dataclasses import dataclass, asdict, field
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict


STOPWORDS = set("""a an and are as at be been but by for if in into is it
its no not of on or such that the their then there these they this to was
will with we our us i me you your he she his her our they them""".split())

NEGATION_TOKENS = {"not", "no", "never", "without", "lack", "lacking", "absent",
                   "missing", "don't", "doesn't", "didn't", "won't", "isn't"}


def tokenize(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    return [t for t in text.split() if t and t not in STOPWORDS and len(t) > 2]


def sentences(text: str) -> List[str]:
    # naive but effective sentence split
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [p.strip() for p in parts if p.strip()]


def cosine_sim(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[k] * b.get(k, 0) for k in a)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


@dataclass
class ControlResult:
    control_id: str
    title: str
    category: str
    coverage_score: float
    status: str  # COVERED / PARTIAL / MISSING
    keywords_found: List[str]
    keywords_missing: List[str]
    similarity: float
    evidence: List[str]
    negation_flag: bool
    remediation: str = ""


class ComplianceAnalyzer:
    def __init__(self, framework_path: str):
        self.framework = json.loads(Path(framework_path).read_text(encoding="utf-8"))
        self.framework_name = self.framework["name"]

    def analyze(self, policy_text: str) -> List[ControlResult]:
        results = []
        policy_lower = policy_text.lower()
        policy_sentences = sentences(policy_text)
        policy_tokens = tokenize(policy_text)
        policy_vec = Counter(policy_tokens)

        for ctrl in self.framework["controls"]:
            keywords = [k.lower() for k in ctrl["keywords"]]
            found_kw = []
            missing_kw = []

            # 1. Keyword presence
            for kw in keywords:
                if kw in policy_lower:
                    found_kw.append(kw)
                else:
                    missing_kw.append(kw)

            keyword_score = (len(found_kw) / len(keywords)) * 100 if keywords else 0

            # 2. TF-IDF cosine similarity
            ctrl_vec = Counter(tokenize(ctrl["description"] + " " + ctrl["title"]))
            sim = cosine_sim(ctrl_vec, policy_vec)

            # 3. Evidence: find sentences that match any of the found keywords
            evidence = []
            for sent in policy_sentences:
                s_lower = sent.lower()
                if any(kw in s_lower for kw in found_kw):
                    evidence.append(sent[:220])
                    if len(evidence) >= 3:
                        break

            # 4. Negation detection - if evidence sentence contains negation near a keyword
            negation_flag = False
            for sent in evidence:
                s_lower = sent.lower()
                tokens = s_lower.split()
                for kw in found_kw:
                    if kw in s_lower:
                        # look in a 5-token window before the keyword for negation
                        idx_matches = [i for i, t in enumerate(tokens) if kw in t]
                        for idx in idx_matches:
                            window = tokens[max(0, idx - 5):idx]
                            if any(neg in window for neg in NEGATION_TOKENS):
                                negation_flag = True
                                break

            # 5. Combine scores
            coverage = 0.7 * keyword_score + 0.3 * (sim * 100)
            if negation_flag:
                coverage *= 0.3  # heavy penalty - explicit negation

            if coverage >= 70 and not negation_flag:
                status = "COVERED"
                remediation = "Control appears satisfied. Recommend auditor spot-check during assessment."
            elif coverage >= 40 or (found_kw and not negation_flag):
                status = "PARTIAL"
                remediation = (
                    f"Policy mentions {', '.join(found_kw[:3])} but lacks "
                    f"{', '.join(missing_kw[:3])}. Add a dedicated section referencing "
                    f"'{ctrl['title']}' with measurable criteria."
                )
            else:
                status = "MISSING"
                remediation = (
                    f"No evidence found in the policy for '{ctrl['title']}'. "
                    f"Draft a new section covering: {', '.join(keywords[:4])}. "
                    f"Include ownership, frequency, and measurement."
                )

            results.append(ControlResult(
                control_id=ctrl["id"],
                title=ctrl["title"],
                category=ctrl["category"],
                coverage_score=round(coverage, 1),
                status=status,
                keywords_found=found_kw,
                keywords_missing=missing_kw,
                similarity=round(sim, 3),
                evidence=evidence,
                negation_flag=negation_flag,
                remediation=remediation,
            ))
        return results

    def summary(self, results: List[ControlResult]) -> Dict:
        total = len(results)
        covered = sum(1 for r in results if r.status == "COVERED")
        partial = sum(1 for r in results if r.status == "PARTIAL")
        missing = sum(1 for r in results if r.status == "MISSING")
        avg_coverage = sum(r.coverage_score for r in results) / total if total else 0
        return {
            "framework": self.framework_name,
            "total_controls": total,
            "covered": covered,
            "partial": partial,
            "missing": missing,
            "avg_coverage": round(avg_coverage, 1),
            "compliance_percent": round((covered + partial * 0.5) / total * 100, 1) if total else 0,
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        }


def main():
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(
        description="Compliance Gap Analyzer - maps a policy against SOC2/ISO27001"
    )
    parser.add_argument("policy", help="Path to the policy text/markdown file")
    parser.add_argument("-f", "--framework", default="frameworks/soc2.json",
                        help="Framework JSON file (default: SOC2)")
    parser.add_argument("-o", "--output", default="reports/gap_report.json")
    parser.add_argument("--html", default="reports/gap_report.html")
    args = parser.parse_args()

    policy_text = Path(args.policy).read_text(encoding="utf-8")
    analyzer = ComplianceAnalyzer(args.framework)
    results = analyzer.analyze(policy_text)
    summary = analyzer.summary(results)

    print("=" * 60)
    print("  [Compliance Gap Analyzer v1.0]")
    print("=" * 60)
    print(f"  Policy    : {args.policy}")
    print(f"  Framework : {summary['framework']}")
    print(f"  Controls  : {summary['total_controls']}")
    print(f"  Covered   : {summary['covered']}")
    print(f"  Partial   : {summary['partial']}")
    print(f"  Missing   : {summary['missing']}")
    print(f"  Compliance: {summary['compliance_percent']}%")
    print("=" * 60)

    for r in sorted(results, key=lambda x: x.coverage_score):
        icon = {"COVERED": "[OK]", "PARTIAL": "[--]", "MISSING": "[XX]"}[r.status]
        print(f"{icon} {r.control_id:<8} {r.title}  ({r.coverage_score}%)")
        if r.negation_flag:
            print(f"   ! Negation detected in policy text")
        if r.keywords_missing:
            print(f"   missing: {', '.join(r.keywords_missing[:4])}")
        print()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as fp:
        json.dump({
            "summary": summary,
            "results": [asdict(r) for r in results]
        }, fp, indent=2)
    print(f"[+] JSON report: {args.output}")

    from report_generator import generate_html
    generate_html(summary, results, args.html)
    print(f"[+] HTML report: {args.html}")


if __name__ == "__main__":
    main()
