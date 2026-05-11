// §10 Step 2 fixture — pre-install JSON-RPC stdio probe for memory MCP
//
// ⚠️ 패키지 출처 검증 (§8-3 안전 룰) — probe도 코드 실행이다:
//   - 본 스크립트는 `@modelcontextprotocol/server-memory` (= github.com/modelcontextprotocol/servers/memory, anthropic/MCP 메인테이너) 검증 완료 패키지를 spawn
//   - npm 구현 — npx 경유 (filesystem과 동일 패턴)
//
// 사용법:
//   1. 패키지 출처 검증 ✓
//   2. `node probe_memory.js`
//   3. COUNT=N + 도구 목록 캡처 → §3 인벤토리 memory 행 박제

const { spawn } = require("child_process");

const NPX_PATH = "npx";

const child = spawn(NPX_PATH, ["-y", "@modelcontextprotocol/server-memory"], {
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
    clientInfo: { name: "probe-memory", version: "0.0.1" },
  },
});
send({ jsonrpc: "2.0", method: "notifications/initialized", params: {} });
send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });

timeoutHandle = setTimeout(() => {
  console.error("TIMEOUT (60s) — npx가 @modelcontextprotocol/server-memory 패키지를 첫 실행 시 다운로드. 네트워크 또는 캐시 확인.");
  cleanExit(2);
}, 60000);
