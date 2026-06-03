#!/usr/bin/env python3
"""
convert_notion.py — 노션에서 가져온 폴리싱본 소설을 VN 스크립트로 변환.

입력: story/source/polished_raw.md  (## 폴리싱 NN편 + 본문 문단)
출력: story/script.txt               (VN 엔진 스크립트 형식)

변환 규칙
  - 각 편 → 라벨(== chNN ==), 순차 진행, 마지막 편은 @end
  - 지문 문단 → 문장 단위 내레이션
  - 따옴표("..." / “...” / ‘...’) 대사 → 대화 라인
      · 대사 인접 지문에 '엘리시아/로웬' 또는 '칼리안/아스테르'가 명시되면 화자 부여
      · 모호하면 따옴표를 살린 내레이션으로 (오attribution 방지)
"""

import re
import sys
import os

SRC = "story/source/polished_raw.md"
OUT = "story/script.txt"

TITLE = "악녀는 남편 대신 상단을 샀다"
GENRE = "로맨스판타지 · 악녀 · 경영"
SYNOPSIS = (
    "원작 속 엘리시아는 냉혹한 북부대공과 결혼한 뒤 여주를 괴롭히다 처형당하는 악녀였다. "
    "빙의한 그녀는 결혼을 피하기 위해, 남편감을 설득하는 대신 그의 빚더미 보급 상단을 통째로 사버린다."
)

# 화자 사전: 지문에서 이 이름이 보이면 해당 화자로 attribute
HEROINE = ("엘리시아", "로웬")
HERO = ("칼리안", "아스테르")

# 편별 연출: (배경, BGM, 엘리시아 표정, 칼리안 등장 여부)
# 배경/캐릭터/BGM 에셋은 tools/gen_*.py 로 생성됨.
SCENE = {
    1:  ("dawn_room", "bgm_main",    "cold",    False),
    2:  ("study",     "bgm_main",    "neutral", False),
    3:  ("salon",     "bgm_tense",   "cold",    False),
    4:  ("auction",   "bgm_tense",   "neutral", False),
    5:  ("northroad", "bgm_main",    "neutral", False),
    6:  ("study",     "bgm_tense",   "cold",    True),
    7:  ("study",     "bgm_main",    "neutral", False),
    8:  ("court",     "bgm_tense",   "cold",    False),
    9:  ("court",     "bgm_tense",   "cold",    False),
    10: ("salon",     "bgm_tense",   "neutral", False),
    11: ("ballroom",  "bgm_romance", "smile",   True),
    12: ("salon",     "bgm_tense",   "cold",    False),
    13: ("banquet",   "bgm_tense",   "cold",    False),
    14: ("treasury",  "bgm_tense",   "neutral", False),
    15: ("finale",    "bgm_romance", "smile",   True),
}


def scene_commands(num):
    """편 시작 시 배경/BGM/캐릭터 연출 명령 리스트."""
    bg, bgm, expr, hero = SCENE.get(num, ("study", "bgm_main", "neutral", False))
    cmds = ["@hide", f"@bg {bg}", f"@music {bgm}"]
    heroine_expr = "" if expr == "neutral" else f" {expr}"
    if hero:
        cmds.append(f"@show 엘리시아{heroine_expr} left")
        cmds.append("@show 칼리안 cold right")
    else:
        cmds.append(f"@show 엘리시아{heroine_expr} center")
    return cmds

QUOTE_RE = re.compile(r'[“"]([^“”"]+)[”"]|[‘\']([^‘’\']+)[’\']')

# 발화동사 — 이름과 가까이 있을 때만 화자로 인정 (오attribution 방지)
SPEECH_VERB = re.compile(
    r'(말했|말하|말끝|물었|되물|답했|대답|외쳤|외치|중얼|속삭|내뱉|덧붙|'
    r'받아쳤|읊조|권했|되뇌|입을 열|묻는|묻자|읊었|꺼냈|뱉었)'
)


def attribute_speaker(following, preceding):
    """대사 인접 지문에서 '이름 + 발화동사' 패턴이 가까울 때만 화자 부여.

    한국어 인용 부속절은 보통 대사 뒤에 온다: "…" 엘리시아가 말했다.
    따라서 발화동사 직전 ~18자 안에 등장하는 이름으로 화자를 정한다.
    """
    for ctx in (following, preceding):
        if not ctx:
            continue
        for m in SPEECH_VERB.finditer(ctx):
            window = ctx[max(0, m.start() - 18):m.start()]
            h = any(n in window for n in HEROINE)
            k = any(n in window for n in HERO)
            if h and not k:
                return "엘리시아"
            if k and not h:
                return "칼리안"
    return None


def split_sentences(text):
    """한국어 지문을 문장 단위로 분할 (마침표/물음표/느낌표 기준)."""
    text = text.strip()
    if not text:
        return []
    # 문장 종결 부호 뒤에서 분리하되 부호는 유지
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def escape_line(s):
    """스크립트 한 줄로 안전하게: 줄바꿈 제거, 양끝 공백 정리."""
    return " ".join(s.split())


