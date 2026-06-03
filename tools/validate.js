#!/usr/bin/env node
/**
 * validate.js — 노벨 스크립트 검증 도구 (linter)
 *
 * 다른 에이전트가 생성한 스크립트가 형식에 맞는지, 분기가 깨지지 않았는지 검사합니다.
 *
 * 사용법:
 *   node tools/validate.js story/script.txt
 *   node tools/validate.js story/*.txt
 *   node tools/validate.js                 (인자 없으면 story/script.txt 검사)
 *
 * 종료 코드: 오류가 하나라도 있으면 1, 없으면 0 (CI 연동 가능)
 *
 * 검사 항목
 *   [오류]  존재하지 않는 라벨로 점프(-> / 선택지 target)
 *   [오류]  중복된 라벨 정의
 *   [오류]  선택지 항목에 점프 대상(-> 라벨)이 없음
 *   [오류]  @bg / @music 등 인자가 필요한 명령에 인자 누락
 *   [경고]  어디서도 도달할 수 없는(고립된) 라벨
 *   [경고]  @end 도 점프도 없이 끝나 다음 라벨로 흘러넘치는(fall-through) 구간
 *   [경고]  대사/내레이션이 하나도 없는 스크립트
 *   [정보]  화자 목록, 라벨 수, 명령 통계
 */

"use strict";

const fs = require("fs");
const path = require("path");

// 브라우저용 parser.js 를 Node에서 재사용 (window shim)
global.window = {};
require(path.join(__dirname, "..", "js", "parser.js"));
const { parse } = global.window.VNParser;

