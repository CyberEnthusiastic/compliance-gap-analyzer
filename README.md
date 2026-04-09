# 📋 Compliance Gap Analyzer (RAG-based)

A local, API-free, RAG-style tool that takes a company's security policy document and tells you exactly which **SOC 2** or **ISO 27001** controls are covered, partially covered, or missing — with evidence snippets pulled from the policy itself.

**Zero external dependencies.** Runs on Python 3.8+ stdlib only. No OpenAI, no vector DB, no embedding model — just Counter-based TF-IDF + keyword matching + negation detection.

## Why this exists

When a customer asks "are you SOC 2 compliant?", most companies scramble through a 60-page policy doc and try to remember. This tool answers that in 2 seconds, with a per-control breakdown and the exact sentence that proves (or disproves) coverage.

## Features

- **Two frameworks bundled**: SOC 2 TSC (10 controls) and ISO 27001:2022 Annex A (10 controls). Extensible via JSON.
- **Coverage scoring**: 0–100 per control, combining keyword presence + TF-IDF cosine similarity.
- **Evidence extraction**: for every COVERED / PARTIAL control, pulls up to 3 verbatim sentences from the policy as proof.
- **Negation detection**: catches sneaky cases like *"we do NOT currently have MFA"* and down-weights them by 70%.
- **Remediation hints**: for every gap, generates a specific rewrite suggestion listing the missing keywords.
- **Dark-mode HTML report** + JSON output for pipelines.

## Quickstart

```bash
git clone https://github.com/CyberEnthusiastic/compliance-gap-analyzer.git
cd compliance-gap-analyzer

# Analyze the bundled sample policy against SOC 2
python analyzer.py samples/acme_security_policy.md

# Against ISO 27001
python analyzer.py samples/acme_security_policy.md -f frameworks/iso27001.json

# Open the HTML report
start reports/gap_report.html      # Windows
open  reports/gap_report.html      # macOS
xdg-open reports/gap_report.html   # Linux
```

## Sample output

```
============================================================
  [Compliance Gap Analyzer v1.0]
============================================================
  Policy    : samples/acme_security_policy.md
  Framework : SOC 2 Type II (Trust Services Criteria)
  Controls  : 10
  Covered   : 7
  Partial   : 2
  Missing   : 1
  Compliance: 80.0%
============================================================
[XX] CC1.1    Commitment to integrity and ethical values  (22.5%)
   missing: code of conduct, ethics, whistleblower, tone at the top

[--] CC2.1    Internal and external communication of security policies  (58.1%)
   missing: external parties

[OK] CC5.1    Logical access controls  (96.0%)
[OK] CC5.2    Encryption of data in transit and at rest  (92.0%)
[OK] CC6.6    Change management  (88.0%)
...
```

## How it works

### 1. Keyword presence (weight: 0.7)
Each control in the framework JSON defines a list of keywords. The analyzer lowercases the policy and checks how many of those keywords appear. Score = (found / total) × 100.

### 2. TF-IDF cosine similarity (weight: 0.3)
Both the control description and the whole policy get tokenized, stopwords removed, and turned into term-frequency Counters. A cosine similarity between the two vectors gives a 0–1 semantic similarity — captures cases where the policy uses synonyms or paraphrases the control intent.

### 3. Evidence extraction
The policy is split into sentences. For each found keyword, up to 3 sentences containing it are pulled as verbatim evidence and attached to the control result.

### 4. Negation detection
For each evidence sentence, the analyzer looks 5 tokens before each found keyword for any of:
`not, no, never, without, lack, lacking, absent, missing, don't, doesn't, didn't, won't, isn't`.
If found, the control's coverage score is multiplied by **0.3** — a policy saying "we do NOT have MFA" should NOT count as covering the MFA control.

### 5. Decision
- `≥ 70 AND no negation` → **COVERED**
- `≥ 40 OR found_keywords ≥ 1` → **PARTIAL**
- otherwise → **MISSING**

Final compliance score: `(covered + 0.5 × partial) / total × 100`.

## Framework JSON format

```json
{
  "name": "SOC 2 Type II",
  "version": "2017",
  "controls": [
    {
      "id": "CC5.1",
      "category": "Control Activities",
      "title": "Logical access controls",
      "description": "Access to information assets is restricted through MFA, RBAC, and quarterly reviews.",
      "keywords": ["access control", "MFA", "multi-factor", "RBAC", "access review"]
    }
  ]
}
```

To add NIST CSF, HIPAA, PCI-DSS, or GDPR, just drop a new JSON file in `frameworks/` and pass it with `-f`.

## Analyze your own policy

```bash
# PDF? Convert first, e.g. with pdftotext
pdftotext my_policy.pdf my_policy.txt
python analyzer.py my_policy.txt

# Custom framework
python analyzer.py my_policy.md -f frameworks/iso27001.json

# Custom output
python analyzer.py my_policy.md -o /tmp/report.json --html /tmp/report.html
```

## CI/CD integration

```yaml
# .github/workflows/compliance-drift.yml
on:
  push:
    paths:
      - 'docs/security-policy.md'

jobs:
  compliance-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: |
          git clone https://github.com/CyberEnthusiastic/compliance-gap-analyzer.git /tmp/cga
          python /tmp/cga/analyzer.py docs/security-policy.md
          # Fail PR if SOC 2 compliance drops below 75%
          python -c "import json; r=json.load(open('reports/gap_report.json')); exit(1 if r['summary']['compliance_percent']<75 else 0)"
```

## Roadmap

- [ ] NIST CSF 2.0 framework JSON
- [ ] HIPAA Security Rule framework JSON
- [ ] PCI-DSS v4.0 framework JSON
- [ ] Real sentence-transformers embeddings (optional — currently pure stdlib)
- [ ] LLM-generated remediation drafts (Claude/GPT optional backend)
- [ ] Multi-doc ingestion (combine policy + runbook + SOPs)
- [ ] Diff report against previous version ("what changed in our compliance posture?")

## License

MIT

---

Built by [CyberEnthusiastic](https://github.com/CyberEnthusiastic) · Part of the AI Security Projects series
