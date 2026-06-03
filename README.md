# Visual Novel — Ricecookey

순수 텍스트 스크립트로 동작하는 웹 기반 비주얼 노벨 엔진입니다.
다른 에이전트가 생성한 노벨 텍스트를 **정해진 스크립트 형식**으로 넣으면 바로 플레이할 수 있습니다.

빌드 도구나 의존성이 필요 없습니다. 순수 HTML / CSS / JavaScript로 만들어졌습니다.

---

## 실행 방법

브라우저 보안 정책상 `fetch`로 스크립트를 읽으려면 **로컬 웹 서버**가 필요합니다.
(파일을 더블클릭해 `file://` 로 여는 방식은 동작하지 않습니다.)

```bash
# 프로젝트 루트에서
python3 -m http.server 8000
# 또는
npx serve .
```

그다음 브라우저에서 `http://localhost:8000` 접속.

다른 스크립트로 플레이하려면 URL 파라미터를 사용합니다:

```
http://localhost:8000/?script=story/내스토리.txt
```

---

## 프로젝트 구조

```
VisualNovel_Ricecookey/
├── index.html          # 진입점 (게임 화면 레이아웃)
├── css/
│   └── style.css       # 스타일 (대화박스, 캐릭터, 타이틀 등)
├── js/
│   ├── parser.js       # 텍스트 스크립트 → 명령 배열 변환
│   ├── engine.js       # 런타임 (타이핑/이미지/오디오/세이브/분기)
│   └── main.js         # DOM 연결 · 입력 처리 · 스크립트 로딩
├── story/
│   └── script.txt      # 노벨 스크립트 (← 다른 에이전트가 채우는 부분)
├── assets/
│   ├── bg/             # 배경 이미지 (classroom.jpg 등)
│   ├── char/           # 캐릭터 스프라이트 (리코_smile.png 등)
│   └── audio/          # BGM / 효과음 (bgm_main.mp3 등)
└── README.md
```

이미지·오디오 파일이 없어도 **텍스트만으로 정상 진행**됩니다
(이미지 자리에는 캐릭터 이름 라벨이 표시됩니다).

---

## 스크립트 형식 (다른 에이전트용 가이드)

`story/script.txt` 는 한 줄에 하나의 명령/대사를 적는 단순한 텍스트입니다.

### 기본 규칙

| 쓰는 법 | 의미 |
|---|---|
| `# 텍스트` | 주석 (무시됨) |
| `# title: 제목` | 타이틀 화면 제목 지정 |
| `== 라벨 ==` 또는 `:: 라벨` | 장면 라벨 (분기 점프 대상) |
| `이름: 대사` | 화자가 있는 대사 |
| `콜론 없는 줄` | 내레이션(지문) |
| `* 선택지 -> 라벨` | 선택지 (연속된 `*` 줄이 한 묶음) |
| `-> 라벨` | 해당 라벨로 점프 |

### 연출 명령 (`@`로 시작)

| 명령 | 설명 |
|---|---|
| `@bg 이름` | 배경 변경 (`assets/bg/이름.jpg\|png…` 자동 탐색) |
| `@show 이름 표정 위치` | 캐릭터 표시. 위치 = `left\|center\|right` (생략 가능), 표정 생략 가능 |
| `@hide 이름` | 캐릭터 숨김 (이름 생략 시 전체 숨김) |
| `@music 이름` | BGM 재생 (`@music stop` = 정지) |
| `@sound 이름` | 효과음 1회 재생 |
| `@wait 0.5` | 지정 초만큼 대기 |
| `@clear` | 배경·캐릭터 모두 지움 |
| `@end` | 스토리 종료 |

> 자산 파일 이름은 확장자를 생략할 수 있습니다. 엔진이 png/jpg/webp, mp3/ogg/wav 등을 자동으로 시도합니다.
> 캐릭터 표정 스프라이트는 `이름_표정` 규칙으로 찾습니다 (예: `@show 리코 smile` → `assets/char/리코_smile.png`).