// ----- 한 파일 검사 -----
function validateFile(file) {
  const errors = [];
  const warnings = [];
  const infos = [];

  let source;
  try {
    source = fs.readFileSync(file, "utf8");
  } catch (e) {
    return { file, errors: [`파일을 읽을 수 없습니다: ${e.message}`], warnings, infos };
  }

  // 라벨 정의 중복 검사 (parse 는 마지막 정의로 덮어쓰므로 원문에서 직접 셈)
  const labelLines = {};
  source.split(/\r?\n/).forEach((raw, i) => {
    const line = raw.trim();
    const m = line.match(/^==\s*(.+?)\s*==$/) || line.match(/^::\s*(.+)$/);
    if (m) {
      const name = m[1].trim();
      (labelLines[name] = labelLines[name] || []).push(i + 1);
    }
  });
  for (const [name, lines] of Object.entries(labelLines)) {
    if (lines.length > 1) {
      errors.push(`라벨 '${name}' 이 중복 정의됨 (줄 ${lines.join(", ")})`);
    }
  }

  const { commands, labels } = parse(source);
  const labelNames = new Set(Object.keys(labels));

  // 점프 대상 유효성 + 도달 가능 라벨 수집
  const reachable = new Set();
  let sayCount = 0;
  const speakers = new Set();
  const cmdStats = {};

  commands.forEach((cmd) => {
    cmdStats[cmd.type] = (cmdStats[cmd.type] || 0) + 1;

    if (cmd.type === "say") {
      sayCount++;
      if (cmd.speaker) speakers.add(cmd.speaker);
    }
    if (cmd.type === "jump") {
      if (!labelNames.has(cmd.target)) {
        errors.push(`점프 대상 라벨 '${cmd.target}' 이 존재하지 않습니다`);
      } else {
        reachable.add(cmd.target);
      }
    }
    if (cmd.type === "bg" && !cmd.name) errors.push("@bg 에 배경 이름이 없습니다");
    if (cmd.type === "music" && !cmd.name) errors.push("@music 에 곡 이름이 없습니다");
    if (cmd.type === "show" && !cmd.name) errors.push("@show 에 캐릭터 이름이 없습니다");

    if (cmd.type === "choice") {
      if (!cmd.options.length) {
        errors.push("선택지 블록에 항목이 없습니다");
      }
      cmd.options.forEach((opt) => {
        if (!opt.target) {
          errors.push(`선택지 '${opt.text}' 에 점프 대상(-> 라벨)이 없습니다`);
        } else if (!labelNames.has(opt.target)) {
          errors.push(`선택지 '${opt.text}' 의 점프 대상 '${opt.target}' 이 존재하지 않습니다`);
        } else {
          reachable.add(opt.target);
        }
      });
    }
  });

  // 고립된 라벨 (start/첫 라벨은 진입점이므로 제외)
  const labelOrder = Object.entries(labels).sort((a, b) => a[1] - b[1]);
  const entryLabel = labelOrder.length ? labelOrder[0][0] : null;
  for (const name of labelNames) {
    if (name === entryLabel) continue;
    if (name === "start") continue;
    if (!reachable.has(name)) {
      warnings.push(`라벨 '${name}' 은 어디서도 점프되지 않습니다 (고립 가능성)`);
    }
  }

  // fall-through 검사: 각 라벨 구간이 jump/end/choice 로 끝나는지 확인
  for (let i = 0; i < labelOrder.length; i++) {
    const [name, startIdx] = labelOrder[i];
    const endIdx = i + 1 < labelOrder.length ? labelOrder[i + 1][1] : commands.length;
    // 구간의 마지막 '실행 흐름' 명령 찾기
    let terminated = false;
    for (let j = endIdx - 1; j >= startIdx; j--) {
      const t = commands[j].type;
      if (t === "jump" || t === "end") { terminated = true; break; }
      if (t === "choice") {
        // 모든 선택지가 점프 대상을 가지면 종결로 간주
        terminated = commands[j].options.every((o) => o.target);
        break;
      }
      if (t === "say") break; // say 로 끝나면 다음 라벨로 흘러감
    }
    const isLast = i === labelOrder.length - 1;
    if (!terminated && !isLast) {
      warnings.push(`라벨 '${name}' 구간이 -> 점프나 @end 없이 끝나 다음 라벨로 이어집니다 (의도된 것인지 확인)`);
    }
  }

  if (sayCount === 0) {
    warnings.push("대사/내레이션이 하나도 없습니다");
  }

  infos.push(`라벨 ${labelNames.size}개, 대사/지문 ${sayCount}줄, 화자 ${speakers.size}명`);
  if (speakers.size) infos.push(`화자: ${[...speakers].join(", ")}`);
  const statStr = Object.entries(cmdStats)
    .filter(([k]) => k !== "say" && k !== "end")
    .map(([k, v]) => `${k}:${v}`)
    .join("  ");
  if (statStr) infos.push(`명령: ${statStr}`);

  return { file, errors, warnings, infos };
}

// ----- 출력 -----
const C = {
  red: (s) => `\x1b[31m${s}\x1b[0m`,
  yellow: (s) => `\x1b[33m${s}\x1b[0m`,
  green: (s) => `\x1b[32m${s}\x1b[0m`,
  gray: (s) => `\x1b[90m${s}\x1b[0m`,
  bold: (s) => `\x1b[1m${s}\x1b[0m`,
};

function report(result) {
  console.log("\n" + C.bold(`📄 ${result.file}`));
  result.infos.forEach((m) => console.log("   " + C.gray("ℹ " + m)));
  result.warnings.forEach((m) => console.log("   " + C.yellow("⚠ " + m)));
  result.errors.forEach((m) => console.log("   " + C.red("✖ " + m)));
  if (!result.errors.length && !result.warnings.length) {
    console.log("   " + C.green("✓ 문제 없음"));
  }
}

function main() {
  let files = process.argv.slice(2);
  if (!files.length) files = ["story/script.txt"];

  let totalErrors = 0;
  let totalWarnings = 0;
  for (const f of files) {
    const r = validateFile(f);
    report(r);
    totalErrors += r.errors.length;
    totalWarnings += r.warnings.length;
  }

  console.log("\n" + C.bold("─".repeat(40)));
  const summary = `오류 ${totalErrors} · 경고 ${totalWarnings}`;
  console.log(
    totalErrors ? C.red("결과: " + summary) : C.green("결과: " + summary)
  );
  process.exit(totalErrors ? 1 : 0);
}

main();
