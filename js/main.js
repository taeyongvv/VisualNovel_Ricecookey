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
      // 타이틀 갱신: 스크립트 첫 줄이 "# title: 제목" 이면 제목으로 사용
      const titleMatch = source.match(/^#\s*title:\s*(.+)$/im);
      if (titleMatch) dom.titleText.textContent = titleMatch[1].trim();
    } catch (e) {
      engine.toast("스크립트 로드 실패: " + e.message + " (로컬 서버로 실행하세요)", 4000);
      console.error(e);
    }
    engine.refreshContinueButton();
    engine.dom.bgm.muted = engine.settings.muted;
    updateMuteButton();
  }

  /* ---------- 입력 처리 ---------- */

  // 대화 박스 클릭 → 진행
  dom.textbox.addEventListener("click", () => engine.proceed());

  // 키보드: 스페이스/엔터/→ 진행, Esc 메뉴
  document.addEventListener("keydown", (e) => {
    if (!dom.titleScreen.classList.contains("hidden")) return;
    if (["Space", "Enter", "ArrowRight"].includes(e.code)) {
      e.preventDefault();
      engine.proceed();
    }
  });

  // 타이틀 버튼
  dom.titleScreen.addEventListener("click", (e) => {
    const action = e.target.dataset.action;
    if (action === "start") engine.start(null);
    else if (action === "continue") engine.loadSave();
  });

  // 상단 메뉴
  dom.menu.addEventListener("click", (e) => {
    const action = e.target.dataset.action;
    if (!action) return;
    switch (action) {
      case "save": engine.save(); break;
      case "load": engine.loadSave(); break;
      case "auto": {
        const on = engine.toggleAuto();
        e.target.classList.toggle("active", on);
        break;
      }
      case "skip": {
        const on = engine.toggleSkip();
        e.target.classList.toggle("active", on);
        break;
      }
      case "mute": {
        engine.toggleMute();
        updateMuteButton();
        break;
      }
    }
  });

  function updateMuteButton() {
    const btn = dom.menu.querySelector('[data-action="mute"]');
    if (btn) {
      btn.textContent = engine.settings.muted ? "🔇" : "🔊";
      btn.classList.toggle("active", engine.settings.muted);
    }
  }

  boot();
})();
