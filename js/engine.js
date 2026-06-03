/**
 * engine.js — 파싱된 명령을 실행하는 비주얼 노벨 런타임.
 *
 * 기능: 타이핑 효과, 배경/캐릭터 표시, BGM/효과음, 선택지/분기,
 *       세이브/로드(localStorage), 자동 진행, 스킵.
 */

(function (global) {
  "use strict";

  const SAVE_KEY = "vn_ricecookey_save";
  const SETTINGS_KEY = "vn_ricecookey_settings";

  // 이미지/오디오 파일 후보 확장자
  // 실제 래스터 아트(png 등)를 우선 사용하고, 없으면 생성된 svg 플레이스홀더로 폴백
  const IMG_EXT = ["png", "webp", "jpg", "jpeg", "gif", "svg"];
  const AUDIO_EXT = ["mp3", "ogg", "wav", "m4a"];

  class Engine {
    constructor(dom) {
      this.dom = dom;
      this.script = { commands: [], labels: {} };
      this.ip = 0;                 // instruction pointer
      this.typing = false;
      this.typeTimer = null;
      this.autoTimer = null;
      this.waitTimer = null;
      this.currentText = "";
      this.shownChars = {};        // 이름 -> element
      this.state = {               // 세이브에 들어가는 진행 상태
        ip: 0,
        bg: "",
        music: "",
        chars: {},                 // 이름 -> {expr, pos}
        lastSpeaker: "",
      };
      this.settings = this.loadSettings();
      this.auto = false;
      this.skip = false;
      this.typeSpeed = 28;         // ms per char
    }

    /* ---------- 스크립트 로드 ---------- */
    load(parsed) {
      this.script = parsed;
    }

    /* ---------- 자산 경로 해석 (확장자 자동 탐색) ---------- */
    resolveAsset(dir, name, exts) {
      // 이미 확장자가 있으면 그대로 사용
      if (/\.[a-z0-9]+$/i.test(name)) return [`${dir}/${name}`];
      return exts.map((e) => `${dir}/${name}.${e}`);
    }

    setBackgroundImage(name) {
      this.state.bg = name;
      const el = this.dom.background;
      if (!name || name === "none") {
        el.style.backgroundImage = "";
        return;
      }
      const candidates = this.resolveAsset("assets/bg", name, IMG_EXT);
      this.tryLoadImage(candidates, (url) => {
        el.style.backgroundImage = `url("${url}")`;
      }, () => {
        // 이미지가 없으면 라벨 표시용 그라데이션
        el.style.backgroundImage = "";
        el.style.backgroundColor = "#1a1f2e";
        this.toast(`배경 '${name}' 이미지 없음 (텍스트로 진행)`, 1200);
      });
    }

    tryLoadImage(candidates, onOk, onFail) {
      let i = 0;
      const next = () => {
        if (i >= candidates.length) { onFail && onFail(); return; }
        const url = candidates[i++];
        const img = new Image();
        img.onload = () => onOk(url);
        img.onerror = next;
        img.src = url;
      };
      next();
    }

    showCharacter(name, expr, pos) {
      this.state.chars[name] = { expr, pos };
      let el = this.shownChars[name];
      if (!el) {
        el = document.createElement("div");
        el.className = "character";
        this.dom.characters.appendChild(el);
        this.shownChars[name] = el;
      }
      el.className = `character shown ${pos || "center"}`;
      const spriteName = expr ? `${name}_${expr}` : name;
      const candidates = this.resolveAsset("assets/char", spriteName, IMG_EXT);
      this.tryLoadImage(candidates, (url) => {
        el.innerHTML = `<img src="${url}" alt="${name}" style="max-height:92vh;" />`;
      }, () => {
        el.innerHTML = `<div class="placeholder">${name}${expr ? " (" + expr + ")" : ""}</div>`;
      });
    }

    hideCharacter(name) {
      if (!name) {
        // 전체 숨김
        Object.values(this.shownChars).forEach((el) => el.remove());
        this.shownChars = {};
        this.state.chars = {};
        return;
      }
      const el = this.shownChars[name];
      if (el) { el.remove(); delete this.shownChars[name]; }
      delete this.state.chars[name];
    }

    /* ---------- 오디오 ---------- */
    playMusic(name) {
      const bgm = this.dom.bgm;
      if (!name || name === "stop" || name === "none") {
        this.state.music = "";
        bgm.pause();
        bgm.removeAttribute("src");
        return;
      }
      // 같은 곡이 이미 재생 중이면 끊지 않고 그대로 이어 간다 (화 전환 시 끊김 방지)
      if (this.state.music === name && bgm.getAttribute("src") && !bgm.paused) {
        return;
      }
      this.state.music = name;
      const candidates = this.resolveAsset("assets/audio", name, AUDIO_EXT);
      this.playAudioCandidates(bgm, candidates, true);
    }

    playSound(name) {
      if (!name) return;
      const sfx = this.dom.sfx;
      const candidates = this.resolveAsset("assets/audio", name, AUDIO_EXT);
      this.playAudioCandidates(sfx, candidates, false);
    }

    playAudioCandidates(audioEl, candidates, isMusic) {
      let i = 0;
      const tryNext = () => {
        if (i >= candidates.length) return; // 조용히 실패 (자산 없음)
        audioEl.src = candidates[i++];
        audioEl.muted = this.settings.muted;
        audioEl.volume = isMusic ? 0.5 : 0.8;
        const p = audioEl.play();
        if (p && p.catch) p.catch(() => { /* 자동재생 차단 등은 무시 */ });
      };
      audioEl.onerror = tryNext;
      tryNext();
    }

    /* ---------- 진행 ---------- */
    start(fromState) {
      this.dom.titleScreen.classList.add("hidden");
      this.dom.textbox.classList.remove("hidden");
      if (fromState) {
        this.restoreState(fromState);
      } else {
        this.ip = 0;
        this.next();
      }
    }

    restoreState(s) {
      this.state = JSON.parse(JSON.stringify(s));
      this.ip = s.ip;
      // 화면 복원
      this.dom.characters.innerHTML = "";
      this.shownChars = {};
      if (s.bg) this.setBackgroundImage(s.bg);
      if (s.music) this.playMusic(s.music);
      for (const [name, c] of Object.entries(s.chars || {})) {
        this.showCharacter(name, c.expr, c.pos);
      }
      this.run(this.ip);
    }

    next() {
      this.clearTimers();
      this.run(this.ip);
    }

    run(index) {
      this.ip = index;
      const cmd = this.script.commands[index];
      if (!cmd) { this.end(); return; }

      switch (cmd.type) {
        case "bg":
          this.setBackgroundImage(cmd.name);
          this.advance();
          break;
        case "show":
          this.showCharacter(cmd.name, cmd.expr, cmd.pos);
          this.advance();
          break;
        case "hide":
          this.hideCharacter(cmd.name);
          this.advance();
          break;
        case "music":
          this.playMusic(cmd.name);
          this.advance();
          break;
        case "sound":
          this.playSound(cmd.name);
          this.advance();
          break;
        case "clear":
          this.hideCharacter("");
          this.setBackgroundImage("");
          this.advance();
          break;
        case "wait":
          if (this.skip) { this.advance(); break; }
          this.waitTimer = setTimeout(() => this.advance(), cmd.seconds * 1000);
          break;
        case "jump":
          this.jumpTo(cmd.target);
          break;
        case "choice":
          this.showChoices(cmd.options);
          break;
        case "say":
          this.say(cmd.speaker, cmd.text);
          break;
        case "end":
          this.end();
          break;
        default:
          this.advance();
      }
    }

    advance() {
      this.run(this.ip + 1);
    }

    jumpTo(label) {
      const target = this.script.labels[label];
      if (target === undefined) {
        this.toast(`라벨 '${label}' 을 찾을 수 없습니다`, 1500);
        this.end();
        return;
      }
      this.run(target);
    }

    /* ---------- 대사 + 타이핑 효과 ---------- */
    say(speaker, text) {
      this.state.lastSpeaker = speaker;
      this.dom.speaker.textContent = speaker || "";
      this.dom.dialogue.textContent = "";
      this.dom.continueHint.classList.remove("show");
      this.currentText = text;

      if (this.skip || this.settings.instant) {
        this.dom.dialogue.textContent = text;
        this.typing = false;
        this.onLineComplete();
        return;
      }

      this.typing = true;
      let i = 0;
      const tick = () => {
        if (i <= text.length) {
          this.dom.dialogue.textContent = text.slice(0, i);
          i++;
          this.typeTimer = setTimeout(tick, this.typeSpeed);
        } else {
          this.typing = false;
          this.onLineComplete();
        }
      };
      tick();
    }

    onLineComplete() {
      this.dom.continueHint.classList.add("show");
      if (this.auto && !this.skip) {
        const dwell = Math.min(2500, 800 + this.currentText.length * 45);
        this.autoTimer = setTimeout(() => this.proceed(), dwell);
      } else if (this.skip) {
        this.autoTimer = setTimeout(() => this.proceed(), 30);
      }
    }

    // 클릭/스페이스 등으로 진행
    proceed() {
      // 선택지가 떠 있으면 무시
      if (!this.dom.choices.classList.contains("hidden")) return;

      if (this.typing) {
        // 타이핑 중이면 즉시 완성
        clearTimeout(this.typeTimer);
        this.typing = false;
        this.dom.dialogue.textContent = this.currentText;
        this.onLineComplete();
        return;
      }
      this.clearTimers();
      this.run(this.ip + 1);
    }

    /* ---------- 선택지 ---------- */
    showChoices(options) {
      const box = this.dom.choices;
      box.innerHTML = "";
      box.classList.remove("hidden");
      this.dom.continueHint.classList.remove("show");
      options.forEach((opt) => {
        const btn = document.createElement("button");
        btn.textContent = opt.text;
        btn.onclick = () => {
          box.classList.add("hidden");
          box.innerHTML = "";
          if (opt.target) this.jumpTo(opt.target);
          else this.run(this.ip + 1);
        };
        box.appendChild(btn);
      });
    }

    /* ---------- 종료 ---------- */
    end() {
      this.clearTimers();
      this.dom.speaker.textContent = "";
      this.dom.dialogue.textContent = "— 끝 —";
      this.dom.continueHint.classList.remove("show");
      this.toast("이야기가 끝났습니다", 2000);
      setTimeout(() => {
        this.dom.titleScreen.classList.remove("hidden");
        this.refreshContinueButton();
      }, 1500);
    }

    /* ---------- 세이브 / 로드 ---------- */
    save() {
      this.state.ip = this.ip;
      try {
        localStorage.setItem(SAVE_KEY, JSON.stringify(this.state));
        this.toast("저장되었습니다", 1000);
      } catch (e) {
        this.toast("저장 실패: " + e.message, 1500);
      }
    }

    hasSave() {
      return !!localStorage.getItem(SAVE_KEY);
    }

    loadSave() {
      const raw = localStorage.getItem(SAVE_KEY);
      if (!raw) { this.toast("저장된 데이터가 없습니다", 1200); return; }
      try {
        const s = JSON.parse(raw);
        this.dom.titleScreen.classList.add("hidden");
        this.dom.textbox.classList.remove("hidden");
        this.restoreState(s);
        this.toast("불러왔습니다", 1000);
      } catch (e) {
        this.toast("불러오기 실패: " + e.message, 1500);
      }
    }

    refreshContinueButton() {
      const btn = this.dom.titleScreen.querySelector('[data-action="continue"]');
      if (btn) btn.disabled = !this.hasSave();
    }

    /* ---------- 설정 ---------- */
    loadSettings() {
      try {
        return Object.assign(
          { muted: false, instant: false },
          JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}")
        );
      } catch { return { muted: false, instant: false }; }
    }
    saveSettings() {
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(this.settings));
    }

    toggleMute() {
      this.settings.muted = !this.settings.muted;
      this.dom.bgm.muted = this.settings.muted;
      this.dom.sfx.muted = this.settings.muted;
      this.saveSettings();
      return this.settings.muted;
    }

    toggleAuto() { this.auto = !this.auto; if (this.auto && !this.typing) this.onLineComplete(); return this.auto; }
    toggleSkip() {
      this.skip = !this.skip;
      if (this.skip) this.proceed();
      return this.skip;
    }

    /* ---------- 유틸 ---------- */
    clearTimers() {
      clearTimeout(this.typeTimer);
      clearTimeout(this.autoTimer);
      clearTimeout(this.waitTimer);
    }

    toast(msg, ms) {
      const t = this.dom.toast;
      t.textContent = msg;
      t.classList.remove("hidden");
      clearTimeout(this._toastTimer);
      this._toastTimer = setTimeout(() => t.classList.add("hidden"), ms || 1200);
    }
  }

  global.VNEngine = Engine;
})(window);
