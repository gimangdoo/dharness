// §10 Step 2 fixture — pre-install JSON-RPC stdio probe for chrome-devtools MCP (T1)
//
// ✅ 패키지 출처 *확정* (23차 사이클 empirical, 2026-05-11 plugin host 세션 verify):
//   - npm package: `chrome-devtools-mcp` (latest v0.25.0, 2026-05-06; 49 versions since 2025-05-13)
//   - npm Author: **Google LLC** / Maintainers: `mathias` (Mathias Bynens, Chrome DevTools 팀) / `orkon` (Alexei Rudenko, Chrome team) / `google-wombot` (Google 공식 npm 봇)
//   - GitHub: `ChromeDevTools/chrome-devtools-mcp` (39.2k stars / 2.5k forks / Apache-2.0)
//   - mcpName: `io.github.ChromeDevTools/chrome-devtools-mcp` (MCP registry 공식 형식)
//   - bin entries: `chrome-devtools-mcp` (실제 서버) / `chrome-devtools` (alias)
//   - 17차 docs 박제 44 도구 카운트와 GitHub README ✓ 100% 일치
//   - 18차 fixture의 "후보 1 (가장 유력)"이 출처 verify로 ✅ 확정 — spoofing 위험 0
//
// ⚠️ T1 함정 (사용자 명시 승인 필수):
//   - chrome-devtools MCP는 **default가 auto-launch** (GitHub README verify) — playwright와 유사, 17차 박제값과 약간 다름 (17차는 "auto-launch + 9222 attach 두 모드"로 박제)
//   - Remote attach는 명시 flag 필요: `--browser-url=http://127.0.0.1:9222` 또는 `--ws-endpoint=<url>` (+ `--ws-headers` 옵션)
//   - `--autoConnect`는 Chrome 144+ 요구 (release 채널 의존)
//   - auto-launch 모드: Chromium 또는 시스템 Chrome 기동 (다운로드 부수 효과 가능 — puppeteer 24.43.0 devDep 사용)
//   - **engines: node ^20.19 || ^22.12 || >=23** (모든 49 versions 일관 — 0.0.1만 22+, 0.1.0~0.25.0 모두 20.19+; npm view로 23차 사이클 확정)
//
// 🚫 Node engines 함정 (23차 사이클 empirical, 2026-05-11):
//   - 측정 host 세션 환경(Node v18.15.0, 32-bit `C:\Program Files (x86)\nodejs`)에서 본 fixture 직접 spawn 시 **`ERROR: chrome-devtools-mcp does not support Node v18.15.0`**로 즉시 종료
//   - npm WARN EBADENGINE 부수 출력 — npm은 경고만 띄우지만 패키지 자체가 startup에서 engine 체크하여 hard fail
//   - **playwright(22차 통과)와 다른 함정 surface**: playwright는 engines 요구가 더 관대 / chrome-devtools-mcp는 Node 메이저 버전 의존이 추가 차단 layer
//   - probe 실행 전 사용자 측 **Node 20.19+ 가용성 확인 필수** — 옵션: (a) winget `OpenJS.NodeJS.LTS` 시스템 교체 (b) nvm-windows 공존 (c) portable Node zip 1회용 추출. 측정 host 환경에서는 시스템 변경 회피로 본 fixture spawn closure (derived 프로젝트별 §10 진입 시점에 사용자 환경 확인)
//
// 사용법 (외부 실행자):
//   1. ✅ 패키지 출처는 23차 verify로 확정 — 추가 검증 불요
//   2. **권장: 외부 attach 모드 (Chromium 다운로드 회피)**
//      - 측정 대상 Chrome을 미리 launch: `chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\temp\cdp-profile`
//      - `$env:CHROME_DEVTOOLS_FLAGS="--browser-url=http://127.0.0.1:9222"` 후 본 fixture 실행
//   3. 대안: auto-launch 모드 (default — Chromium 다운로드 발생 가능)
//      - `node probe_chrome_devtools.js` 그대로 실행
//   4. COUNT=N 라인과 도구 목록을 받아 §3 인벤토리 chrome-devtools 행 enumeration 박제
//   5. 17차 docs 박제 44종 vs 실 probe diff 확인 (playwright 22차 패턴 — 17차 박제 정정 가능성)
//
// 측정 의도 (§3 인벤토리 footnote 박제용):
//   - 17차 docs 박제 44종 카운트와 실 probe 일치/diff 검증 (playwright 22차에서 17차 정정 2건 발견 선례)
//   - playwright와 도구명 overlap 정도 (e.g. `navigate`/`screenshot`/`evaluate` 등) — code-test profile 내 *대체 채택* 판단
//   - CDP attach (외부 9222) vs auto-launch 모드 차이로 인한 도구 풀 변화 (도구 카운트는 동일 가설, 실 호출 시점에 차이)
//
// §8-3 재사용 검증 기법 — JSON-RPC stdio 직접 핑. install 없이 도구 카탈로그 enumerate.

