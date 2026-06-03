#!/usr/bin/env python3
"""
gen_backgrounds.py — 장면 배경 SVG를 생성한다 (브라우저가 직접 렌더).

AI 일러스트 도구가 없는 환경이므로, 그라데이션·조명·실루엣으로
각 장면의 분위기를 표현하는 스타일라이즈드 벡터 배경을 만든다.
1920x1080 (16:9). 출력: assets/bg/*.svg
"""

import os

W, H = 1920, 1080
OUT = "assets/bg"


def svg(body, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice">\n'
        f'<defs>{defs}</defs>\n{body}\n</svg>\n'
    )


def vgrad(id_, stops):
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<linearGradient id="{id_}" x1="0" y1="0" x2="0" y2="1">{s}</linearGradient>'


def rgrad(id_, cx, cy, r, stops):
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return (f'<radialGradient id="{id_}" cx="{cx}" cy="{cy}" r="{r}" '
            f'gradientUnits="userSpaceOnUse">{s}</radialGradient>')


def bg_sky(name, sky, glow_xy, glow_color, ground, extra=""):
    """하늘 그라데이션 + 광원 + 바닥 실루엣 공통 템플릿."""
    gx, gy = glow_xy
    defs = (
        vgrad("sky", sky)
        + rgrad("glow", gx, gy, 1100, [(0, glow_color), (1, "transparent")])
        + vgrad("ground", ground)
    )
    body = (
        f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
        f'<rect width="{W}" height="{H}" fill="url(#glow)"/>'
        f'{extra}'
        f'<rect y="{int(H*0.72)}" width="{W}" height="{int(H*0.28)}" fill="url(#ground)"/>'
    )
    return name, svg(body, defs)


def pillars(color, n=6, top=120, bottom=780, op=0.5):
    """기둥(궁전/서재 분위기) 실루엣."""
    out = []
    gap = W / n
    for i in range(n):
        x = i * gap + gap * 0.18
        w = gap * 0.16
        out.append(f'<rect x="{x:.0f}" y="{top}" width="{w:.0f}" height="{bottom-top}" '
                   f'fill="{color}" opacity="{op}"/>')
        out.append(f'<rect x="{x-w*0.4:.0f}" y="{top-24}" width="{w*1.8:.0f}" height="28" '
                   f'fill="{color}" opacity="{op}"/>')
    return "".join(out)


def window_light(x, y, w, h, color="#ffe9b0", op=0.18):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{w*0.45:.0f}" '
            f'fill="{color}" opacity="{op}"/>')


def snow(n=90):
    import random
    random.seed(7)
    out = []
    for _ in range(n):
        x = random.randint(0, W); y = random.randint(0, int(H*0.75))
        r = random.choice([2, 3, 3, 4])
        out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" opacity="0.55"/>')
    return "".join(out)


def stars(n=120):
    import random
    random.seed(3)
    out = []
    for _ in range(n):
        x = random.randint(0, W); y = random.randint(0, int(H*0.6))
        r = random.choice([1, 1, 2])
        out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" opacity="{random.uniform(0.2,0.8):.2f}"/>')
    return "".join(out)


SCENES = []

# 새벽 침실 — 처형장 꿈에서 깨어남, 계약서를 불태우는 새벽
SCENES.append(bg_sky(
    "dawn_room",
    sky=[(0, "#2a2540"), (0.5, "#5b4a63"), (1, "#caa07a")],
    glow_xy=(1500, 320), glow_color="#ffd9a0",
    ground=[(0, "#2c2333"), (1, "#19131f")],
    extra=window_light(1180, 150, 360, 560, "#ffdfa6", 0.22)
          + '<rect x="980" y="150" width="14" height="560" fill="#15101a" opacity="0.6"/>'
          + '<rect x="1360" y="150" width="14" height="560" fill="#15101a" opacity="0.6"/>',
))

# 서재 / 집무실 — 손익계산서, 계약, 회장 직인
SCENES.append(bg_sky(
    "study",
    sky=[(0, "#241c16"), (0.6, "#3a2c20"), (1, "#5a4330")],
    glow_xy=(520, 360), glow_color="#ffcaa0",
    ground=[(0, "#2a1f17"), (1, "#16100b")],
    extra=pillars("#1c1410", n=5, top=80, bottom=820, op=0.55)
          + window_light(360, 140, 300, 420, "#ffd9a0", 0.20),
))

# 사교계 살롱 — 비웃음, 소문
SCENES.append(bg_sky(
    "salon",
    sky=[(0, "#3a2440"), (0.6, "#6a3f63"), (1, "#9c6a82")],
    glow_xy=(960, 300), glow_color="#ffd0e0",
    ground=[(0, "#2e1d33"), (1, "#1a0f1e")],
    extra=pillars("#241327", n=6, top=70, bottom=800, op=0.5)
          + '<circle cx="960" cy="120" r="46" fill="#ffe9b0" opacity="0.5"/>'
          + '<circle cx="620" cy="150" r="30" fill="#ffe9b0" opacity="0.35"/>'
          + '<circle cx="1300" cy="150" r="30" fill="#ffe9b0" opacity="0.35"/>',
))