def convert_paragraph(para, lines):
    """문단 하나를 say/대사 라인들로 변환해 lines 에 추가."""
    # 대사와 지문이 섞인 문단을 순서대로 토큰화
    pos = 0
    segments = []  # (kind, text)  kind: 'quote' | 'narr'
    for m in QUOTE_RE.finditer(para):
        if m.start() > pos:
            segments.append(("narr", para[pos:m.start()]))
        quote = m.group(1) or m.group(2)
        segments.append(("quote", quote))
        pos = m.end()
    if pos < len(para):
        segments.append(("narr", para[pos:]))

    for i, (kind, text) in enumerate(segments):
        text = text.strip()
        if not text:
            continue
        if kind == "narr":
            for sent in split_sentences(text):
                lines.append(escape_line(sent))
        else:  # quote
            # 대사 뒤 지문(우선) / 앞 지문에서 '이름+발화동사'로 화자 추정
            following = ""
            preceding = ""
            if i + 1 < len(segments) and segments[i + 1][0] == "narr":
                following = segments[i + 1][1][:40]
            if i - 1 >= 0 and segments[i - 1][0] == "narr":
                preceding = segments[i - 1][1][-40:]
            speaker = attribute_speaker(following, preceding)
            if speaker:
                lines.append(f"{speaker}: {escape_line(text)}")
            else:
                # 화자 모호 → 따옴표 살린 내레이션
                lines.append(escape_line(f"“{text}”"))


def main():
    if not os.path.exists(SRC):
        print(f"입력 파일 없음: {SRC}", file=sys.stderr)
        sys.exit(1)

    raw = open(SRC, encoding="utf-8").read()
    # "### 폴리싱 NN편" 헤더로 분할
    chapters = re.split(r'^###\s+폴리싱\s+(\d+)편\s*$', raw, flags=re.M)
    # split 결과: [pre, '01', body1, '02', body2, ...]
    pairs = []
    for i in range(1, len(chapters), 2):
        num = chapters[i]
        body = chapters[i + 1].strip()
        pairs.append((int(num), body))
    pairs.sort()

    out = []
    out.append(f"# title: {TITLE}")
    out.append(f"# 자동 변환: tools/convert_notion.py (원본: 노션 폴리싱본 15편)")
    out.append("")

    # ----- 인트로 -----
    out.append("== intro ==")
    out.append("@bg dawn_room")
    out.append("@music bgm_main")
    out.append("@show 엘리시아 cold center")
    out.append(f"《{TITLE}》")
    out.append(f"장르 — {GENRE}")
    out.append(SYNOPSIS)
    out.append("그리고 남주는 파혼 대신 동업 계약서를 들고 찾아온다.")
    out.append("“부인이 아니라 회장님이라 부르면 됩니까?”")
    out.append("")
    # 편 선택 메뉴
    out.append("* 처음부터 읽기 -> ch01")
    out.append("* 회차 선택 -> select")
    out.append("")

    # ----- 회차 선택 메뉴 -----
    out.append("== select ==")
    out.append("어느 편부터 읽으시겠습니까?")
    for num, _ in pairs:
        out.append(f"* 제{num}편 -> ch{num:02d}")
    out.append("")

    # ----- 본편 -----
    for idx, (num, body) in enumerate(pairs):
        is_last = idx == len(pairs) - 1
        next_label = "ending" if is_last else f"ch{num + 1:02d}"
        out.append(f"== ch{num:02d} ==")
        out.extend(scene_commands(num))
        out.append(f"── 제{num}편 ──")
        # 챕터 전체를 한 번에 토큰화해야 대사와 인접 지문(다른 문단에 있을 수 있음)을
        # 함께 보고 화자를 추정할 수 있다.
        body_joined = re.sub(r'\s+', ' ', body)
        lines = []
        convert_paragraph(body_joined, lines)
        out.extend(lines)
        out.append("")
        # 편 사이 진행 선택
        if is_last:
            out.append("-> ending")
        else:
            out.append(f"* 다음 편으로 → -> {next_label}")
            out.append("* 회차 선택으로 -> select")
        out.append("")

    # ----- 엔딩 -----
    out.append("== ending ==")
    out.append("@bg finale")
    out.append("@music bgm_romance")
    out.append("@show 엘리시아 smile center")
    out.append("── 끝 ──")
    out.append(f"《{TITLE}》 — 폴리싱본 15편 완결.")
    out.append("@end")
    out.append("")

    open(OUT, "w", encoding="utf-8").write("\n".join(out))
    print(f"생성 완료: {OUT}  ({len(pairs)}편, {sum(1 for l in out if l and not l.startswith(('#','==','*','@','->')))} 텍스트 라인)")


if __name__ == "__main__":
    main()