const { spawn } = require("child_process");

// === 환경별 수정 영역 ===
const NPX_PATH = "npx";
const PACKAGE_SPEC = process.env.CHROME_DEVTOOLS_PACKAGE || "chrome-devtools-mcp@latest";  // ⚠️ 출처 검증 후 갱신
const EXTRA_FLAGS = (process.env.CHROME_DEVTOOLS_FLAGS || "").split(/\s+/).filter(Boolean);
// =======================

const args = ["-y", PACKAGE_SPEC, ...EXTRA_FLAGS];
console.log(`[probe_chrome_devtools] spawning: ${NPX_PATH} ${args.join(" ")}`);

const child = spawn(NPX_PATH, args, {
  stdio: ["pipe", "pipe", "pipe"],
  shell: true,
});

let buf = "";
let timeoutHandle = null;
let exited = false;

const cleanExit = (code) => {
  if (exited) return;
  exited = true;
  if (timeoutHandle) clearTimeout(timeoutHandle);
  try { child.kill(); } catch (_) { /* already dead */ }
  process.exit(code);
};

child.stdout.on("data", (d) => {
  buf += d.toString();
  let idx;
  while ((idx = buf.indexOf("\n")) !== -1) {
    const line = buf.slice(0, idx).trim();
    buf = buf.slice(idx + 1);
    if (!line) continue;
    try {
      const msg = JSON.parse(line);
      if (msg.id === 2) {
        const tools = (msg.result && msg.result.tools) || [];
        console.log(`COUNT=${tools.length}`);
        console.log(`PACKAGE=${PACKAGE_SPEC}`);
        for (const t of tools) {
          const required = (t.inputSchema && t.inputSchema.required) || [];
          const props = (t.inputSchema && t.inputSchema.properties) || {};
          const allParams = Object.keys(props);
          console.log(`  - ${t.name}  required=[${required.join(",")}]  all=[${allParams.join(",")}]`);
        }
        cleanExit(0);
        return;
      }
    } catch (e) {
      // ignore non-JSON noise
    }
  }
});
child.stderr.on("data", (d) => process.stderr.write("[stderr] " + d));

const send = (obj) => child.stdin.write(JSON.stringify(obj) + "\n");

send({
  jsonrpc: "2.0",
  id: 1,
  method: "initialize",
  params: {
    protocolVersion: "2024-11-05",
    capabilities: {},
    clientInfo: { name: "probe-chrome-devtools", version: "0.0.1" },
  },
});
send({ jsonrpc: "2.0", method: "notifications/initialized", params: {} });
send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });

timeoutHandle = setTimeout(() => {
  console.error("TIMEOUT (90s) — chrome-devtools MCP가 (a) 패키지 다운로드 (b) Chrome attach 시도 단계 중 stuck. 패키지명 출처 재확인 또는 `chrome.exe --remote-debugging-port=9222` 사전 launch 후 재시도.");
  cleanExit(2);
}, 90000);
