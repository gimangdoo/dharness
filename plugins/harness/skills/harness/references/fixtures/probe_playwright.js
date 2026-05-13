// §10 Step 2 fixture — pre-install JSON-RPC stdio probe for Playwright MCP (T1)
//
// ⚠️ 패키지 출처 검증 (§8-3 안전 룰) — probe도 코드 실행이다:
//   - 본 스크립트는 `@playwright/mcp` (microsoft/playwright-mcp, Microsoft 메인테이너) 패키지를 spawn
//   - 미trust 변형(`playwright-mcp-*`, `mcp-playwright-*` 등 이름 spoofing)은 install과 동일 위협 모델
//
// ⚠️ T1 함정 (사용자 명시 승인 필수):
//   - 첫 실행 시 npx가 패키지 다운로드 + Chromium browser binary 다운로드 (~120MB)
//   - plugin host 본 폴더 세션은 §6 자동 install 금지 정책 적용 — *외부 실행자 권고*
//   - 본 세션에서 실행하려면 사용자가 명시 confirm 후 OS 측 npx 가용 확인
//
// 사용법 (외부 실행자):
//   1. 패키지 출처 검증 ✓ (위 ⚠️ 룰)
//   2. npx + node 가용 확인 (`npx --version`, `node --version`)
//   3. (선택) PLAYWRIGHT_FLAGS 환경변수로 CLI flag 조합 변경 — 도구 enum이 flag별로 달라지는지 측정
//        예: `PLAYWRIGHT_FLAGS="--isolated --caps=vision" node probe_playwright.js`
//   4. `node probe_playwright.js` 실행
//   5. COUNT=N 라인과 도구 목록을 받아 §3 인벤토리 playwright 행 enumeration 박제
//
// 측정 의도 — flag 조합별 도구 풀 차이 (§3 인벤토리 footnote 박제용):
//   - default                     → baseline 도구 풀
//   - --isolated                  → 시크릿 모드 isolation 효과 (도구 추가/제거 없음 가설)
//   - --caps=vision               → screenshot/vision 계열 도구 추가 가설
//   - --browser=firefox           → cross-browser 도구명 동일성 확인
//
// §8-3 재사용 검증 기법 — JSON-RPC stdio 직접 핑. install 없이 도구 카탈로그 enumerate.
// (probe_sqlite.js / probe_filesystem.js / probe_time.js 동일 패턴, target만 playwright로 교체)

const { spawn } = require("child_process");

// === 환경별 수정 영역 ===
const NPX_PATH = "npx";  // PATH 통과 가정 — Windows에서는 "npx.cmd"로 명시 가능
const PLAYWRIGHT_FLAGS = (process.env.PLAYWRIGHT_FLAGS || "--browser chromium --isolated").split(/\s+/).filter(Boolean);
// =======================

const args = ["-y", "@playwright/mcp@latest", ...PLAYWRIGHT_FLAGS];
console.log(`[probe_playwright] spawning: ${NPX_PATH} ${args.join(" ")}`);

const child = spawn(NPX_PATH, args, {
  stdio: ["pipe", "pipe", "pipe"],
  shell: true,  // Windows에서 npx.cmd 해석을 위해 필요
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
        console.log(`FLAGS=${PLAYWRIGHT_FLAGS.join(" ")}`);
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
      // ignore non-JSON noise (서버 시작 banner / Chromium 다운로드 진행 로그 등)
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
    clientInfo: { name: "probe-playwright", version: "0.0.1" },
  },
});
send({ jsonrpc: "2.0", method: "notifications/initialized", params: {} });
send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });

timeoutHandle = setTimeout(() => {
  console.error("TIMEOUT (180s) — playwright MCP는 첫 실행 시 (a) @playwright/mcp 패키지 다운로드 + (b) Chromium browser binary (~120MB) 다운로드 가능. 네트워크/캐시 확인 또는 `npx playwright install chromium` 사전 실행.");
  cleanExit(2);
}, 180000);
