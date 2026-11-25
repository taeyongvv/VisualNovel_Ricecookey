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
  - story/source/direction.json (선택) 이 있으면 우선 적용
      · openings : 편 시작 배경/BGM/표정/칼리안 등장 여부 (SCENE 표를 덮어씀)
      · quotes   : (편, 대사 원문) → 화자·엘리시아 표정. 휴리스틱보다 우선
      · cues     : 앵커 문장 앞에 끼워 넣을 연출 명령 (@bg/@music/@show/@hide)
    칼리안이 등장/퇴장하면 엘리시아 위치(left↔center)는 자동으로 맞춘다.
"""

import re
import sys
import os
import json

SRC = "story/source/polished_raw.md"
DIRECTION = "story/source/direction.json"
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


SENTINEL_RE = re.compile("\x01CUE(\\d+)\x01")


class Stage:
    """편 안의 무대 상태(엘리시아 표정, 칼리안 등장 여부)를 추적하며 연출 명령을 만든다."""

    def __init__(self, opening):
        self.bg = opening["bg"]
        self.music = opening["music"]
        self.expr = opening.get("elisia_expr", "neutral") or "neutral"
        self.kalian = bool(opening.get("kalian_present"))
        self.kalian_expr = "cold"

    def elisia_pos(self):
        return "left" if self.kalian else "center"

    def show_elisia(self):
        e = "" if self.expr == "neutral" else f" {self.expr}"
        return f"@show elisia{e} {self.elisia_pos()}"

    def show_kalian(self):
        e = "" if self.kalian_expr == "neutral" else f" {self.kalian_expr}"
        return f"@show kalian{e} right"

    def opening_cmds(self):
        cmds = ["@hide", f"@bg {self.bg}", f"@music {self.music}", self.show_elisia()]
        if self.kalian:
            cmds.append(self.show_kalian())
        return cmds

    def apply(self, cmd):
        """direction.json 의 명령 하나를 상태에 반영하고, 실제로 낼 명령들을 돌려준다."""
        parts = cmd.split()
        op = parts[0]
        if op == "@show" and len(parts) >= 2:
            who = parts[1]
            rest = parts[2:]
            expr = next((r for r in rest if r not in ("left", "center", "right")), "neutral")
            if who == "elisia":
                self.expr = expr
                return [self.show_elisia()]
            if who == "kalian":
                self.kalian_expr = expr
                was = self.kalian
                self.kalian = True
                out = [self.show_kalian()]
                if not was:  # 칼리안 입장 → 엘리시아 왼쪽으로
                    out.insert(0, self.show_elisia())
                return out
        if op == "@hide" and len(parts) >= 2 and parts[1] == "kalian":
            if not self.kalian:
                return []
            self.kalian = False
            return ["@hide kalian", self.show_elisia()]  # 엘리시아 중앙 복귀
        if op == "@bg":
            if parts[1] == self.bg:
                return []
            self.bg = parts[1]
        if op == "@music":
            if parts[1] == self.music:
                return []
            self.music = parts[1]
        return [cmd]

    def set_expr(self, expr):
        expr = expr or "neutral"
        if expr == self.expr:
            return []
        self.expr = expr
        return [self.show_elisia()]


def insert_cue_sentinels(body, cues, warn):
    """각 cue 의 앵커가 포함된 문장 시작점에 센티널을 끼워 넣는다."""
    marks = []
    search_from = 0
    for i, cue in enumerate(cues):
        anchor = " ".join(cue["anchor"].split())
        idx = body.find(anchor, search_from)
        if idx < 0:
            idx = body.find(anchor)
        if idx < 0:
            warn(f"앵커를 찾지 못함 (ch{cue['chapter']}): {anchor}")
            continue
        # 문장 시작점까지 거슬러 올라감: 종결부호/닫는따옴표 + 공백 뒤
        j = idx
        while j > 0 and not (body[j - 1] == " " and j >= 2 and body[j - 2] in ".!?”\"’'"):
            j -= 1
        marks.append((j, i))
        search_from = idx
    for pos, i in sorted(marks, reverse=True):
        body = body[:pos] + f"\x01CUE{i}\x01" + body[pos:]
    return body


def convert_chapter(body, lines, stage, cues, quotes, warn):
    """챕터 본문을 대사/지문/연출 라인으로 변환해 lines 에 추가."""
    body = insert_cue_sentinels(body, cues, warn)
    used = set()

    def emit_cues(text):
        for m in SENTINEL_RE.finditer(text):
            for cmd in cues[int(m.group(1))]["cmds"]:
                lines.extend(stage.apply(cmd))
        return SENTINEL_RE.sub("", text)

    def lookup(text):
        norm = " ".join(text.split())
        for k, q in enumerate(quotes):
            if k not in used and " ".join(q["text"].split()) == norm:
                used.add(k)
                return q
        return None

    pos = 0
    segments = []  # (kind, text, open_mark)
    for m in QUOTE_RE.finditer(body):
        if m.start() > pos:
            segments.append(("narr", body[pos:m.start()], ""))
        quote = m.group(1) or m.group(2)
        segments.append(("quote", quote, "‘" if m.group(2) else "“"))
        pos = m.end()
    if pos < len(body):
        segments.append(("narr", body[pos:], ""))

    for i, (kind, text, mark) in enumerate(segments):
        if kind == "narr":
            for piece in re.split(r"(\x01CUE\d+\x01)", text):
                if SENTINEL_RE.fullmatch(piece):
                    emit_cues(piece)
                    continue
                for sent in split_sentences(piece):
                    lines.append(escape_line(sent))
            continue
        text = emit_cues(text).strip()
        if not text:
            continue
        q = lookup(text)
        if q is not None:
            speaker = q.get("speaker")
        else:
            following = segments[i + 1][1][:40] if i + 1 < len(segments) and segments[i + 1][0] == "narr" else ""
            preceding = segments[i - 1][1][-40:] if i >= 1 and segments[i - 1][0] == "narr" else ""
            speaker = attribute_speaker(SENTINEL_RE.sub("", following), SENTINEL_RE.sub("", preceding))
        if speaker:
            if speaker == "엘리시아" and q is not None and q.get("expr"):
                lines.extend(stage.set_expr(q["expr"]))
            lines.append(f"{speaker}: {escape_line(text)}")
        else:
            close = "’" if mark == "‘" else "”"
            lines.append(escape_line(f"{mark}{text}{close}"))

    for k, q in enumerate(quotes):
        if k not in used:
            warn(f"direction.json 대사가 본문에 없음 (ch{q['chapter']}): {q['text'][:30]}")


def dedupe_shows(lines):
    """같은 캐릭터를 같은 표정·위치로 다시 @show 하는 중복 명령을 제거."""
    current = {}
    out = []
    for ln in lines:
        if ln == "@hide":
            current = {}
        elif ln.startswith("@hide "):
            current.pop(ln.split()[1], None)
        elif ln.startswith("@show "):
            who = ln.split()[1]
            if current.get(who) == ln:
                continue
            current[who] = ln
        out.append(ln)
    return out


def load_direction():
    if not os.path.exists(DIRECTION):
        return {"openings": {}, "quotes": [], "cues": []}
    d = json.load(open(DIRECTION, encoding="utf-8"))
    d.setdefault("openings", {})
    d.setdefault("quotes", [])
    d.setdefault("cues", [])
    return d


def opening_for(num, direction):
    o = direction["openings"].get(str(num))
    if o:
        return o
    bg, bgm, expr, hero = SCENE.get(num, ("study", "bgm_main", "neutral", False))
    return {"bg": bg, "music": bgm, "elisia_expr": expr, "kalian_present": hero}


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

    direction = load_direction()
    warnings = []

    out = []
    out.append(f"# title: {TITLE}")
    out.append(f"# 자동 변환: tools/convert_notion.py (원본: 노션 폴리싱본 15편)")
    out.append("")

    # ----- 인트로 -----
    out.append("== intro ==")
    out.append("@bg dawn_room")
    out.append("@music bgm_main")
    out.append("@show elisia cold center")
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
        stage = Stage(opening_for(num, direction))
        opening = stage.opening_cmds()
        out.extend(opening)
        out.append(f"── 제{num}편 ──")
        # 챕터 전체를 한 번에 토큰화해야 대사와 인접 지문(다른 문단에 있을 수 있음)을
        # 함께 보고 화자를 추정할 수 있다.
        body_joined = re.sub(r'\s+', ' ', body)
        cues = sorted((c for c in direction["cues"] if c["chapter"] == num), key=lambda c: c.get("line", 0))
        quotes = [q for q in direction["quotes"] if q["chapter"] == num]
        lines = []
        convert_chapter(body_joined, lines, stage, cues, quotes, warnings.append)
        # 편 시작 명령은 이미 냈으므로, 그것을 기준 상태로 삼아 본문 중복만 제거
        out.extend(dedupe_shows(opening + lines)[len(opening):])
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
    out.append("@show elisia smile center")
    out.append("── 끝 ──")
    out.append(f"《{TITLE}》 — 폴리싱본 15편 완결.")
    out.append("@end")
    out.append("")

    open(OUT, "w", encoding="utf-8").write("\n".join(out))
    for w in warnings:
        print("경고:", w, file=sys.stderr)
    print(f"생성 완료: {OUT}  ({len(pairs)}편, {sum(1 for l in out if l and not l.startswith(('#','==','*','@','->')))} 텍스트 라인)")


if __name__ == "__main__":
    main()
