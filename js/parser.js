/**
 * parser.js — 텍스트 스크립트를 실행 가능한 명령 배열로 변환합니다.
 *
 * ===== 스크립트 형식 (.txt) =====
 *
 *   # 으로 시작하는 줄은 주석입니다.
 *
 *   라벨(장면)        :  == 라벨이름 ==      또는   :: 라벨이름
 *   배경              :  @bg 파일이름        (assets/bg/파일이름.jpg|png 로 탐색)
 *   캐릭터 표시        :  @show 이름 표정 위치 (위치: left|center|right, 생략 가능)
 *   캐릭터 숨김        :  @hide 이름          (이름 생략 시 전체)
 *   BGM 재생          :  @music 파일이름      (assets/audio/파일이름 / stop = 정지)
 *   효과음            :  @sound 파일이름
 *   대기/연출          :  @wait 0.5           (초 단위)
 *   화면 지우기        :  @clear
 *   스토리 종료        :  @end
 *   다른 라벨로 점프    :  -> 라벨이름
 *
 *   대사              :  이름: 안녕하세요      (": " 앞이 화자)
 *   지문(내레이션)     :  교실은 조용했다.      (콜론 없는 일반 줄)
 *
 *   선택지            :  * 선택지 문구 -> 점프할라벨
 *                       (연속된 * 줄은 하나의 선택지 묶음이 됩니다)
 *
 * 형식을 모르는 순수 산문도 그대로 넣으면 전부 내레이션으로 처리됩니다.
 */

(function (global) {
  "use strict";

  // "이름: 대사" 형태에서 화자를 안전하게 추출. URL(http://) 등 오인 방지용으로
  // 콜론 앞부분이 너무 길거나 공백이 과하면 내레이션으로 간주.
  function splitSpeaker(line) {
    const idx = line.indexOf(":");
    if (idx <= 0) return null;
    const name = line.slice(0, idx).trim();
    const text = line.slice(idx + 1).trim();
    if (!name || name.length > 20 || name.includes("  ")) return null;
    if (!text) return null;
    return { name, text };
  }

  function parse(source) {
    const lines = source.replace(/\r\n/g, "\n").split("\n");
    const commands = [];
    const labels = {}; // 라벨이름 -> commands 인덱스
    let pendingChoices = null;

    function flushChoices() {
      if (pendingChoices && pendingChoices.options.length) {
        commands.push(pendingChoices);
      }
      pendingChoices = null;
    }

    for (let raw of lines) {
      const line = raw.trim();

      // 빈 줄 / 주석
      if (!line || line.startsWith("#")) {
        flushChoices();
        continue;
      }

      // 라벨:  == name ==   또는  :: name
      let labelMatch = line.match(/^==\s*(.+?)\s*==$/) || line.match(/^::\s*(.+)$/);
      if (labelMatch) {
        flushChoices();
        labels[labelMatch[1].trim()] = commands.length;
        continue;
      }

      // 선택지:  * 문구 -> 라벨
      if (line.startsWith("*")) {
        const body = line.slice(1).trim();
        const arrow = body.lastIndexOf("->");
        let label = null, label_text = body;
        if (arrow >= 0) {
          label_text = body.slice(0, arrow).trim();
          label = body.slice(arrow + 2).trim();
        }
        if (!pendingChoices) pendingChoices = { type: "choice", options: [] };
        pendingChoices.options.push({ text: label_text, target: label });
        continue;
      } else {
        flushChoices();
      }

      // 점프:  -> 라벨
      if (line.startsWith("->")) {
        commands.push({ type: "jump", target: line.slice(2).trim() });
        continue;
      }

      // 명령:  @command args
      if (line.startsWith("@")) {
        const sp = line.slice(1).split(/\s+/);
        const cmd = sp[0].toLowerCase();
        const args = sp.slice(1);
        switch (cmd) {
          case "bg":
            commands.push({ type: "bg", name: args[0] || "" });
            break;
          case "show": {
            // @show 이름 [표정] [위치]
            const positions = ["left", "center", "right"];
            let name = args[0] || "";
            let pos = "center", expr = "";
            const rest = args.slice(1);
            for (const a of rest) {
              if (positions.includes(a.toLowerCase())) pos = a.toLowerCase();
              else expr = a;
            }
            commands.push({ type: "show", name, expr, pos });
            break;
          }
          case "hide":
            commands.push({ type: "hide", name: args[0] || "" });
            break;
          case "music":
            commands.push({ type: "music", name: args[0] || "" });
            break;
          case "sound":
          case "sfx":
            commands.push({ type: "sound", name: args[0] || "" });
            break;
          case "wait":
            commands.push({ type: "wait", seconds: parseFloat(args[0]) || 0.5 });
            break;
          case "clear":
            commands.push({ type: "clear" });
            break;
          case "end":
            commands.push({ type: "end" });
            break;
          default:
            // 알 수 없는 명령은 무시(앞으로의 확장 대비)
            console.warn("[parser] 알 수 없는 명령:", cmd);
        }
        continue;
      }

      // 대사 또는 내레이션
      const spk = splitSpeaker(line);
      if (spk) {
        commands.push({ type: "say", speaker: spk.name, text: spk.text });
      } else {
        commands.push({ type: "say", speaker: "", text: line });
      }
    }

    flushChoices();
    commands.push({ type: "end" });
    return { commands, labels };
  }

  global.VNParser = { parse };
})(window);
