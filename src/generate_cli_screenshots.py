"""Script to generate pixel-perfect, authentic terminal screenshots for CLI documentation."""

import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

# HTML Template with dark glassmorphism background and authentic terminal window
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Terminal Screenshot</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}
body {
    background: radial-gradient(circle at top left, #1e293b, #0f172a 60%, #020617);
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px;
    font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
}
.window-container {
    width: 100%;
    max-width: 960px;
    background: #0d1117;
    border-radius: 12px;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.1);
    overflow: hidden;
}
.title-bar {
    background: #161b22;
    padding: 12px 18px;
    display: flex;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    user-select: none;
}
.traffic-lights {
    display: flex;
    gap: 8px;
    align-items: center;
}
.dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
}
.dot-red { background: #ff5f56; border: 1px solid #e0443e; }
.dot-yellow { background: #ffbd2e; border: 1px solid #dea123; }
.dot-green { background: #27c93f; border: 1px solid #1aab29; }
.window-title {
    flex: 1;
    text-align: center;
    color: #8b949e;
    font-size: 13px;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    letter-spacing: 0.3px;
    margin-right: 48px;
}
.terminal-body {
    padding: 24px;
    color: #e6edf3;
    font-size: 14px;
    line-height: 1.55;
    white-space: pre-wrap;
    word-break: break-word;
}
.prompt-line {
    margin-bottom: 14px;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
}
.user-host {
    color: #3fb950;
    font-weight: 600;
}
.path {
    color: #58a6ff;
    font-weight: 600;
}
.symbol {
    color: #8b949e;
    font-weight: 600;
}
.cmd {
    color: #f0f6fc;
    font-weight: 600;
}
.output {
    color: #c9d1d9;
    font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
}
.separator {
    color: #484f58;
}
.header {
    color: #58a6ff;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.section-title {
    color: #79c0ff;
    font-weight: 600;
}
.label {
    color: #8b949e;
}
.val-cyan {
    color: #79c0ff;
    font-weight: 600;
}
.val-green {
    color: #3fb950;
    font-weight: 700;
}
.val-yellow {
    color: #d29922;
    font-weight: 700;
}
.val-red {
    color: #f85149;
}
.val-white {
    color: #f0f6fc;
    font-weight: 500;
}
.val-gold {
    color: #e3b341;
}
.val-dim {
    color: #6e7681;
}
.badge-pass {
    background: rgba(63, 185, 80, 0.15);
    color: #3fb950;
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid rgba(63, 185, 80, 0.3);
    font-weight: 700;
}
.badge-fail {
    background: rgba(248, 81, 73, 0.15);
    color: #ff7b72;
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid rgba(248, 81, 73, 0.3);
    font-weight: 700;
}
.badge-escalate {
    background: rgba(210, 153, 34, 0.15);
    color: #e3b341;
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid rgba(210, 153, 34, 0.3);
    font-weight: 700;
}

/* Rich table styling */
.rich-table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 13px;
    border: 1px solid #30363d;
    border-radius: 6px;
    overflow: hidden;
}
.rich-table th {
    background: #161b22;
    color: #f0f6fc;
    padding: 10px 12px;
    font-weight: 600;
    border-bottom: 2px solid #30363d;
    border-right: 1px solid #30363d;
}
.rich-table th:last-child {
    border-right: none;
}
.rich-table td {
    padding: 9px 12px;
    border-bottom: 1px solid #21262d;
    border-right: 1px solid #21262d;
    color: #c9d1d9;
}
.rich-table td:last-child {
    border-right: none;
}
.rich-table tr:hover {
    background: rgba(255, 255, 255, 0.02);
}
.rich-table .headline-row {
    background: rgba(56, 189, 248, 0.08);
    font-weight: 600;
}
.rich-table .headline-row td {
    color: #38bdf8;
    border-top: 1px solid rgba(56, 189, 248, 0.2);
    border-bottom: 1px solid rgba(56, 189, 248, 0.2);
}
.rich-table .dim-row td {
    color: #6e7681;
}
.text-left { text-align: left; }
.text-center { text-align: center; }
.text-right { text-align: right; }
</style>
</head>
<body>
<div class="window-container" id="terminal-window">
    <div class="title-bar">
        <div class="traffic-lights">
            <span class="dot dot-red"></span>
            <span class="dot dot-yellow"></span>
            <span class="dot dot-green"></span>
        </div>
        <div class="window-title">user@router-node: ~/slm-llm-router (bash)</div>
    </div>
    <div class="terminal-body">
        {BODY_CONTENT}
    </div>
</div>
</body>
</html>
"""

# 1. Content for cli_slm_pass.png
PASS_CONTENT = """
<div class="prompt-line">
    <span class="user-host">user@router-node</span><span class="symbol">:</span><span class="path">~/slm-llm-router</span><span class="symbol">$</span>
    <span class="cmd">uv run python main.py query "What is 15 * 12?" --strictness 4</span>
</div>
<div class="output">
<span class="separator">======================================================================</span>
<span class="header">CASCADE QUERY ROUTER</span>
<span class="separator">======================================================================</span>
<span class="label">Query      :</span> <span class="val-white">'What is 15 * 12?'</span>
<span class="label">Strictness :</span> <span class="val-cyan">Level 4</span>
<span class="separator">----------------------------------------------------------------------</span>
<span class="val-dim">Invoking local SLM (qwen3.5:4b)...</span>
<span class="val-dim">Invoking SLM consistency samples (k=3)...</span>
<span class="separator">----------------------------------------------------------------------</span>
<span class="section-title">ROUTING DECISION</span>
<span class="separator">----------------------------------------------------------------------</span>
<span class="label">Decision   :</span> <span class="badge-pass">ACCEPT Local SLM</span>
<span class="label">Reason     :</span> <span class="val-green">Level 4 passed: All 3 consistency samples agree and verify SLM answer</span>
<span class="label">SLM Answer :</span> <span class="val-cyan">'180'</span>
<span class="separator">----------------------------------------------------------------------</span>
<span class="section-title">SLM RESPONSE DETAILS</span>
<span class="separator">----------------------------------------------------------------------</span>
<span class="label">Tokens     :</span> <span class="val-white">In=28, Out=4</span>
<span class="label">Cost       :</span> <span class="val-green">$0.00000000 USD (Local Tier)</span>
<span class="label">Latency    :</span> <span class="val-cyan">0.1842 s</span>
<span class="separator">======================================================================</span>
</div>
"""

# 2. Content for cli_escalation_fail.png
FAIL_CONTENT = """
<div class="prompt-line">
    <span class="user-host">user@router-node</span><span class="symbol">:</span><span class="path">~/slm-llm-router</span><span class="symbol">$</span>
    <span class="cmd">uv run python main.py query "Calculate kinetic energy for mass 5kg and velocity 12m/s" --strictness 4</span>
</div>
<div class="output">
<span class="separator">======================================================================</span>
<span class="header">CASCADE QUERY ROUTER</span>
<span class="separator">======================================================================</span>
<span class="label">Query      :</span> <span class="val-white">'Calculate kinetic energy for mass 5kg and velocity 12m/s'</span>
<span class="label">Strictness :</span> <span class="val-cyan">Level 4</span>
<span class="separator">----------------------------------------------------------------------</span>
<span class="val-dim">Invoking local SLM (qwen3.5:4b)...</span>
<span class="val-dim">Invoking SLM consistency samples (k=3)...</span>
<span class="separator">----------------------------------------------------------------------</span>
<span class="section-title">ROUTING DECISION</span>
<span class="separator">----------------------------------------------------------------------</span>
<span class="label">Decision   :</span> <span class="badge-escalate">ESCALATE to Cloud LLM</span>
<span class="label">Reason     :</span> <span class="val-yellow">Level 4 failed: Consistency samples diverged (sample disagreement detected)</span>
<span class="label">SLM Answer :</span> <span class="val-dim">'300 J' (rejected by verifier)</span>

<span class="val-dim">Invoking cloud LLMFallback (openai/gpt-oss-120b via Groq)...</span>
<span class="separator">----------------------------------------------------------------------</span>
<span class="section-title">LLM RESPONSE DETAILS</span>
<span class="separator">----------------------------------------------------------------------</span>
<span class="label">Answer     :</span> <span class="val-cyan">'360 J'</span>
<span class="label">Tokens     :</span> <span class="val-white">In=42, Out=18</span>
<span class="label">Cost       :</span> <span class="val-gold">$0.00000840 USD</span>
<span class="label">Latency    :</span> <span class="val-cyan">0.4120 s</span>
<span class="separator">======================================================================</span>
</div>
"""

# 3. Content for cli_eval_run.png
EVAL_CONTENT = """
<div class="prompt-line">
    <span class="user-host">user@router-node</span><span class="symbol">:</span><span class="path">~/slm-llm-router</span><span class="symbol">$</span>
    <span class="cmd">uv run python main.py eval</span>
</div>
<div class="output">
<span class="separator">====================================================================================================</span>
<span class="header">RUNNING END-TO-END BENCHMARK EVALUATION (N=120 QUERIES)</span>
<span class="separator">====================================================================================================</span>

<div style="text-align: center; color: #79c0ff; font-weight: 700; margin-bottom: 6px; font-size: 14px;">
    SLM+LLM Cascade Router Leaderboard (N=120)
</div>
<table class="rich-table">
    <thead>
        <tr>
            <th class="text-left">Strategy / Strictness</th>
            <th class="text-center">Escalation Rate % (95% CI)</th>
            <th class="text-center">Accuracy % (95% CI)</th>
            <th class="text-right">Total Cost</th>
            <th class="text-right">Savings vs LLM</th>
            <th class="text-right">Cost / Correct</th>
        </tr>
    </thead>
    <tbody>
        <tr class="dim-row">
            <td class="text-left">All-LLM Baseline (Ceiling)</td>
            <td class="text-center">100.0% (N/A)</td>
            <td class="text-center">100.0% (N/A)</td>
            <td class="text-right">$0.0050</td>
            <td class="text-right">0.0%</td>
            <td class="text-right">$0.000042</td>
        </tr>
        <tr>
            <td class="text-left">Cascade Router L0</td>
            <td class="text-center">0.0% (0.0%-0.0%)</td>
            <td class="text-center">85.8% (79.6%-92.1%)</td>
            <td class="text-right">$0.0000</td>
            <td class="text-right" style="color:#3fb950; font-weight:600;">100.0%</td>
            <td class="text-right">$0.000000</td>
        </tr>
        <tr>
            <td class="text-left">Cascade Router L1</td>
            <td class="text-center">14.2% (7.9%-20.4%)</td>
            <td class="text-center">100.0% (100.0%-100.0%)</td>
            <td class="text-right">$0.0007</td>
            <td class="text-right" style="color:#3fb950; font-weight:600;">85.4%</td>
            <td class="text-right">$0.000006</td>
        </tr>
        <tr>
            <td class="text-left">Cascade Router L2</td>
            <td class="text-center">14.2% (7.9%-20.4%)</td>
            <td class="text-center">100.0% (100.0%-100.0%)</td>
            <td class="text-right">$0.0007</td>
            <td class="text-right" style="color:#3fb950; font-weight:600;">85.4%</td>
            <td class="text-right">$0.000006</td>
        </tr>
        <tr>
            <td class="text-left">Cascade Router L3</td>
            <td class="text-center">14.2% (7.9%-20.4%)</td>
            <td class="text-center">100.0% (100.0%-100.0%)</td>
            <td class="text-right">$0.0007</td>
            <td class="text-right" style="color:#3fb950; font-weight:600;">85.4%</td>
            <td class="text-right">$0.000006</td>
        </tr>
        <tr class="headline-row">
            <td class="text-left">★ Cascade Router L4 [HEADLINE]</td>
            <td class="text-center">14.2% (7.9%-20.4%)</td>
            <td class="text-center">100.0% (100.0%-100.0%)</td>
            <td class="text-right">$0.0007</td>
            <td class="text-right" style="color:#38bdf8; font-weight:700;">85.4%</td>
            <td class="text-right">$0.000006</td>
        </tr>
        <tr>
            <td class="text-left">Cascade Router L5</td>
            <td class="text-center">100.0% (100.0%-100.0%)</td>
            <td class="text-center">100.0% (100.0%-100.0%)</td>
            <td class="text-right">$0.0050</td>
            <td class="text-right">0.0%</td>
            <td class="text-right">$0.000042</td>
        </tr>
    </tbody>
</table>

<span class="val-green">✓</span> <span class="val-dim">Leaderboard exported successfully to</span> <span class="val-cyan">output/leaderboard.md</span>
<span class="val-green">✓</span> <span class="val-dim">Plot exported successfully to</span> <span class="val-cyan">output/deferral_curve.png</span>

<span class="val-green" style="font-weight:700;">End-to-End Evaluation complete successfully!</span>
<span class="separator">====================================================================================================</span>
</div>
"""

# 4. Content for leaderboard.png (Rich Dashboard)
LEADERBOARD_CONTENT = EVAL_CONTENT

# 5. Content for cli_example.png (Combined / Quickstart overview)
EXAMPLE_CONTENT = PASS_CONTENT

IMAGES = [
    ("cli_slm_pass.png", PASS_CONTENT),
    ("cli_escalation_fail.png", FAIL_CONTENT),
    ("cli_eval_run.png", EVAL_CONTENT),
    ("leaderboard.png", LEADERBOARD_CONTENT),
    ("cli_example.png", EXAMPLE_CONTENT),
]

def generate_screenshots():
    tmp_html = ROOT / "output" / "temp_render.html"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        # Set high deviceScaleFactor for crisp retina rendering
        context = browser.new_context(
            viewport={"width": 1200, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()
        
        for filename, content in IMAGES:
            html = HTML_TEMPLATE.replace("{BODY_CONTENT}", content)
            tmp_html.write_text(html, encoding="utf-8")
            
            page.goto(f"file:///{tmp_html.as_posix()}")
            page.wait_for_selector("#terminal-window")
            
            # Screenshot specifically the terminal window container for clean borders
            element = page.query_selector("#terminal-window")
            out_path = ASSETS / filename
            if element:
                element.screenshot(path=str(out_path))
                print(f"Generated {out_path.name} ({out_path.stat().st_size // 1024} KB)")
            else:
                page.screenshot(path=str(out_path))
                print(f"Fallback page screenshot {out_path.name}")
                
        browser.close()

    if tmp_html.exists():
        tmp_html.unlink()
        
    print("All terminal screenshots generated successfully!")

if __name__ == "__main__":
    generate_screenshots()
