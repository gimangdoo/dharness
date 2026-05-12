// §11-4 / §10 Step 2 fixture — pre-install JSON-RPC stdio probe for sqlite MCP
//
// ⚠️ 패키지 출처 검증 (§8-3 안전 룰) — probe도 코드 실행이다:
//   - 본 스크립트는 `mcp-server-sqlite` (= github.com/modelcontextprotocol/servers/sqlite, anthropic/MCP 메인테이너) 검증 완료 패키지를 spawn
//   - 다른 MCP로 변형 사용 시: trusted source 확인 후에만 (github.com/modelcontextprotocol/servers / §3 인벤토리 ✓ 항목 / 사용자 명시 trust) probe 실행
//   - 미trust 패키지(이름 spoofing 변형 포함, 예: `mcp-server-sqlite-X`)는 *probe 자체가 코드 실행*이라 install과 동일 위협 모델
//
// 사용법:
//   1. 패키지 출처 검증 ✓ (위 ⚠️ 룰)
//   2. 사용자가 §6 정책에 따라 sqlite MCP install을 명시 승인 (§10 Step 3 user confirm gate 통과)
//   3. uvx 가용 확인 (`uvx --version` — Windows 예: `%APPDATA%\Python\Python312\Scripts\uvx.exe` 절대경로)
//   4. 아래 UVX_PATH / DB_PATH 두 상수를 환경에 맞게 수정
//   5. `node probe_sqlite.js` 실행
//   6. COUNT=N 라인과 도구 목록을 받아 §10 Step 4 install 진행 여부 최종 판단
//      (도구 enumeration이 §3 인벤토리 sqlite 행 갱신용 1차 자료)
//
// §8-3 재사용 검증 기법 — JSON-RPC stdio 직접 핑. install 없이 도구 카탈로그 enumerate.
// (mcp_probe_git.js와 동일 패턴, target만 sqlite로 교체)

const { spawn } = require("child_process");

// === 환경별 수정 영역 ===
const UVX_PATH = "C:\\Users\\user01\\AppData\\Roaming\\Python\\Python312\\Scripts\\uvx.exe";
const DB_PATH = "./data/app.db";  // 실제 SQLite DB 경로로 교체 (시연 시 빈 파일이라도 됨)
// =======================

const child = spawn(UVX_PATH, ["mcp-server-sqlite", "--db-path", DB_PATH], {
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
    clientInfo: { name: "probe-sqlite", version: "0.0.1" },
  },
});
send({ jsonrpc: "2.0", method: "notifications/initialized", params: {} });
send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });

timeoutHandle = setTimeout(() => {
  console.error("TIMEOUT (30s) — uvx가 mcp-server-sqlite 패키지를 첫 실행 시 다운로드. 네트워크 또는 캐시 확인.");
  cleanExit(2);
}, 30000);

// === 예상 도구 enumeration (확인 필요) ===
// - read_query    required=[query]   all=[query]
// - write_query   required=[query]   all=[query]
// - list_tables   required=[]        all=[]
// - describe_table required=[table_name] all=[table_name]
// - append_insight required=[insight] all=[insight]
//
// 실제 결과는 §3 인벤토리 sqlite 행에 채워 본 fixture로 §11-4 Step 2 박제 완료.