# 경매장 — 첫 입찰 대결
SCENES.append(bg_sky(
    "auction",
    sky=[(0, "#2b1f1a"), (0.6, "#4a3322"), (1, "#7a5230")],
    glow_xy=(960, 240), glow_color="#ffcf8a",
    ground=[(0, "#34231a"), (1, "#1c120c")],
    extra='<rect x="820" y="560" width="280" height="180" fill="#1a110b" opacity="0.7"/>'
          + window_light(700, 120, 520, 300, "#ffdca0", 0.16),
))

# 북부 설원 보급로 — 마도 냉장 마차
SCENES.append(bg_sky(
    "northroad",
    sky=[(0, "#1d2b3a"), (0.55, "#3f5a72"), (1, "#9fb6c6")],
    glow_xy=(1450, 240), glow_color="#dfeefc",
    ground=[(0, "#cfdae6"), (1, "#aebccb")],
    extra='<polygon points="0,780 520,420 1040,780" fill="#8aa0b4" opacity="0.6"/>'
          '<polygon points="760,780 1280,360 1920,780" fill="#7891a8" opacity="0.6"/>'
          + snow(),
))

# 왕실 법정 / 재무관 — 거래를 불법으로 몰다, 압수
SCENES.append(bg_sky(
    "court",
    sky=[(0, "#201d2e"), (0.6, "#363052"), (1, "#534a78")],
    glow_xy=(960, 200), glow_color="#bcd0ff",
    ground=[(0, "#1c1830"), (1, "#0f0c1c")],
    extra=pillars("#15122a", n=7, top=60, bottom=820, op=0.6)
          + '<polygon points="760,60 960,-40 1160,60" fill="#15122a" opacity="0.6"/>',
))

# 공개 무도회 — 전장 보급 계약, 칼리안
SCENES.append(bg_sky(
    "ballroom",
    sky=[(0, "#241a3a"), (0.55, "#4a3a72"), (1, "#7e6aa8")],
    glow_xy=(960, 260), glow_color="#ffe3b0",
    ground=[(0, "#241836"), (1, "#140d22")],
    extra=pillars("#1a1230", n=6, top=70, bottom=800, op=0.45)
          + '<g opacity="0.7">'
          + "".join(f'<circle cx="{x}" cy="120" r="{r}" fill="#ffe9b0"/>'
                    for x, r in [(960,40),(700,26),(1220,26),(480,18),(1440,18)])
          + '</g>',
))

# 만찬 / 독살 사건 — 범인을 역으로 초대
SCENES.append(bg_sky(
    "banquet",
    sky=[(0, "#2a1414"), (0.6, "#48201f"), (1, "#6e2f2b")],
    glow_xy=(960, 300), glow_color="#ff9a7a",
    ground=[(0, "#2a1110"), (1, "#170808")],
    extra='<rect x="560" y="640" width="800" height="120" fill="#1c0c0b" opacity="0.7"/>'
          + "".join(f'<circle cx="{x}" cy="610" r="8" fill="#ffce7a" opacity="0.9"/>'
                    for x in range(640, 1300, 90)),
))

# 왕실 금고 / 전쟁자금 비는 밤
SCENES.append(bg_sky(
    "treasury",
    sky=[(0, "#11131f"), (0.6, "#1c2236"), (1, "#2c3654")],
    glow_xy=(960, 760), glow_color="#ffd98a",
    ground=[(0, "#0e1018"), (1, "#05060a")],
    extra=stars()
          + '<rect x="820" y="540" width="280" height="240" rx="10" fill="#0c0e16" '
            'stroke="#caa55a" stroke-width="4" opacity="0.85"/>'
          + '<circle cx="960" cy="660" r="34" fill="none" stroke="#caa55a" stroke-width="6" opacity="0.8"/>',
))

# 피날레 — 새 계약서 첫 줄, 새벽빛
SCENES.append(bg_sky(
    "finale",
    sky=[(0, "#2a2348"), (0.5, "#6a5a8a"), (1, "#f0c89a")],
    glow_xy=(960, 360), glow_color="#ffe6c0",
    ground=[(0, "#2a2238"), (1, "#181225")],
    extra='<circle cx="960" cy="360" r="160" fill="#fff3da" opacity="0.5"/>',
))


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, data in SCENES:
        path = os.path.join(OUT, f"{name}.svg")
        open(path, "w", encoding="utf-8").write(data)
    print(f"배경 {len(SCENES)}개 생성 → {OUT}/")
    for name, _ in SCENES:
        print("  -", name)


if __name__ == "__main__":
    main()
