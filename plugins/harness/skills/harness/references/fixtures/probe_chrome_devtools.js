// §10 Step 2 fixture — pre-install JSON-RPC stdio probe for chrome-devtools MCP (T1)
//
// ⚠️ 패키지 출처 *미확정* — 외부 실행자가 trusted source에서 정확한 패키지명·메인테이너 확인 후 PACKAGE_SPEC 갱신:
//   - 후보 1 (가장 유력): `chrome-devtools-mcp` (npm) — github.com/ChromeDevTools/chrome-devtools-mcp (Chrome DevTools 팀 메인테이너) — 본 fixture default
//   - 후보 2 (대안): `@modelcontextprotocol/server-chrome-devtools` (만약 modelcontextprotocol/servers 본가에 포함되어 있다면)
//   - 후보 3 (community): `@<scope>/chrome-mcp` 등 — ⚠️ 이름 spoofing 위험, 메인테이너 직접 확인 필수
//
// ⚠️ T1 함정 (사용자 명시 승인 필수):
//   - chrome-devtools MCP는 *실행 중인 Chrome 인스턴스에 attach* (CDP — Chrome DevTools Protocol over WebSocket)
//   - 첫 실행 시 Chrome 자체 설치는 불요(이미 설치된 Chrome에 9222 포트 등으로 연결) — playwright와 다름
//   - 단 attach 대상 Chrome이 `--remote-debugging-port=9222`로 시작되어 있어야 함 (없으면 spawn 시 자체 launch 시도 가능)
//
// 사용법 (외부 실행자):
//   1. ⚠️ 패키지 출처 검증 (위 ⚠️ 룰) — `npm view <PACKAGE_SPEC> repository` 또는 GitHub 직접 확인
//   2. (선택) 측정 대상 Chrome을 미리 launch: `chrome.exe --remote-debugging-port=9222`
//   3. npx + node 가용 확인
//   4. `node probe_chrome_devtools.js` 실행
//   5. COUNT=N 라인과 도구 목록을 받아 §3 인벤토리 chrome-devtools 행 enumeration 박제
//
// 측정 의도 (§3 인벤토리 footnote 박제용):
//   - playwright와 도구명 overlap 정도 (e.g. `navigate`/`screenshot`/`evaluate` 등) — code-test profile 내 *대체 채택* 판단
//   - CDP attach vs spawn 차이로 인한 stateless/stateful 도구 비율
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
