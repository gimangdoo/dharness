// §11-4 / §10 Step 2 fixture — pre-install JSON-RPC stdio probe for sqlite MCP
//
// 사용법:
//   1. 사용자가 §6 정책에 따라 sqlite MCP install을 명시 승인 (§10 Step 3 user confirm gate 통과)
//   2. uvx 가용 확인 (`uvx --version` — dharness에서는 `C:\Users\user01\AppData\Roaming\Python\Python312\Scripts\uvx.exe` 절대경로)
//   3. 아래 UVX_PATH / DB_PATH 두 상수를 환경에 맞게 수정
//   4. `node probe_sqlite.js` 실행
//   5. COUNT=N 라인과 도구 목록을 받아 §10 Step 4 install 진행 여부 최종 판단
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
        child.kill();
        process.exit(0);
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

setTimeout(() => {
  console.error("TIMEOUT (30s) — uvx가 mcp-server-sqlite 패키지를 첫 실행 시 다운로드. 네트워크 또는 캐시 확인.");
  child.kill();
  process.exit(2);
}, 30000);

// === 예상 도구 enumeration (확인 필요) ===
// - read_query    required=[query]   all=[query]
// - write_query   required=[query]   all=[query]
// - list_tables   required=[]        all=[]
// - describe_table required=[table_name] all=[table_name]
// - append_insight required=[insight] all=[insight]
//
// 실제 결과는 §3 인벤토리 sqlite 행에 채워 본 fixture로 §11-4 Step 2 박제 완료.
