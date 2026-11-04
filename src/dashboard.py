"""Dashboard generator for credit-risk-lab.

Reads results/results.json and results/model_grades.json and writes a single
self-contained dashboard.html at the repo root: no external CDN, no
JavaScript at all, charts are inline SVG generated here. Opens from file://.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "results.json"
GRADES = ROOT / "results" / "model_grades.json"
OUT = ROOT / "dashboard.html"

INK = "#1a1a1a"
GREY = "#5a6570"
ACCENT = "#b03a2e"
BLUE = "#2c5f8a"
AMBER = "#d9903f"
LIGHT = "#eef1f4"


def money(v):
    return f"NT${v:,.0f}"


def fmt(v, digits=4):
    return f"{v:.{digits}f}"


def hbar_chart(items, width=680, row_h=30, color="#2c5f8a", value_fmt=str):
    """Horizontal bars: items = list of (label, value)."""
    max_v = max(v for _, v in items) or 1
    label_w, val_w = 90, 190
    bar_w = width - label_w - val_w
    h = row_h * len(items) + 8
    parts = [f'<svg width="{width}" height="{h}" role="img">']
    for i, (label, v) in enumerate(items):
        y = 4 + i * row_h
        w = max(1, bar_w * v / max_v)
        parts.append(f'<text x="0" y="{y + 16}" font-size="13" fill="{INK}">{label}</text>')
        parts.append(f'<rect x="{label_w}" y="{y + 3}" width="{w:.1f}" height="{row_h - 10}" fill="{color}"/>')
        parts.append(f'<text x="{label_w + w + 8:.1f}" y="{y + 16}" font-size="13" fill="{GREY}">{value_fmt(v)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def calibration_chart(calib, size=320):
    pad_l, pad_b, pad_t, pad_r = 44, 36, 14, 14
    plot = size - pad_l - pad_r
    plot_h = size - pad_b - pad_t
    vmax = 0.8
    def X(v): return pad_l + plot * v / vmax
    def Y(v): return pad_t + plot_h * (1 - v / vmax)
    parts = [f'<svg width="{size + 40}" height="{size}" role="img">']
    for t in [0, 0.2, 0.4, 0.6, 0.8]:
        parts.append(f'<line x1="{X(t):.1f}" y1="{Y(0):.1f}" x2="{X(t):.1f}" y2="{Y(vmax):.1f}" stroke="{LIGHT}"/>')
        parts.append(f'<line x1="{X(0):.1f}" y1="{Y(t):.1f}" x2="{X(vmax):.1f}" y2="{Y(t):.1f}" stroke="{LIGHT}"/>')
        parts.append(f'<text x="{X(t) - 8:.1f}" y="{Y(0) + 18:.1f}" font-size="11" fill="{GREY}">{t:.1f}</text>')
        parts.append(f'<text x="{X(0) - 30:.1f}" y="{Y(t) + 4:.1f}" font-size="11" fill="{GREY}">{t:.1f}</text>')
    parts.append(f'<line x1="{X(0):.1f}" y1="{Y(0):.1f}" x2="{X(vmax):.1f}" y2="{Y(vmax):.1f}" stroke="{GREY}" stroke-dasharray="5 4"/>')
    pts = " ".join(f"{X(b['pred']):.1f},{Y(b['obs']):.1f}" for b in calib)
    parts.append(f'<polyline points="{pts}" fill="none" stroke="{ACCENT}" stroke-width="2"/>')
    for b in calib:
        parts.append(f'<circle cx="{X(b["pred"]):.1f}" cy="{Y(b["obs"]):.1f}" r="4" fill="{ACCENT}"/>')
    parts.append(f'<text x="{X(0.4) - 30:.1f}" y="{size - 2}" font-size="12" fill="{GREY}">predicted PD</text>')
    parts.append(f'<text x="4" y="{Y(0.45):.1f}" font-size="12" fill="{GREY}" transform="rotate(-90 12 {Y(0.45):.1f})">observed default rate</text>')
    parts.append("</svg>")
    return "".join(parts)


def distribution_chart(dist, width=760, height=260):
    pad_l, pad_b, pad_t = 48, 30, 10
    plot_w, plot_h = width - pad_l - 10, height - pad_b - pad_t
    max_v = max(max(r["default"], r["non_default"]) for r in dist) or 1
    n = len(dist)
    slot = plot_w / n
    bw = slot / 2 - 1
    parts = [f'<svg width="{width}" height="{height}" role="img">']
    def Y(v): return pad_t + plot_h * (1 - v / max_v)
    for t in [0, 0.5, 1.0]:
        v = max_v * t
        parts.append(f'<line x1="{pad_l}" y1="{Y(v):.1f}" x2="{width - 10}" y2="{Y(v):.1f}" stroke="{LIGHT}"/>')
        parts.append(f'<text x="4" y="{Y(v) + 4:.1f}" font-size="11" fill="{GREY}">{int(v):,}</text>')
    for i, r in enumerate(dist):
        x = pad_l + i * slot
        parts.append(f'<rect x="{x + 1:.1f}" y="{Y(r["non_default"]):.1f}" width="{bw:.1f}" height="{pad_t + plot_h - Y(r["non_default"]):.1f}" fill="#7a8a99"/>')
        parts.append(f'<rect x="{x + 1 + bw:.1f}" y="{Y(r["default"]):.1f}" width="{bw:.1f}" height="{pad_t + plot_h - Y(r["default"]):.1f}" fill="{ACCENT}"/>')
        if i % 2 == 0:
            parts.append(f'<text x="{x + 1:.1f}" y="{height - 8}" font-size="10" fill="{GREY}">{r["bin_start"]:.1f}</text>')
    parts.append(f'<rect x="{pad_l}" y="{height - 26}" width="0" height="0" fill="none"/>')
    parts.append("</svg>")
    return "".join(parts)


def build_html(results: dict, grades: dict) -> str:
    ds, st = results["dataset"], results["staging"]
    champ = results["champion"]
    rows = ""
    for name, m in results["models"].items():
        g = grades["models"][name]
        star = " (champion)" if name == champ else ""
        rows += (f"<tr><td><b>{name}</b>{star}</td><td>{fmt(m['auc'])}</td>"
                 f"<td>{fmt(m['ks'])}</td><td>{fmt(m['gini'])}</td><td>{fmt(m['brier'])}</td>"
                 f"<td>{fmt(m['score_psi'])}</td>"
                 f"<td><b>{g['total_points']:.2f}</b> / 1000</td>"
                 f"<td><span class='band band-{g['letter_band']}'>{g['letter_band']}</span></td></tr>")
    deductions = ""
    for name, g in grades["models"].items():
        items = "".join(
            f"<li>{c['component']}: -{c['deduction']:.2f} pts ({c['detail']})</li>"
            for c in g["components"] if c["deduction"] > 0)
        deductions += f"<h3>{name}: deductions from 1000</h3><ul>{items}</ul>"
    stage_accounts = [(f"Stage {s['stage']}", s["accounts"]) for s in st["by_stage"]]
    stage_ecl = [(f"Stage {s['stage']}", s["ecl"]) for s in st["by_stage"]]
    stage_colors = {1: BLUE, 2: AMBER, 3: ACCENT}
    accts_svg = ""
    for label, v in stage_accounts:
        accts_svg += hbar_chart([(label, v)], color=stage_colors[int(label[-1])],
                                value_fmt=lambda x: f"{x:,.0f} accounts")
    ecl_svg = ""
    for label, v in stage_ecl:
        ecl_svg += hbar_chart([(label, v)], color=stage_colors[int(label[-1])],
                              value_fmt=money)
    stage_rows = "".join(
        f"<tr><td>Stage {s['stage']}</td><td>{s['accounts']:,}</td>"
        f"<td>{s['observed_default_rate'] * 100:.1f}%</td><td>{money(s['ead'])}</td>"
        f"<td>{money(s['ecl'])}</td></tr>" for s in st["by_stage"])
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>credit-risk-lab dashboard</title>
<style>
body {{ font-family: Helvetica, Arial, sans-serif; color: {INK}; margin: 28px auto; max-width: 860px; padding: 0 16px; }}
h1 {{ font-size: 24px; margin-bottom: 2px; }} h2 {{ font-size: 17px; margin-top: 30px; border-bottom: 2px solid {INK}; padding-bottom: 4px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
th, td {{ border-bottom: 1px solid #d8dde2; padding: 6px 8px; text-align: right; }}
th:first-child, td:first-child {{ text-align: left; }}
.cards {{ display: flex; gap: 12px; flex-wrap: wrap; margin-top: 14px; }}
.card {{ background: {LIGHT}; padding: 10px 14px; border-radius: 6px; font-size: 14px; }}
.card b {{ display: block; font-size: 19px; }}
.band {{ padding: 2px 10px; border-radius: 10px; color: #fff; font-weight: bold; }}
.band-A {{ background: #1e7d32; }} .band-B {{ background: {BLUE}; }} .band-C {{ background: {AMBER}; }}
.band-D {{ background: #e07b39; }} .band-F {{ background: {ACCENT}; }}
.small {{ color: {GREY}; font-size: 13px; }} li {{ font-size: 14px; margin: 3px 0; }}
.legend {{ font-size: 13px; color: {GREY}; }}
.sw {{ display: inline-block; width: 11px; height: 11px; margin: 0 4px 0 12px; }}
</style></head><body>
<h1>credit-risk-lab dashboard</h1>
<p class="small">Generated by src/dashboard.py from results/results.json and results/model_grades.json.
No external assets, no JavaScript. Every number comes from the pipeline run.</p>
<div class="cards">
<div class="card">Accounts<b>{ds['rows']:,}</b></div>
<div class="card">Observed default rate<b>{ds['default_rate'] * 100:.2f}%</b></div>
<div class="card">Champion model<b>{champ}</b></div>
<div class="card">Portfolio EAD<b>{money(st['total_ead'])}</b></div>
<div class="card">Portfolio ECL<b>{money(st['total_ecl'])}</b></div>
</div>
<h2>Model comparison and grades</h2>
<table><tr><th>Model</th><th>AUC</th><th>KS</th><th>Gini</th><th>Brier</th><th>Score PSI</th><th>Grade</th><th>Band</th></tr>
{rows}</table>
<p class="small">Scorecard: discrimination 500 (AUC 250, KS 150, Gini 100), calibration 300
(Brier 150, calibration MAE 150), stability 200 (score PSI). Bands: A 900+, B 800+, C 700+, D 600+, F below 600.</p>
{deductions}
<h2>IFRS 9 style staging</h2>
<table><tr><th>Stage</th><th>Accounts</th><th>Observed default rate</th><th>EAD</th><th>ECL</th></tr>
{stage_rows}
<tr><td><b>Total</b></td><td><b>{ds['rows']:,}</b></td><td></td><td><b>{money(st['total_ead'])}</b></td><td><b>{money(st['total_ecl'])}</b></td></tr></table>
<h3>Accounts by stage</h3>{accts_svg}
<h3>ECL by stage</h3>{ecl_svg}
<p class="small">Policy: {st['policy']} LGD {st['lgd_assumption']:.0%} and the
{st['lifetime_years_assumption']}-year lifetime horizon are stated lab assumptions, not measured values.</p>
<h2>Calibration, champion model (test set)</h2>
{calibration_chart(results['validation']['calibration_test'])}
<p class="legend">Dashed line is perfect calibration. Points are the 10 test-set bins.</p>
<h2>Score distribution by outcome, champion model (test set)</h2>
{distribution_chart(results['validation']['score_distribution'])}
<p class="legend"><span class="sw" style="background:#7a8a99"></span>non-default
<span class="sw" style="background:{ACCENT}"></span>default. X axis: predicted PD bin start.</p>
<h2>Limits</h2>
<p class="small">Public-data lab on the UCI credit dataset (Taiwan, 2005). Not a production
system and not employment experience in credit risk. See MODEL_CARD.md for intended use,
assumptions, and limits.</p>
</body></html>"""


def build(results_path: Path = RESULTS, grades_path: Path = GRADES,
          out_path: Path = OUT) -> Path:
    results = json.loads(Path(results_path).read_text())
    if Path(grades_path).exists():
        grades = json.loads(Path(grades_path).read_text())
    else:
        import sys
        sys.path.insert(0, str(ROOT / "src"))
        from grading import grade_all
        grades = grade_all(results)
    Path(out_path).write_text(build_html(results, grades))
    return Path(out_path)


if __name__ == "__main__":
    p = build()
    print("wrote", p)
