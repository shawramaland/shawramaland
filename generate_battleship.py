import requests
import os
from datetime import datetime

USERNAME = os.environ.get("USERNAME", "shawramaland")
TOKEN = os.environ.get("GH_TOKEN", "")

def get_contributions():
    query = """
    query($username: String!) {
      user(login: $username) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
                weekday
              }
            }
          }
        }
      }
    }
    """
    headers = {"Authorization": f"bearer {TOKEN}"}
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"username": USERNAME}},
        headers=headers,
        timeout=10
    )
    r.raise_for_status()
    data = r.json()
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return cal["weeks"], cal["totalContributions"]

def generate_svg(weeks, total):
    CELL = 13
    GAP = 2
    STEP = CELL + GAP
    LEFT_PAD = 28
    TOP_PAD = 52
    RIGHT_PAD = 15
    BOTTOM_PAD = 30

    cols = len(weeks)
    rows = 7

    width = LEFT_PAD + cols * STEP + RIGHT_PAD
    height = TOP_PAD + rows * STEP + BOTTOM_PAD

    day_labels = ['', 'Mon', '', 'Wed', '', 'Fri', '']

    out = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" overflow="visible">')

    # ── DEFS: gradients + CSS keyframes (defined once) ──────────────────────
    out.append(f'''<defs>
<radialGradient id="gh" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#ff2200"/><stop offset="100%" stop-color="#880000"/></radialGradient>
<radialGradient id="gm" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#ffaa00"/><stop offset="100%" stop-color="#664400"/></radialGradient>
<radialGradient id="gq" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#1a2a1a"/><stop offset="100%" stop-color="#0a120a"/></radialGradient>
<filter id="fh" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="fm" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="1.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<style>
.rm{{fill:none;stroke:#ffaa00;stroke-width:1.5;transform-box:fill-box;transform-origin:center;animation:ring 1.4s ease-out infinite}}
.rh{{fill:none;stroke:#ff2200;stroke-width:2;transform-box:fill-box;transform-origin:center;animation:ring 1.1s ease-out infinite}}
.rh2{{fill:none;stroke:#ff6600;stroke-width:1.5;transform-box:fill-box;transform-origin:center;animation:ring 1.1s ease-out infinite}}
.fl{{fill:#ff4400;animation:flash 0.9s ease-in-out infinite}}
.al{{animation:blink 1.2s ease-in-out infinite}}
@keyframes ring{{0%{{transform:scale(1);opacity:.85}}100%{{transform:scale(2.4);opacity:0}}}}
@keyframes flash{{0%,100%{{opacity:0}}40%{{opacity:.9}}70%{{opacity:.5}}}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.15}}}}
</style>
</defs>''')

    # ── BACKGROUND ──────────────────────────────────────────────────────────
    out.append(f'<rect width="{width}" height="{height}" fill="#080e08" rx="10"/>')
    ground_y = TOP_PAD + rows * STEP + 2
    out.append(f'<rect x="0" y="{ground_y}" width="{width}" height="{BOTTOM_PAD}" fill="#0f1a0f"/>')
    out.append(f'<line x1="0" y1="{ground_y}" x2="{width}" y2="{ground_y}" stroke="#1a3a1a" stroke-width="1" opacity="0.6"/>')

    # ── TITLE ───────────────────────────────────────────────────────────────
    out.append(f'<text x="{width//2}" y="18" text-anchor="middle" fill="#ff2200" font-family="monospace" font-size="12" font-weight="bold" letter-spacing="4" filter="url(#fh)">FRONTLINE - OPERATION LOG</text>')
    out.append(f'<text x="{width//2}" y="34" text-anchor="middle" fill="#3a5a3a" font-family="monospace" font-size="8" letter-spacing="2">{total} OPERATIONS CONFIRMED</text>')
    out.append(f'<rect x="{width-80}" y="6" width="65" height="14" fill="#1a0000" rx="2" stroke="#ff2200" stroke-width="0.5"/>')
    out.append(f'<text x="{width-47}" y="16" text-anchor="middle" fill="#ff2200" font-family="monospace" font-size="7" font-weight="bold" class="al">● ALERT ACTIVE</text>')

    # ── BULLET TRACERS ──────────────────────────────────────────────────────
    tracers = [
        (1, "3s",   "0s",    "ltr", "#ffff44", 35, 1.5),
        (3, "2s",   "0.8s",  "rtl", "#ffcc00", 25, 1.5),
        (5, "2.5s", "1.5s",  "ltr", "#ffffff", 20, 1.0),
        (0, "4s",   "2s",    "rtl", "#ffaa00", 30, 1.0),
    ]
    for row, dur, begin, direction, color, bw, bh in tracers:
        ty = TOP_PAD + row * STEP + CELL // 2
        fx = -bw if direction == "ltr" else width + bw
        tx = width + bw if direction == "ltr" else -bw
        hx = bw if direction == "ltr" else 0
        out.append(f'<g overflow="visible"><rect x="0" y="{ty-bh/2:.1f}" width="{bw}" height="{bh}" fill="{color}" opacity="0.9" rx="1"/><circle cx="{hx}" cy="{ty}" r="{bh+0.5:.1f}" fill="white" opacity="0.95"/><animateTransform attributeName="transform" type="translate" from="{fx} 0" to="{tx} 0" dur="{dur}" repeatCount="indefinite" begin="{begin}"/></g>')

    # ── GRID CELLS ──────────────────────────────────────────────────────────
    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            count = day["contributionCount"]
            row = day["weekday"]
            x = LEFT_PAD + wi * STEP
            y = TOP_PAD + row * STEP
            cx = x + CELL // 2
            cy = y + CELL // 2
            rv = CELL // 2 - 1
            delay = f"{(wi * 0.07 + row * 0.13) % 4:.2f}s"

            out.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="#0a120a" rx="2"/>')

            if count == 0:
                # Quiet — static dark dot, no animation
                out.append(f'<circle cx="{cx}" cy="{cy}" r="{rv-1}" fill="url(#gq)"/>')

            elif count < 4:
                # Medium alert — orange glow + expanding ring (CSS class)
                out.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" fill="url(#gm)" filter="url(#fm)"/>')
                out.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" class="rm" style="animation-delay:{delay}"/>')

            else:
                # Red alert — red glow + flash + two rings
                out.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" fill="url(#gh)" filter="url(#fh)"/>')
                out.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" class="fl" style="animation-delay:{delay}"/>')
                out.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" class="rh" style="animation-delay:{delay}"/>')
                delay2 = f"{(float(delay[:-1])+0.55)%4:.2f}s"
                out.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" class="rh2" style="animation-delay:{delay2}"/>')

    # ── DAY LABELS ──────────────────────────────────────────────────────────
    for i, label in enumerate(day_labels):
        if label:
            ly = TOP_PAD + i * STEP + CELL // 2 + 3
            out.append(f'<text x="{LEFT_PAD-5}" y="{ly}" text-anchor="end" fill="#2a4a2a" font-family="monospace" font-size="7">{label}</text>')

    # ── MONTH LABELS ────────────────────────────────────────────────────────
    last_month = None
    for wi, week in enumerate(weeks):
        if week["contributionDays"]:
            month = datetime.strptime(week["contributionDays"][0]["date"], "%Y-%m-%d").strftime("%b")
            if month != last_month:
                mx = LEFT_PAD + wi * STEP
                out.append(f'<text x="{mx}" y="{TOP_PAD-10}" fill="#2a4a2a" font-family="monospace" font-size="7">{month}</text>')
                last_month = month

    # ── LEGEND ──────────────────────────────────────────────────────────────
    ly = height - 10
    lx = LEFT_PAD
    out.append(f'<circle cx="{lx+4}" cy="{ly-3}" r="3" fill="url(#gq)"/><text x="{lx+10}" y="{ly}" fill="#2a4a2a" font-family="monospace" font-size="7">QUIET</text>')
    out.append(f'<circle cx="{lx+46}" cy="{ly-3}" r="3" fill="url(#gm)" filter="url(#fm)"/><text x="{lx+52}" y="{ly}" fill="#2a4a2a" font-family="monospace" font-size="7">ALERT</text>')
    out.append(f'<circle cx="{lx+90}" cy="{ly-3}" r="3" fill="url(#gh)" filter="url(#fh)"/><text x="{lx+96}" y="{ly}" fill="#2a4a2a" font-family="monospace" font-size="7">RED ALERT</text>')

    out.append('</svg>')
    return '\n'.join(out)

if __name__ == "__main__":
    weeks, total = get_contributions()
    svg = generate_svg(weeks, total)
    with open("battleship.svg", "w") as f:
        f.write(svg)
    print(f"Generated battleship.svg ({len(svg)//1024}KB) — {total} total contributions")
