// §10 Step 2 fixture — pre-install JSON-RPC stdio probe for time MCP
//
// ⚠️ 패키지 출처 검증 (§8-3 안전 룰) — probe도 코드 실행이다:
//   - 본 스크립트는 `mcp-server-time` (= github.com/modelcontextprotocol/servers/time, anthropic/MCP 메인테이너) 검증 완료 패키지를 spawn
//   - Python 구현 — uvx 경유 spawn (sqlite/git 동일 패턴)
//
// 사용법:
//   1. 패키지 출처 검증 ✓
//   2. uvx 가용 (`uvx --version`)
//   3. `node probe_time.js`
//   4. COUNT=N + 도구 목록 캡처 → §3 인벤토리 time 행 박제

const { spawn } = require("child_process");

const UVX_PATH = "C:\\Users\\user01\\AppData\\Roaming\\Python\\Python312\\Scripts\\uvx.exe";

const child = spawn(UVX_PATH, ["mcp-server-time"], {
  stdio: ["pipe", "pipe", "pipe"],
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
    clientInfo: { name: "probe-time", version: "0.0.1" },
  },
});
send({ jsonrpc: "2.0", method: "notifications/initialized", params: {} });
send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });

timeoutHandle = setTimeout(() => {
  console.error("TIMEOUT (60s) — uvx가 mcp-server-time 패키지를 첫 실행 시 다운로드. 네트워크 또는 캐시 확인.");
  cleanExit(2);
}, 60000);
