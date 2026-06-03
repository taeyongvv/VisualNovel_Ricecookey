#!/usr/bin/env python3
"""
gen_characters.py — 캐릭터 스프라이트 SVG 생성 (스타일라이즈드 실루엣 초상).

AI 일러스트가 없으므로, 인물의 분위기를 색/실루엣/표정 포인트로 표현한
반신 실루엣 스프라이트를 만든다. 출력: assets/char/*.svg
파일명 규칙: 이름.svg / 이름_표정.svg  (엔진의 @show 이름 표정 과 매칭)
"""

import os

W, H = 700, 1000
OUT = "assets/char"


def sprite(palette, expr="neutral"):
    """palette: dict(hair, skin, cloth, cloth2, accent, eye)."""
    p = palette
    # 표정에 따른 눈/입 포인트
    mouth = {
        "neutral": f'<path d="M310 300 q40 14 80 0" stroke="{p["eye"]}" stroke-width="6" fill="none"/>',
        "smile":   f'<path d="M305 298 q45 30 90 0" stroke="{p["eye"]}" stroke-width="7" fill="none"/>',
        "cold":    f'<path d="M312 306 h76" stroke="{p["eye"]}" stroke-width="6" fill="none"/>',
        "pout":    f'<path d="M315 312 q35 -16 70 0" stroke="{p["eye"]}" stroke-width="6" fill="none"/>',
    }.get(expr, "")
    brow = {
        "cold": (f'<rect x="296" y="244" width="48" height="7" rx="3" fill="{p["eye"]}" '
                 f'transform="rotate(8 320 247)"/>'
                 f'<rect x="356" y="244" width="48" height="7" rx="3" fill="{p["eye"]}" '
                 f'transform="rotate(-8 380 247)"/>'),
        "smile": (f'<path d="M298 250 q22 -8 46 0" stroke="{p["eye"]}" stroke-width="5" fill="none"/>'
                  f'<path d="M356 250 q22 -8 46 0" stroke="{p["eye"]}" stroke-width="5" fill="none"/>'),
    }.get(expr, "")

    defs = (
        f'<linearGradient id="cloth" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{p["cloth"]}"/>'
        f'<stop offset="1" stop-color="{p["cloth2"]}"/></linearGradient>'
        f'<radialGradient id="rim" cx="350" cy="260" r="320" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0.7" stop-color="transparent"/>'
        f'<stop offset="1" stop-color="{p["accent"]}" stop-opacity="0.5"/></radialGradient>'
    )
    body = (
        # 어깨/상체 의상
        f'<path d="M120 1000 C140 720 230 560 350 560 C470 560 560 720 580 1000 Z" fill="url(#cloth)"/>'
        f'<path d="M350 560 L300 1000 L400 1000 Z" fill="{p["accent"]}" opacity="0.35"/>'
        # 목
        f'<rect x="318" y="470" width="64" height="120" rx="26" fill="{p["skin"]}"/>'
        # 머리 (뒤 머리카락)
        f'<ellipse cx="350" cy="300" rx="180" ry="210" fill="{p["hair"]}"/>'
        # 얼굴
        f'<ellipse cx="350" cy="290" rx="120" ry="150" fill="{p["skin"]}"/>'
        # 앞머리
        f'<path d="M230 250 Q350 120 470 250 Q470 170 350 150 Q230 170 230 250 Z" fill="{p["hair"]}"/>'
        # 눈
        f'<ellipse cx="320" cy="276" rx="13" ry="17" fill="{p["eye"]}"/>'
        f'<ellipse cx="380" cy="276" rx="13" ry="17" fill="{p["eye"]}"/>'
        f'{brow}{mouth}'
        # 림 라이트
        f'<rect width="{W}" height="{H}" fill="url(#rim)"/>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">\n<defs>{defs}</defs>\n{body}\n</svg>\n'
    )


# 엘리시아 — 은발/적안 악녀, 우아하고 냉철
ELISIA = dict(hair="#d8d2e0", skin="#f3dccb", cloth="#5a2740",
              cloth2="#2a1020", accent="#c0344e", eye="#7a1f33")
# 칼리안 — 흑발, 북부대공, 차갑고 단단
KALIAN = dict(hair="#20242e", skin="#e7cdb8", cloth="#1d2c44",
              cloth2="#0c141f", accent="#3f6ea0", eye="#22303f")


def main():
    os.makedirs(OUT, exist_ok=True)
    # 파일명은 영문(romanized)으로 — 일부 호스트/CDN의 한글 파일명 인코딩 이슈 회피.
    # 화면에 표시되는 화자 이름("엘리시아")은 스크립트의 대사 라인에서 별도로 관리됨.
    files = {
        "elisia": sprite(ELISIA, "neutral"),
        "elisia_smile": sprite(ELISIA, "smile"),
        "elisia_cold": sprite(ELISIA, "cold"),
        "kalian": sprite(KALIAN, "neutral"),
        "kalian_cold": sprite(KALIAN, "cold"),
    }
    for name, data in files.items():
        open(os.path.join(OUT, f"{name}.svg"), "w", encoding="utf-8").write(data)
    print(f"캐릭터 {len(files)}개 생성 → {OUT}/")
    for n in files:
        print("  -", n)


if __name__ == "__main__":
    main()