### 예시

```
# title: 어느 오후

== start ==
@bg classroom
@music bgm_main

방과 후의 교실. 노을이 길게 드리운다.

@show 리코 smile center
리코: 어, 아직 안 갔네?

* 같이 가자고 한다 -> together
* 먼저 간다 -> alone

== together ==
나: 같이 갈래?
리코: 좋아!
-> end_scene

== alone ==
나: 먼저 갈게.
-> end_scene

== end_scene ==
@hide 리코
@end
```

순수 산문(콜론·명령 없는 일반 문장)만 넣어도 전부 내레이션으로 자연스럽게 재생됩니다.
따라서 다른 에이전트는 최소한 **대사/지문 텍스트만** 생성해도 되고,
연출이 필요하면 위 `@` 명령을 섞어 주면 됩니다.

---

## 에셋 생성 (배경 · 캐릭터 · BGM)

AI 일러스트/음원 도구 없이, 브라우저가 직접 렌더하는 형식으로 에셋을 생성합니다.

```bash
python3 tools/gen_backgrounds.py   # assets/bg/*.svg   (장면 배경, 벡터)
python3 tools/gen_characters.py    # assets/char/*.svg (캐릭터 실루엣 스프라이트)
python3 tools/gen_bgm.py           # assets/audio/*.wav (합성 앰비언트 BGM 루프)
```

- 배경/캐릭터는 그라데이션·조명·실루엣 기반 **스타일라이즈드 SVG**입니다.
- BGM은 표준 라이브러리만으로 합성한 **WAV 루프**(메인/긴장/로맨스 3종)입니다.
- 추후 진짜 일러스트·음원이 생기면 **같은 파일명으로 교체**만 하면 됩니다
  (예: `assets/bg/study.svg` → `assets/bg/study.png`. 엔진이 확장자를 자동 탐색).

편별 배경·BGM·캐릭터 매핑은 `tools/convert_notion.py` 의 `SCENE` 표에서 관리합니다.

---

## 스크립트 검증 (linter)

스토리 텍스트가 형식에 맞는지, 분기가 깨지지 않았는지 검사합니다.

```bash
node tools/validate.js story/script.txt
node tools/validate.js story/*.txt        # 여러 파일 한 번에
```

검사 항목:
- **오류**: 존재하지 않는 라벨로 점프, 중복 라벨, 점프 대상 없는 선택지, 인자 누락(`@bg` 등)
- **경고**: 고립된(도달 불가) 라벨, `@end`/점프 없이 다음 라벨로 흘러넘치는 구간, 대사 없는 스크립트
- **정보**: 라벨 수, 화자 목록, 명령 통계

오류가 있으면 종료 코드 `1` 을 반환하므로 CI에 연동됩니다.
GitHub Actions 배포 워크플로에서도 배포 전에 자동으로 이 검증을 실행하여,
깨진 스크립트는 배포되지 않습니다.

---

## 배포 (GitHub Pages)

`main` 또는 작업 브랜치에 푸시하면 `.github/workflows/deploy-pages.yml` 이
저장소 루트를 그대로 GitHub Pages로 배포합니다 (빌드 불필요).

최초 1회만 저장소 설정이 필요합니다:
**Settings → Pages → Build and deployment → Source 를 "GitHub Actions" 로 변경.**

이후 푸시할 때마다 자동 재배포되며, 배포 URL은 Actions 실행 로그의
`deploy` 잡 또는 **Settings → Pages** 상단에서 확인할 수 있습니다.

---

## 조작

- **클릭 / Space / Enter / →** : 다음으로 진행 (타이핑 중이면 즉시 완성)
- 상단 우측 메뉴: 💾 저장 · 📂 불러오기 · ▶ 자동 진행 · ⏩ 스킵 · 🔊 음소거

세이브 데이터와 설정은 브라우저 `localStorage` 에 저장됩니다.
