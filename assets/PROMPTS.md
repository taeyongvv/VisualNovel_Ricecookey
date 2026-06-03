# GPT 이미지 생성 프롬프트 — 「악녀는 남편 대신 상단을 샀다」

이 문서의 프롬프트로 GPT 이미지(예: ChatGPT의 이미지 생성)를 사용해 배경/캐릭터를 만들고,
아래 **파일명 그대로** 저장해서 업로드해 주세요. 제가 `assets/` 에 넣고 배포에 반영합니다.

## 공통 지침
- **배경**: 가로(landscape) 비율로 생성. 가능하면 16:9, 어려우면 3:2(1536×1024). **인물·글자·워터마크 없이.**
- **캐릭터**: 세로(portrait) 비율(1024×1536). **배경 투명(transparent PNG)**, 한 명만, 정면, 반신~무릎 위. **글자 없이.**
- 전체 아트 디렉션(아래 STYLE)을 각 프롬프트 앞에 붙이면 톤이 통일됩니다.

**STYLE (공통 접두):**
> Romance-fantasy light-novel illustration, semi-realistic anime style, painterly and cinematic lighting, rich elegant colors, European imperial setting with subtle magitech (arcane-machinery) accents, highly detailed, no text, no watermark.

---

## 배경 (assets/bg/)  — 인물 없이, 가로

| 파일명 | 프롬프트 (STYLE + 아래) |
|---|---|
| `dawn_room.png` | A noble lady's bedchamber at dawn, cold pre-spring morning light through tall arched windows, sheer curtains, a writing desk with a wax-sealed contract and a guttering candle, melancholic but resolute mood, empty room, wide 16:9. |
| `study.png` | A grand ducal study / merchant office, dark mahogany shelves of ledgers, an open profit-and-loss ledger on a large desk, warm amber lamplight, magitech brass instruments, serious negotiating atmosphere, empty room, wide 16:9. |
| `salon.png` | An opulent aristocratic salon / high-society ballroom interior, crystal chandeliers, marble columns, rose-gold and violet palette, gossiping-court atmosphere, empty room, wide 16:9. |
| `auction.png` | A grand auction hall, tiered seating in shadow, a spotlighted auction podium, warm gold lighting, tense bidding atmosphere, empty room, wide 16:9. |
| `northroad.png` | A snowy northern supply road at the foot of mountains, a magitech refrigerated carriage faintly visible, pale blue winter light, falling snow, cold vast landscape, wide 16:9. |
| `court.png` | A solemn royal court / treasury tribunal hall, towering stone columns, cold blue moonlight, banners, oppressive imperial authority, empty hall, wide 16:9. |
| `ballroom.png` | A glittering imperial ball, golden chandeliers, grand staircase, warm romantic glow, dancing-hall splendor, empty room, wide 16:9. |
| `banquet.png` | A dim candlelit banquet hall, a long table set with crimson and gold, ominous luxurious mood (a poisoning-plot dinner), deep red shadows, empty room, wide 16:9. |
| `treasury.png` | A royal vault at midnight, an empty open safe, scattered gold light, starlight through a high window, tense heist atmosphere, empty room, wide 16:9. |
| `finale.png` | A palace terrace at sunrise, warm golden dawn light, soft hopeful romantic atmosphere, a new contract on a small table, empty scene, wide 16:9. |

---

## 캐릭터 (assets/char/)  — 투명 배경, 세로, 한 명

### 엘리시아 로웬 (여주, 악녀)
공통 묘사:
> A beautiful villainess noblewoman in her early 20s, long platinum-silver hair, sharp garnet-crimson eyes, pale flawless skin, elegant and calculating aura. Wearing a deep crimson-and-black noble gown with gold embroidery. Visual-novel standing sprite, three-quarter / knee-up body, facing the viewer, centered, **transparent background**, soft cel-shaded anime illustration, even full-body lighting, no text.

| 파일명 | 표정 (위 묘사 + 아래) |
|---|---|
| `elisia.png` | neutral confident expression, faint composed smile, looking straight ahead. |
| `elisia_smile.png` | a warm genuine smile, softer eyes, slightly relaxed posture. |
| `elisia_cold.png` | a cold disdainful expression, raised chin, narrowed eyes, villainess smirk. |

### 칼리안 아스테르 (남주, 북부대공)
공통 묘사:
> A tall, stern, handsome northern grand duke in his late 20s, short black hair, cool steel-blue eyes, strong jaw. Wearing a dark navy military-noble coat with silver trim and epaulettes. Visual-novel standing sprite, three-quarter / knee-up body, facing the viewer, centered, **transparent background**, soft cel-shaded anime illustration, even full-body lighting, no text.

| 파일명 | 표정 (위 묘사 + 아래) |
|---|---|
| `kalian.png` | calm composed expression, reserved and watchful. |
| `kalian_cold.png` | a cold guarded expression, slight frown, arms crossed, intimidating. |

---

## 일관성 팁
- 캐릭터의 여러 표정은 **같은 대화 세션에서 연속 생성**하고 "같은 인물·같은 의상, 표정만 바꿔줘"라고 지시하면 디자인이 잘 유지됩니다.
- 비율이 정확히 16:9가 아니어도 됩니다 — 엔진이 `cover` 로 채웁니다. 다만 너무 정사각형이면 잘림이 커지니 가로/세로 비율을 권장합니다.
- 파일명만 위 표대로 맞춰 주시면(또는 업로드 시 어떤 슬롯인지 알려 주시면) 제가 배치·교체합니다.
