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

    # weekday 0=Sun in GitHub API — show Mon at top
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
</defs>''')

    # Background
    lines.append(f'<rect width="{width}" height="{height}" fill="#0d1b2a" rx="10"/>')

    # Title
    lines.append(f'<text x="{width // 2}" y="17" text-anchor="middle" fill="#4fc3f7" font-family="monospace" font-size="11" font-weight="bold" letter-spacing="2">NAVAL COMMAND — CONTRIBUTION GRID</text>')
    lines.append(f'<text x="{width // 2}" y="32" text-anchor="middle" fill="#37474f" font-family="monospace" font-size="9">{total} OPERATIONS LOGGED</text>')

    # Day labels
    for i, label in enumerate(day_labels):
        if label:
            y = TOP_PAD + i * STEP + CELL // 2 + 3
            lines.append(f'<text x="{LEFT_PAD - 5}" y="{y}" text-anchor="end" fill="#37474f" font-family="monospace" font-size="7">{label}</text>')

    # Month labels
    last_month = None
    for week_idx, week in enumerate(weeks):
        if week["contributionDays"]:
            month = datetime.strptime(week["contributionDays"][0]["date"], "%Y-%m-%d").strftime("%b")
            if month != last_month:
                x = LEFT_PAD + week_idx * STEP
                lines.append(f'<text x="{x}" y="{TOP_PAD - 8}" fill="#37474f" font-family="monospace" font-size="7">{month}</text>')
                last_month = month

    # Cells
    for week_idx, week in enumerate(weeks):
        for day in week["contributionDays"]:
            count = day["contributionCount"]
            # GitHub weekday: 0=Sun, 1=Mon ... 6=Sat
            weekday = day["weekday"]
            row = weekday  # keep Sun at top to match GitHub layout

            x = LEFT_PAD + week_idx * STEP
            y = TOP_PAD + row * STEP
            cx = x + CELL // 2
            cy = y + CELL // 2
            r = CELL // 2 - 1

            # Cell background (water)
            lines.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="#0a1628" rx="1"/>')

            if count == 0:
                # Miss — blue peg
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#miss)" opacity="0.7"/>')
                lines.append(f'<circle cx="{cx - 2}" cy="{cy - 2}" r="1.5" fill="white" opacity="0.2"/>')
            elif count < 4:
                # Hit — orange
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#low)"/>')
                lines.append(f'<circle cx="{cx - 2}" cy="{cy - 2}" r="1.5" fill="white" opacity="0.35"/>')
            else:
                # Direct hit — red with glow
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#hit)" filter="url(#glow)"/>')
                lines.append(f'<circle cx="{cx - 2}" cy="{cy - 2}" r="1.5" fill="white" opacity="0.45"/>')
                lines.append(f'<circle cx="{cx}" cy="{cy}" r="{r + 2}" fill="none" stroke="#ff4444" stroke-width="0.5" opacity="0.4"/>')

    # Legend
    legend_y = height - 10
    lx = LEFT_PAD
    lines.append(f'<circle cx="{lx + 4}" cy="{legend_y - 3}" r="3" fill="url(#miss)" opacity="0.7"/>')
    lines.append(f'<text x="{lx + 10}" y="{legend_y}" fill="#37474f" font-family="monospace" font-size="7">MISS</text>')
    lines.append(f'<circle cx="{lx + 42}" cy="{legend_y - 3}" r="3" fill="url(#low)"/>')
    lines.append(f'<text x="{lx + 48}" y="{legend_y}" fill="#37474f" font-family="monospace" font-size="7">HIT</text>')
    lines.append(f'<circle cx="{lx + 74}" cy="{legend_y - 3}" r="3" fill="url(#hit)" filter="url(#glow)"/>')
    lines.append(f'<text x="{lx + 80}" y="{legend_y}" fill="#37474f" font-family="monospace" font-size="7">DIRECT HIT</text>')

    lines.append('</svg>')
    return '\n'.join(lines)

if __name__ == "__main__":
    weeks, total = get_contributions()
    svg = generate_svg(weeks, total)
    with open("battleship.svg", "w") as f:
        f.write(svg)
    print(f"Generated battleship.svg — {total} total contributions")
