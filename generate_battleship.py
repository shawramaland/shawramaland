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

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" overflow="visible">')

    lines.append(f'''<defs>
  <!-- Alert gradients -->
  <radialGradient id="alert-high" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#ff2200"/>
    <stop offset="60%" stop-color="#cc1100"/>
    <stop offset="100%" stop-color="#880000"/>
  </radialGradient>
  <radialGradient id="alert-med" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#ffaa00"/>
    <stop offset="60%" stop-color="#cc7700"/>
    <stop offset="100%" stop-color="#664400"/>
  </radialGradient>
  <radialGradient id="quiet" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="#1a2a1a"/>
    <stop offset="100%" stop-color="#0a120a"/>
  </radialGradient>
  <!-- Glow filters -->
  <filter id="red-glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="2.5" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="orange-glow" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur stdDeviation="1.5" result="blur"/>
    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="smoke-blur">
    <feGaussianBlur stdDeviation="1.5"/>
  </filter>
</defs>''')

    # ── BACKGROUND ──────────────────────────────────────────────────────────────
    # Dark battlefield base
    lines.append(f'<rect width="{width}" height="{height}" fill="#080e08" rx="10"/>')

    # Ground/terrain layer at the bottom of the grid
    ground_y = TOP_PAD + rows * STEP + 2
    lines.append(f'<rect x="0" y="{ground_y}" width="{width}" height="{BOTTOM_PAD}" fill="#0f1a0f" rx="0"/>')

    # Subtle scanlines for gritty feel
    for i in range(0, height, 4):
        lines.append(f'<line x1="0" y1="{i}" x2="{width}" y2="{i}" stroke="#ffffff" stroke-width="0.3" opacity="0.03"/>')

    # Horizon line
    lines.append(f'<line x1="0" y1="{ground_y}" x2="{width}" y2="{ground_y}" stroke="#1a3a1a" stroke-width="1" opacity="0.6"/>')

    # ── TITLE ───────────────────────────────────────────────────────────────────
    lines.append(f'<text x="{width // 2}" y="18" text-anchor="middle" fill="#ff2200" font-family="monospace" font-size="12" font-weight="bold" letter-spacing="4" filter="url(#red-glow)">⚔ FRONTLINE — OPERATION LOG ⚔</text>')
    lines.append(f'<text x="{width // 2}" y="34" text-anchor="middle" fill="#3a5a3a" font-family="monospace" font-size="8" letter-spacing="2">{total} OPERATIONS CONFIRMED</text>')

    # Alert level indicator (flashing)
    lines.append(f'<rect x="{width - 80}" y="6" width="65" height="14" fill="#1a0000" rx="2" stroke="#ff2200" stroke-width="0.5"/>')
    lines.append(f'<text x="{width - 47}" y="16" text-anchor="middle" fill="#ff2200" font-family="monospace" font-size="7" font-weight="bold" letter-spacing="1">')
    lines.append(f'  ● ALERT ACTIVE')
    lines.append(f'  <animate attributeName="opacity" values="1;0.2;1" dur="1.2s" repeatCount="indefinite"/>')
    lines.append(f'</text>')
    lines.append(f'</text>')

    # ── BULLET TRACERS ──────────────────────────────────────────────────────────
    tracer_rows = [1, 3, 5]
    tracer_configs = [
        {"row": 1, "dur": "3s",  "begin": "0s",   "dir": "ltr", "color": "#ffff44", "w": 35, "h": 1.5},
        {"row": 3, "dur": "2s",  "begin": "0.8s",  "dir": "rtl", "color": "#ffcc00", "w": 25, "h": 1.5},
        {"row": 5, "dur": "2.5s","begin": "1.5s",  "dir": "ltr", "color": "#ffffff", "w": 20, "h": 1},
        {"row": 0, "dur": "4s",  "begin": "2s",    "dir": "rtl", "color": "#ffaa00", "w": 30, "h": 1},
        {"row": 6, "dur": "1.8s","begin": "3s",    "dir": "ltr", "color": "#ffff88", "w": 18, "h": 1},
        {"row": 2, "dur": "3.5s","begin": "1s",    "dir": "rtl", "color": "#ffee44", "w": 28, "h": 1.5},
        {"row": 4, "dur": "2.2s","begin": "0.5s",  "dir": "ltr", "color": "#ffffff", "w": 22, "h": 1},
    ]

    for t in tracer_configs:
        ty = TOP_PAD + t["row"] * STEP + CELL // 2
        bw = t["w"]
        if t["dir"] == "ltr":
            from_x, to_x = -bw, width + bw
        else:
            from_x, to_x = width + bw, -bw
        # Tracer body
        lines.append(f'<g overflow="visible">')
        lines.append(f'  <rect x="0" y="{ty - t["h"] / 2:.1f}" width="{bw}" height="{t["h"]}" fill="{t["color"]}" opacity="0.9" rx="1"/>')
        # Bright head
        head_x = bw if t["dir"] == "ltr" else 0
        lines.append(f'  <circle cx="{head_x}" cy="{ty}" r="{t["h"] + 0.5}" fill="white" opacity="0.95"/>')
        # Tail fade
        lines.append(f'  <rect x="0" y="{ty - t["h"] / 2:.1f}" width="{bw * 0.6:.0f}" height="{t["h"]}" fill="{t["color"]}" opacity="0.3" rx="1"/>')
        lines.append(f'  <animateTransform attributeName="transform" type="translate" from="{from_x} 0" to="{to_x} 0" dur="{t["dur"]}" repeatCount="indefinite" begin="{t["begin"]}"/>')
        lines.append(f'</g>')

    # ── GRID CELLS ──────────────────────────────────────────────────────────────
    for week_idx, week in enumerate(weeks):
        for day in week["contributionDays"]:
            count = day["contributionCount"]
            weekday = day["weekday"]
            row = weekday

            x = LEFT_PAD + week_idx * STEP
            y = TOP_PAD + row * STEP
            cx = x + CELL // 2
            cy = y + CELL // 2
            rv = CELL // 2 - 1

            delay = f"{(week_idx * 0.06 + row * 0.11) % 4:.2f}s"
            dur   = f"{1.2 + (week_idx * 0.02 + row * 0.05) % 1:.2f}s"

            # Cell base
            lines.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="#0a120a" rx="2"/>')

            if count == 0:
                # Quiet zone — dark green dot, very subtle pulse
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv - 1}" fill="url(#quiet)"/>')
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv - 2}" fill="none" stroke="#1a2a1a" stroke-width="0.5">')
                lines.append(f'  <animate attributeName="opacity" values="0.3;0.1;0.3" dur="4s" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'</circle>')

            elif count < 4:
                # ALERT — orange/yellow pulsing
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" fill="url(#alert-med)" filter="url(#orange-glow)"/>')
                # Alert ring pulse
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" fill="none" stroke="#ffaa00" stroke-width="1.5">')
                lines.append(f'  <animate attributeName="r" from="{rv}" to="{rv + 4}" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="opacity" from="0.8" to="0" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="stroke-width" from="1.5" to="0.3" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'</circle>')
                # Inner flash
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv - 2}" fill="#ffcc00" opacity="0">')
                lines.append(f'  <animate attributeName="opacity" values="0;0.6;0" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'</circle>')
                # Smoke
                lines.append(f'<circle cx="{cx}" cy="{cy - rv}" r="2" fill="#3a3a3a" opacity="0" filter="url(#smoke-blur)">')
                lines.append(f'  <animate attributeName="cy" from="{cy - rv}" to="{cy - rv - 10}" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="opacity" values="0;0.4;0" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="r" from="2" to="4" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'</circle>')

            else:
                # RED ALERT — full combat, flashing red
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" fill="url(#alert-high)" filter="url(#red-glow)"/>')
                # Flash core
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" fill="#ff4400" opacity="0">')
                lines.append(f'  <animate attributeName="opacity" values="0;0.9;0;0.7;0" dur="0.9s" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'</circle>')
                # Explosion ring 1
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" fill="none" stroke="#ff2200" stroke-width="2">')
                lines.append(f'  <animate attributeName="r" from="{rv}" to="{rv + 7}" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="opacity" from="1" to="0" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="stroke-width" from="2.5" to="0.3" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'</circle>')
                # Explosion ring 2 (offset)
                delay2 = f"{(float(delay[:-1]) + float(dur[:-1]) * 0.5) % 4:.2f}s"
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" fill="none" stroke="#ff6600" stroke-width="1.5">')
                lines.append(f'  <animate attributeName="r" from="{rv}" to="{rv + 7}" dur="{dur}" repeatCount="indefinite" begin="{delay2}"/>')
                lines.append(f'  <animate attributeName="opacity" from="0.8" to="0" dur="{dur}" repeatCount="indefinite" begin="{delay2}"/>')
                lines.append(f'</circle>')
                # Heavy smoke
                for si, (sx_off, sy_off, sr, sdur_off) in enumerate([(0, 0, 2.5, 0), (2, 1, 2, 0.3), (-2, -1, 2, 0.6)]):
                    sd = f"{(float(delay[:-1]) + sdur_off) % 4:.2f}s"
                    lines.append(f'<circle cx="{cx + sx_off}" cy="{cy - rv + sy_off}" r="{sr}" fill="#555" opacity="0" filter="url(#smoke-blur)">')
                    lines.append(f'  <animate attributeName="cy" from="{cy - rv + sy_off}" to="{cy - rv - 18 + sy_off}" dur="{float(dur[:-1]) * 1.2:.2f}s" repeatCount="indefinite" begin="{sd}"/>')
                    lines.append(f'  <animate attributeName="opacity" values="0;0.7;0" dur="{float(dur[:-1]) * 1.2:.2f}s" repeatCount="indefinite" begin="{sd}"/>')
                    lines.append(f'  <animate attributeName="r" from="{sr}" to="{sr + 4}" dur="{float(dur[:-1]) * 1.2:.2f}s" repeatCount="indefinite" begin="{sd}"/>')
                    lines.append(f'</circle>')

    # ── DAY LABELS ──────────────────────────────────────────────────────────────
    for i, label in enumerate(day_labels):
        if label:
            ly = TOP_PAD + i * STEP + CELL // 2 + 3
            lines.append(f'<text x="{LEFT_PAD - 5}" y="{ly}" text-anchor="end" fill="#2a4a2a" font-family="monospace" font-size="7">{label}</text>')

    # ── MONTH LABELS ────────────────────────────────────────────────────────────
    last_month = None
    for week_idx, week in enumerate(weeks):
        if week["contributionDays"]:
            month = datetime.strptime(week["contributionDays"][0]["date"], "%Y-%m-%d").strftime("%b")
            if month != last_month:
                mx = LEFT_PAD + week_idx * STEP
                lines.append(f'<text x="{mx}" y="{TOP_PAD - 10}" fill="#2a4a2a" font-family="monospace" font-size="7">{month}</text>')
                last_month = month

    # ── LEGEND ──────────────────────────────────────────────────────────────────
    legend_y = height - 10
    lx = LEFT_PAD
    lines.append(f'<circle cx="{lx + 4}" cy="{legend_y - 3}" r="3" fill="url(#quiet)"/>')
    lines.append(f'<text x="{lx + 10}" y="{legend_y}" fill="#2a4a2a" font-family="monospace" font-size="7">QUIET</text>')
    lines.append(f'<circle cx="{lx + 46}" cy="{legend_y - 3}" r="3" fill="url(#alert-med)" filter="url(#orange-glow)"/>')
    lines.append(f'<text x="{lx + 52}" y="{legend_y}" fill="#2a4a2a" font-family="monospace" font-size="7">ALERT</text>')
    lines.append(f'<circle cx="{lx + 90}" cy="{legend_y - 3}" r="3" fill="url(#alert-high)" filter="url(#red-glow)"/>')
    lines.append(f'<text x="{lx + 96}" y="{legend_y}" fill="#2a4a2a" font-family="monospace" font-size="7">RED ALERT</text>')

    lines.append('</svg>')
    return '\n'.join(lines)

if __name__ == "__main__":
    weeks, total = get_contributions()
    svg = generate_svg(weeks, total)
    with open("battleship.svg", "w") as f:
        f.write(svg)
    print(f"Generated battleship.svg — {total} total contributions")
