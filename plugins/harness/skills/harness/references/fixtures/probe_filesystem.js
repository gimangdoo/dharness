// §10 Step 2 fixture — pre-install JSON-RPC stdio probe for filesystem MCP
//
// ⚠️ 패키지 출처 검증 (§8-3 안전 룰) — probe도 코드 실행이다:
//   - 본 스크립트는 `@modelcontextprotocol/server-filesystem` (= github.com/modelcontextprotocol/servers/filesystem, anthropic/MCP 메인테이너) 검증 완료 패키지를 spawn
//   - 미trust 패키지(이름 spoofing 변형 포함, 예: `mcp-server-filesystem-*`)는 *probe 자체가 코드 실행*이라 install과 동일 위협 모델
//
// 사용법:
//   1. 패키지 출처 검증 ✓ (위 ⚠️ 룰)
//   2. npx 가용 확인 (`which npx`)
//   3. 아래 ALLOWED_DIR을 환경에 맞게 수정 (probe-only면 임의 존재 디렉토리 가능)
//   4. `node probe_filesystem.js` 실행
//   5. COUNT=N 라인과 도구 목록을 받아 §3 인벤토리 filesystem 행 enumeration 박제
//
// §8-3 재사용 검증 기법 — JSON-RPC stdio 직접 핑. install 없이 도구 카탈로그 enumerate.
// (probe_sqlite.js / mcp_probe_git.js 동일 패턴, target만 filesystem으로 교체, runtime uvx→npx)

const { spawn } = require("child_process");

// === 환경별 수정 영역 ===
const NPX_PATH = "npx";  // PATH 통과 가정 — Windows에서는 "npx.cmd"로 명시 가능
const ALLOWED_DIR = "C:\\Users\\user01\\dharness-probe-test\\data";  // 존재하는 bounded 디렉토리 (probe-only 용도)
// =======================

const child = spawn(NPX_PATH, ["-y", "@modelcontextprotocol/server-filesystem", ALLOWED_DIR], {
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
      // ignore non-JSON noise (서버 시작 banner 등)
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
    clientInfo: { name: "probe-filesystem", version: "0.0.1" },
  },
});
send({ jsonrpc: "2.0", method: "notifications/initialized", params: {} });
send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });

timeoutHandle = setTimeout(() => {
  console.error("TIMEOUT (60s) — npx가 @modelcontextprotocol/server-filesystem 패키지를 첫 실행 시 다운로드. 네트워크 또는 캐시 확인.");
  cleanExit(2);
}, 60000);
