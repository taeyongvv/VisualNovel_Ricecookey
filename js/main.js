/**
 * main.js — DOM 연결, 입력 처리, 스크립트 로딩 부트스트랩.
 */

(function () {
  "use strict";

  const dom = {
    background: document.getElementById("background"),
    characters: document.getElementById("characters"),
    textbox: document.getElementById("textbox"),
    speaker: document.getElementById("speaker"),
    dialogue: document.getElementById("dialogue"),
    continueHint: document.getElementById("continue-hint"),
    choices: document.getElementById("choices"),
    menu: document.getElementById("menu"),
    titleScreen: document.getElementById("title-screen"),
    titleText: document.getElementById("title-text"),
    titleSub: document.getElementById("title-sub"),
    titleArt: document.getElementById("title-art"),
    toast: document.getElementById("toast"),
    bgm: document.getElementById("bgm"),
    sfx: document.getElementById("sfx"),
  };

  const engine = new VNEngine(dom);

  // 스크립트 파일 경로 — URL 파라미터 ?script=story/다른파일.txt 로 교체 가능
  const params = new URLSearchParams(location.search);
  const scriptPath = params.get("script") || "story/script.txt";

  async function boot() {
    try {
      const res = await fetch(scriptPath, { cache: "no-store" });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const source = await res.text();
      const parsed = VNParser.parse(source);
      engine.load(parsed);
      applyTitleScreen(readHeader(source));
    } catch (e) {
      engine.toast("스크립트 로드 실패: " + e.message + " (로컬 서버로 실행하세요)", 4000);
      console.error(e);
    }
    engine.refreshContinueButton();
    engine.dom.bgm.muted = engine.settings.muted;
    updateMuteButton();
  }

  /**
   * 스크립트 머리말 주석(# key: value)을 읽는다.
   *   # title: 제목            # subtitle: 장르 한 줄
   *   # title_bg: dawn_room    # title_char: elisia cold
   */
  function readHeader(source) {
    const header = {};
    for (const line of source.split(/\r?\n/)) {
      const t = line.trim();
      if (!t) continue;
      const m = t.match(/^#\s*([a-z_]+):\s*(.+)$/i);
      if (m) { header[m[1].toLowerCase()] = m[2].trim(); continue; }
      if (!t.startsWith("#")) break; // 머리말은 첫 명령 전까지만
    }
    return header;
  }

  function applyTitleScreen(h) {
    if (h.title) {
      dom.titleText.textContent = h.title;
      document.title = h.title;
    }
    if (h.subtitle) dom.titleSub.textContent = h.subtitle;
    if (h.title_bg) {
      engine.tryLoadImage(engine.resolveAsset("assets/bg", h.title_bg, ["jpg", "jpeg", "webp", "png", "svg"]),
        (url) => { dom.titleScreen.style.backgroundImage = `url("${url}")`; });
    }
    if (h.title_char) {
      const [name, expr] = h.title_char.split(/\s+/);
      engine.tryLoadImage(engine.spriteCandidates(name, expr),
        (url) => { dom.titleArt.style.backgroundImage = `url("${url}")`; });
    }
  }

  /* ---------- 입력 처리 ---------- */

  // 대화 박스나 그림(배경) 클릭/탭 → 진행
  dom.textbox.addEventListener("click", () => engine.proceed());
  dom.background.addEventListener("click", () => engine.proceed());

  // 키보드: 스페이스/엔터/→ 진행, Esc 메뉴
  document.addEventListener("keydown", (e) => {
    if (!dom.titleScreen.classList.contains("hidden")) return;
    // 버튼(선택지·메뉴)에 포커스가 있으면 Enter/Space 는 그 버튼을 누르게 둔다
    if (e.target.closest && e.target.closest("button") && e.code !== "ArrowRight") return;
    if (["Space", "Enter", "ArrowRight"].includes(e.code)) {
      e.preventDefault();
      engine.proceed();
    }
  });

  // 타이틀 버튼
  dom.titleScreen.addEventListener("click", (e) => {
    const btn = e.target.closest("button");
    if (!btn || btn.disabled) return;
    const action = btn.dataset.action;
    if (action === "start") engine.start(null);
    else if (action === "continue") engine.loadSave();
  });

  // 상단 메뉴
  dom.menu.addEventListener("click", (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;
    const action = btn.dataset.action;
    if (!action) return;
    switch (action) {
      case "save": engine.save(); break;
      case "load": engine.loadSave(); break;
      case "auto": {
        setPressed(btn, engine.toggleAuto());
        break;
      }
      case "skip": {
        setPressed(btn, engine.toggleSkip());
        break;
      }
      case "mute": {
        engine.toggleMute();
        updateMuteButton();
        break;
      }
    }
  });

  function setPressed(btn, on) {
    btn.classList.toggle("active", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
  }

  function updateMuteButton() {
    const btn = dom.menu.querySelector('[data-action="mute"]');
    if (btn) setPressed(btn, engine.settings.muted);
  }

  boot();
})();
