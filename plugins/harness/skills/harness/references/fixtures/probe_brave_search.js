// §10 Step 2 fixture — pre-install JSON-RPC stdio probe for Brave Search MCP (T1+)
//
// ⚠️ 패키지 출처 검증 (§8-3 안전 룰) — probe도 코드 실행이다:
//   - 본 스크립트는 `@brave/brave-search-mcp-server` (npm scope=brave, github.com/brave/brave-search-mcp-server) Brave 메인테이너 패키지를 spawn
//   - 미trust 변형(`brave-search-mcp`, `mcp-brave-search` 등 이름 spoofing)은 install과 동일 위협 모델 — 사용자 명시 trust 후에만 사용
//
// ⚠️ T1+ 함정 (API 키 필수):
//   - BRAVE_API_KEY env가 없으면 서버 startup 시 fail 가능성 — 일부 MCP는 initialize는 통과시키고 tool call 시 fail (실측 필요)
//   - probe-only 모드: BRAVE_API_KEY를 *dummy* 값으로 set하고 tools/list 응답이 오는지 시도. 응답 오면 ✓ enum 가능 / 즉시 종료면 ✗ 키 필수
//   - 실 호출 시 quota 소진 — Free tier 2,000 queries/month (2026-05 기준, 외부 실행자 키 보유 정책 확인 필수)
//
// 사용법 (외부 실행자, API 키 보유 시점):
//   1. 패키지 출처 검증 ✓ (위 ⚠️ 룰)
//   2. `npm view @brave/brave-search-mcp-server repository` 또는 GitHub 직접 확인
//   3. (선택) BRAVE_API_KEY env set (없이도 enum 가능 여부 측정)
//        Windows PowerShell: `$env:BRAVE_API_KEY="<key>"; node probe_brave_search.js`
//        Bash: `BRAVE_API_KEY=<key> node probe_brave_search.js`
//   4. COUNT=N 라인과 도구 목록을 §3 인벤토리 brave-search 행 enumeration 박제 (17차 docs 박제 8종 매칭 확인)
//
// 17차 docs 박제 예상 enum (실 결과로 확정 필요):
//   - brave_web_search, brave_local_search, brave_video_search, brave_image_search
//   - brave_news_search, brave_summarizer, brave_place_search, brave_llm_context
//   (총 8종, 모두 read-only — default 권고 8종 `allow`, 단 API quota 소진 부수 효과로 T1+에선 `ask` 게이트 권장)
//
// §8-3 재사용 검증 기법 — JSON-RPC stdio 직접 핑. install 없이 도구 카탈로그 enumerate.
// (probe_sqlite.js / probe_filesystem.js / probe_time.js 동일 패턴, target만 brave-search로 교체)

const { spawn } = require("child_process");

// === 환경별 수정 영역 ===
const NPX_PATH = "npx";  // PATH 통과 가정 — Windows에서는 "npx.cmd"로 명시 가능
const PACKAGE_SPEC = process.env.BRAVE_PACKAGE || "@brave/brave-search-mcp-server";
const EXTRA_FLAGS = (process.env.BRAVE_FLAGS || "--transport stdio").split(/\s+/).filter(Boolean);
// =======================

const args = ["-y", PACKAGE_SPEC, ...EXTRA_FLAGS];
console.log(`[probe_brave_search] spawning: ${NPX_PATH} ${args.join(" ")}`);
console.log(`[probe_brave_search] BRAVE_API_KEY ${process.env.BRAVE_API_KEY ? "✓ set" : "⚠️ unset — startup fail 가능"}`);

const child = spawn(NPX_PATH, args, {
  stdio: ["pipe", "pipe", "pipe"],
  shell: true,
  env: { ...process.env },
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
      // ignore non-JSON noise (서버 시작 banner / npx 다운로드 진행 로그 등)
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
    clientInfo: { name: "probe-brave-search", version: "0.0.1" },
  },
});
send({ jsonrpc: "2.0", method: "notifications/initialized", params: {} });
send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });

timeoutHandle = setTimeout(() => {
  console.error("TIMEOUT (60s) — npx가 @brave/brave-search-mcp-server 패키지를 첫 실행 시 다운로드. 네트워크 또는 캐시 확인. BRAVE_API_KEY 미설정 시 서버가 즉시 종료할 수 있음 (stderr 확인).");
  cleanExit(2);
}, 60000);
