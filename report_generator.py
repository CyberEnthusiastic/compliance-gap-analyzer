"""HTML report generator for Compliance Gap Analyzer."""
import os
from html import escape


def generate_html(summary, results, output_path):
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    status_colors = {
        "COVERED": "#34c759",
        "PARTIAL": "#ff9500",
        "MISSING": "#ff3b30",
    }

    rows = []
    for i, r in enumerate(sorted(results, key=lambda x: (x.status != "MISSING", x.coverage_score))):
        color = status_colors[r.status]
        bar_w = max(2, int(r.coverage_score))
        ev_html = "".join(f'<div class="ev">"{escape(e)}"</div>' for e in r.evidence)
        missing_chips = "".join(f'<span class="chip miss">{escape(k)}</span>' for k in r.keywords_missing[:8])
        found_chips = "".join(f'<span class="chip found">{escape(k)}</span>' for k in r.keywords_found[:8])

        neg_warn = '<div class="neg">⚠ Negation detected - policy explicitly contradicts this control</div>' if r.negation_flag else ""

        rows.append(f"""
        <div class="ctrl" data-status="{r.status}">
          <div class="chead" onclick="toggle({i})">
            <span class="status" style="background:{color}">{r.status}</span>
            <span class="cid">{r.control_id}</span>
            <span class="title">{escape(r.title)}</span>
            <span class="cat">{escape(r.category)}</span>
            <span class="pct">{r.coverage_score}%</span>
          </div>
          <div class="bar"><div class="fill" style="width:{bar_w}%;background:{color}"></div></div>
          <div class="cbody" id="cb-{i}">
            {neg_warn}
            <div class="row"><b>Similarity (TF-IDF cosine):</b> {r.similarity}</div>
            <div class="row"><b>Keywords found:</b> {found_chips or '<i style="color:#64748b">none</i>'}</div>
            <div class="row"><b>Keywords missing:</b> {missing_chips or '<i style="color:#64748b">none</i>'}</div>
            <div class="row"><b>Evidence in policy:</b></div>
            {ev_html or '<div class="ev empty">No matching evidence found</div>'}
            <div class="rem"><b>Remediation:</b> {escape(r.remediation)}</div>
          </div>
        </div>
        """)

    score = summary["compliance_percent"]
    score_color = "#34c759" if score >= 80 else "#ff9500" if score >= 50 else "#ff3b30"

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Compliance Gap Report</title>
<style>
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0f1a;color:#cbd5e1;margin:0;padding:24px;max-width:1100px;margin:auto}}
  h1{{color:#60a5fa;margin:0 0 4px;font-size:26px}}
  .subtitle{{color:#64748b;margin-bottom:20px;font-size:13px}}
  .hero{{background:#0f172a;border:1px solid #1e293b;border-radius:14px;padding:26px;margin-bottom:20px;display:flex;gap:22px;align-items:center}}
  .big{{font-size:54px;font-weight:800;color:{score_color};line-height:1}}
  .bigl{{font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:.5px;margin-top:4px}}
  .stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;flex:1}}
  .s{{background:#020617;border:1px solid #1e293b;border-radius:10px;padding:12px}}
  .s .n{{font-size:22px;font-weight:700}}
  .s .l{{font-size:11px;color:#64748b;text-transform:uppercase}}
  .ctrl{{background:#0f172a;border:1px solid #1e293b;border-radius:10px;margin-bottom:10px;overflow:hidden}}
  .chead{{display:flex;align-items:center;gap:12px;padding:14px 18px;cursor:pointer}}
  .chead:hover{{background:#131e35}}
  .status{{color:#000;font-weight:800;font-size:10px;padding:3px 10px;border-radius:20px;min-width:70px;text-align:center}}
  .cid{{color:#fbbf24;font-family:monospace;font-size:12px;min-width:60px}}
  .title{{flex:1;color:#e2e8f0;font-weight:600;font-size:14px}}
  .cat{{color:#64748b;font-size:11px}}
  .pct{{color:#94a3b8;font-weight:700;font-size:13px;min-width:50px;text-align:right}}
  .bar{{height:3px;background:#020617;margin:0 18px}}
  .fill{{height:100%;transition:width .4s}}
  .cbody{{display:none;padding:18px;border-top:1px solid #1e293b;margin-top:8px}}
  .cbody.open{{display:block}}
  .row{{margin:8px 0;font-size:13px}}
  .chip{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;margin:2px}}
  .chip.found{{background:rgba(52,199,89,.15);color:#34c759;border:1px solid rgba(52,199,89,.3)}}
  .chip.miss{{background:rgba(255,59,48,.1);color:#ff3b30;border:1px solid rgba(255,59,48,.25)}}
  .ev{{background:#020617;padding:10px 14px;border-left:3px solid #60a5fa;border-radius:4px;font-size:12px;color:#cbd5e1;margin:6px 0;font-style:italic}}
  .ev.empty{{border-left-color:#334155;color:#475569}}
  .neg{{background:rgba(255,59,48,.1);border:1px solid #ff3b30;padding:10px 14px;border-radius:6px;color:#ff6b6b;font-size:13px;margin-bottom:10px}}
  .rem{{background:#020617;padding:12px 14px;border-radius:6px;margin-top:14px;font-size:13px}}
  .footer{{margin-top:30px;color:#334155;font-size:11px;text-align:center}}
</style>
</head>
<body>
  <h1>📋 Compliance Gap Report</h1>
  <div class="subtitle">{escape(summary['framework'])} · Generated {summary['generated_at']}</div>

  <div class="hero">
    <div>
      <div class="big">{score}%</div>
      <div class="bigl">Overall Compliance</div>
    </div>
    <div class="stats">
      <div class="s"><div class="n" style="color:#34c759">{summary['covered']}</div><div class="l">Covered</div></div>
      <div class="s"><div class="n" style="color:#ff9500">{summary['partial']}</div><div class="l">Partial</div></div>
      <div class="s"><div class="n" style="color:#ff3b30">{summary['missing']}</div><div class="l">Missing</div></div>
    </div>
  </div>

  {''.join(rows)}

  <div class="footer">Compliance Gap Analyzer · github.com/CyberEnthusiastic</div>

<script>
function toggle(i){{document.getElementById('cb-'+i).classList.toggle('open');}}
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as fp:
        fp.write(html)
