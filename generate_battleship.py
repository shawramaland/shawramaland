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
    TOP_PAD = 48
    RIGHT_PAD = 15
    BOTTOM_PAD = 28

    cols = len(weeks)
    rows = 7

    width = LEFT_PAD + cols * STEP + RIGHT_PAD
    height = TOP_PAD + rows * STEP + BOTTOM_PAD

    day_labels = ['', 'Mon', '', 'Wed', '', 'Fri', '']

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">')

    lines.append('''<defs>
  <radialGradient id="hit" cx="50%" cy="35%" r="60%">
    <stop offset="0%" stop-color="#ff6b6b"/>
    <stop offset="100%" stop-color="#c0392b"/>
  </radialGradient>
  <radialGradient id="miss" cx="40%" cy="35%" r="65%">
    <stop offset="0%" stop-color="#1a6ca8"/>
    <stop offset="100%" stop-color="#0d3d6b"/>
  </radialGradient>
  <radialGradient id="low" cx="50%" cy="35%" r="60%">
    <stop offset="0%" stop-color="#e67e22"/>
    <stop offset="100%" stop-color="#a04000"/>
  </radialGradient>
  <filter id="glow">
    <feGaussianBlur stdDeviation="1.5" result="coloredBlur"/>
    <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="redglow">
    <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
    <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>''')

    # Background
    lines.append(f'<rect width="{width}" height="{height}" fill="#0d1b2a" rx="10"/>')

    # Title
    lines.append(f'<text x="{width // 2}" y="17" text-anchor="middle" fill="#4fc3f7" font-family="monospace" font-size="11" font-weight="bold" letter-spacing="2">NAVAL COMMAND — CONTRIBUTION GRID</text>')
    lines.append(f'<text x="{width // 2}" y="32" text-anchor="middle" fill="#37474f" font-family="monospace" font-size="9">{total} OPERATIONS LOGGED</text>')

    # Cells
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

            delay = f"{(week_idx * 0.07 + row * 0.13) % 3:.2f}s"
            dur = f"{1.5 + (week_idx * 0.03 + row * 0.07) % 1:.2f}s"

            # Cell background
            lines.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="#0a1628" rx="1"/>')

            if count == 0:
                # Miss — blue peg + water ripple
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" fill="url(#miss)" opacity="0.6"/>')
                lines.append(f'<circle cx="{cx - 2}" cy="{cy - 2}" r="1.5" fill="white" opacity="0.2"/>')
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="2" fill="none" stroke="#4fc3f7" stroke-width="0.5">')
                lines.append(f'  <animate attributeName="r" values="2;{rv};2" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="opacity" values="0.3;0;0.3" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'</circle>')

            elif count < 4:
                # Hit — orange peg + expanding ring + smoke
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" fill="url(#low)" filter="url(#glow)"/>')
                lines.append(f'<circle cx="{cx - 2}" cy="{cy - 2}" r="1.5" fill="white" opacity="0.35"/>')
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" fill="none" stroke="#e67e22" stroke-width="2">')
                lines.append(f'  <animate attributeName="r" from="{rv}" to="{rv + 5}" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="opacity" from="0.7" to="0" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="stroke-width" from="2" to="0.5" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'</circle>')
                lines.append(f'<circle cx="{cx}" cy="{cy - rv}" r="2" fill="#777" opacity="0">')
                lines.append(f'  <animate attributeName="cy" from="{cy - rv}" to="{cy - rv - 12}" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="opacity" values="0;0.5;0" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="r" from="2" to="4" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'</circle>')

            else:
                # Direct hit — pulsing red + double rings + smoke
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" fill="url(#hit)" filter="url(#redglow)"/>')
                lines.append(f'<circle cx="{cx - 2}" cy="{cy - 2}" r="1.5" fill="white" opacity="0.5"/>')
                # Pulsing core
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" fill="url(#hit)" opacity="0.4">')
                lines.append(f'  <animate attributeName="r" values="{rv};{rv + 2};{rv}" dur="0.8s" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="opacity" values="0.4;0.9;0.4" dur="0.8s" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'</circle>')
                # Ring 1 — red
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" fill="none" stroke="#ff4444" stroke-width="2.5">')
                lines.append(f'  <animate attributeName="r" from="{rv}" to="{rv + 7}" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="opacity" from="0.9" to="0" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="stroke-width" from="2.5" to="0.5" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'</circle>')
                # Ring 2 — orange, offset
                delay2 = f"{(float(delay[:-1]) + float(dur[:-1]) * 0.4) % 3:.2f}s"
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{rv}" fill="none" stroke="#ff8800" stroke-width="1.5">')
                lines.append(f'  <animate attributeName="r" from="{rv}" to="{rv + 7}" dur="{dur}" repeatCount="indefinite" begin="{delay2}"/>')
                lines.append(f'  <animate attributeName="opacity" from="0.7" to="0" dur="{dur}" repeatCount="indefinite" begin="{delay2}"/>')
                lines.append(f'  <animate attributeName="stroke-width" from="1.5" to="0.3" dur="{dur}" repeatCount="indefinite" begin="{delay2}"/>')
                lines.append(f'</circle>')
                # Smoke
                lines.append(f'<circle cx="{cx}" cy="{cy - rv}" r="2.5" fill="#999" opacity="0">')
                lines.append(f'  <animate attributeName="cy" from="{cy - rv}" to="{cy - rv - 15}" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="opacity" values="0;0.6;0" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'  <animate attributeName="r" from="2.5" to="5" dur="{dur}" repeatCount="indefinite" begin="{delay}"/>')
                lines.append(f'</circle>')

    # Torpedo 1 — left to right, row 2 (drawn OVER cells)
    t1y = TOP_PAD + 2 * STEP + CELL // 2
    lines.append(f'<g>')
    lines.append(f'  <ellipse cx="0" cy="{t1y}" rx="9" ry="3" fill="#c0392b" opacity="0.9"/>')
    lines.append(f'  <ellipse cx="-7" cy="{t1y}" rx="6" ry="2" fill="#e74c3c" opacity="0.55"/>')
    lines.append(f'  <ellipse cx="-14" cy="{t1y}" rx="4" ry="1.5" fill="#ff9999" opacity="0.3"/>')
    lines.append(f'  <animateTransform attributeName="transform" type="translate" from="-30 0" to="{width + 30} 0" dur="9s" repeatCount="indefinite"/>')
    lines.append(f'</g>')

    # Torpedo 2 — right to left, row 5 (drawn OVER cells)
    t2y = TOP_PAD + 5 * STEP + CELL // 2
    lines.append(f'<g>')
    lines.append(f'  <ellipse cx="{width}" cy="{t2y}" rx="9" ry="3" fill="#e67e22" opacity="0.9"/>')
    lines.append(f'  <ellipse cx="{width + 7}" cy="{t2y}" rx="6" ry="2" fill="#f39c12" opacity="0.55"/>')
    lines.append(f'  <ellipse cx="{width + 14}" cy="{t2y}" rx="4" ry="1.5" fill="#ffcc80" opacity="0.3"/>')
    lines.append(f'  <animateTransform attributeName="transform" type="translate" from="30 0" to="{-(width + 30)} 0" dur="12s" repeatCount="indefinite" begin="4s"/>')
    lines.append(f'</g>')

    # Day labels
    for i, label in enumerate(day_labels):
        if label:
            y_lbl = TOP_PAD + i * STEP + CELL // 2 + 3
            lines.append(f'<text x="{LEFT_PAD - 5}" y="{y_lbl}" text-anchor="end" fill="#37474f" font-family="monospace" font-size="7">{label}</text>')

    # Month labels
    last_month = None
    for week_idx, week in enumerate(weeks):
        if week["contributionDays"]:
            month = datetime.strptime(week["contributionDays"][0]["date"], "%Y-%m-%d").strftime("%b")
            if month != last_month:
                mx = LEFT_PAD + week_idx * STEP
                lines.append(f'<text x="{mx}" y="{TOP_PAD - 8}" fill="#37474f" font-family="monospace" font-size="7">{month}</text>')
                last_month = month

    # Legend
    legend_y = height - 10
    lx = LEFT_PAD
    lines.append(f'<circle cx="{lx + 4}" cy="{legend_y - 3}" r="3" fill="url(#miss)" opacity="0.7"/>')
    lines.append(f'<text x="{lx + 10}" y="{legend_y}" fill="#37474f" font-family="monospace" font-size="7">MISS</text>')
    lines.append(f'<circle cx="{lx + 42}" cy="{legend_y - 3}" r="3" fill="url(#low)"/>')
    lines.append(f'<text x="{lx + 48}" y="{legend_y}" fill="#37474f" font-family="monospace" font-size="7">HIT</text>')
    lines.append(f'<circle cx="{lx + 74}" cy="{legend_y - 3}" r="3" fill="url(#hit)" filter="url(#redglow)"/>')
    lines.append(f'<text x="{lx + 80}" y="{legend_y}" fill="#37474f" font-family="monospace" font-size="7">DIRECT HIT</text>')

    lines.append('</svg>')
    return '\n'.join(lines)

if __name__ == "__main__":
    weeks, total = get_contributions()
    svg = generate_svg(weeks, total)
    with open("battleship.svg", "w") as f:
        f.write(svg)
    print(f"Generated battleship.svg — {total} total contributions")
