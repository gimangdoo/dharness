// §10 Step 2 fixture — pre-install JSON-RPC stdio probe for Firecrawl MCP (T2~)
//
// ⚠️ 패키지 출처 검증 (§8-3 안전 룰) — probe도 코드 실행이다:
//   - 본 스크립트는 `firecrawl-mcp` (npm, github.com/mendableai/firecrawl-mcp-server) Mendable AI 메인테이너 패키지를 spawn
//   - 미trust 변형(`mcp-firecrawl`, `@<scope>/firecrawl-mcp` 등 이름 spoofing)은 install과 동일 위협 모델 — 사용자 명시 trust 후에만 사용
//   - 자체호스팅 채널: `FIRECRAWL_API_URL` env로 endpoint 교체 — SaaS 미사용 케이스
//
// ⚠️ T2~ 함정 (유료, quota 소진 risk 큼):
//   - **Tier T2~**: 유료 SaaS — Free tier 500 credits, scrape=1/url, crawl=대규모(페이지당), batch_scrape=대규모. quota 초과 시 API error
//   - FIRECRAWL_API_KEY 필수 (prefix `fc-`)
//   - default 권고: read 5종 `ask` (T2~로 자동 allow 금지) / batch+crawl `ask` (quota 소진 부수 효과) / `firecrawl_browser_execute` `deny` (임의 코드 실행)
//   - 자체호스팅 시: `-e FIRECRAWL_API_URL=<endpoint>` — quota 소진 risk 사라지지만 *self-hosted endpoint 출처 검증* 필요
//
// 17차 docs 박제:
//   - active 10종 (default):
//     · read 5종: firecrawl_scrape, firecrawl_search, firecrawl_map, firecrawl_extract, firecrawl_check_batch_status
//     · batch/crawl 5종: firecrawl_batch_scrape, firecrawl_crawl, firecrawl_check_crawl_status, firecrawl_agent, firecrawl_agent_status
//   - deprecated 4종 (브라우저 도구 — 사용 권고 X):
//     · firecrawl_browser_create, firecrawl_browser_execute, firecrawl_browser_list, firecrawl_browser_delete
//   - ⚠️ `firecrawl_browser_execute`는 임의 코드 실행 surface — advertise되더라도 frontmatter `tools:` allowlist에서 명시 제외 + `permissions.deny` 박제
//
// 사용법 (외부 실행자, API 키 보유 시점):
//   1. 패키지 출처 검증 ✓ (위 ⚠️ 룰)
//   2. `npm view firecrawl-mcp repository` 또는 GitHub 직접 확인
//   3. FIRECRAWL_API_KEY env set (prefix `fc-` 확인)
//        Windows PowerShell: `$env:FIRECRAWL_API_KEY="fc-<key>"; node probe_firecrawl.js`
//        Bash: `FIRECRAWL_API_KEY=fc-<key> node probe_firecrawl.js`
//   4. (선택) 자체호스팅: `$env:FIRECRAWL_API_URL="<endpoint>"`
//   5. COUNT=N + 도구 목록 → §3 인벤토리 firecrawl 행 enumeration 박제 (active 10 / deprecated 4 advertise 여부 확인)
//   6. ⚠️ 본 probe는 tools/list만 호출하므로 *quota 소비 0* — 실 호출은 frontmatter allowlist에 적은 후에만 발생

const { spawn } = require("child_process");

// === 환경별 수정 영역 ===
const NPX_PATH = "npx";
const PACKAGE_SPEC = process.env.FIRECRAWL_PACKAGE || "firecrawl-mcp";
// =======================

const args = ["-y", PACKAGE_SPEC];
console.log(`[probe_firecrawl] spawning: ${NPX_PATH} ${args.join(" ")}`);
console.log(`[probe_firecrawl] FIRECRAWL_API_KEY ${process.env.FIRECRAWL_API_KEY ? "✓ set" : "⚠️ unset — startup fail 가능"}`);
console.log(`[probe_firecrawl] FIRECRAWL_API_URL ${process.env.FIRECRAWL_API_URL ? "✓ self-hosted: " + process.env.FIRECRAWL_API_URL : "SaaS (default)"}`);

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
        const deprecated = ["firecrawl_browser_create", "firecrawl_browser_execute", "firecrawl_browser_list", "firecrawl_browser_delete"];
        const denyRecommended = ["firecrawl_browser_execute"];
        for (const t of tools) {
          const required = (t.inputSchema && t.inputSchema.required) || [];
          const props = (t.inputSchema && t.inputSchema.properties) || {};
          const allParams = Object.keys(props);
          const tags = [];
          if (deprecated.includes(t.name)) tags.push("⚠️ deprecated");
          if (denyRecommended.includes(t.name)) tags.push("🚫 deny 권고 (임의 코드 실행)");
          const tagStr = tags.length ? "  " + tags.join(" / ") : "";
          console.log(`  - ${t.name}  required=[${required.join(",")}]  all=[${allParams.join(",")}]${tagStr}`);
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
    clientInfo: { name: "probe-firecrawl", version: "0.0.1" },
  },
});
send({ jsonrpc: "2.0", method: "notifications/initialized", params: {} });
send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });

timeoutHandle = setTimeout(() => {
  console.error("TIMEOUT (60s) — npx가 firecrawl-mcp 패키지를 첫 실행 시 다운로드. 네트워크 또는 캐시 확인. FIRECRAWL_API_KEY 미설정 시 서버가 즉시 종료할 수 있음 (stderr 확인).");
  cleanExit(2);
}, 60000);
