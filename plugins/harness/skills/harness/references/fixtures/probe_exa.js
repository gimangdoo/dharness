// §10 Step 2 fixture — pre-install JSON-RPC stdio probe for Exa MCP (T1+)
//
// ⚠️ 패키지 출처 검증 (§8-3 안전 룰) — probe도 코드 실행이다:
//   - 본 스크립트는 `exa-mcp-server` (npm, github.com/exa-labs/exa-mcp-server) Exa Labs 메인테이너 패키지를 spawn
//   - 미trust 변형(`mcp-exa`, `@<scope>/exa-mcp` 등 이름 spoofing)은 install과 동일 위협 모델 — 사용자 명시 trust 후에만 사용
//   - 대체 채널: remote HTTP endpoint `https://mcp.exa.ai/mcp?exaApiKey=<key>&tools=<csv>` — stdio 미사용, 본 probe 패턴 대상 아님
//
// ⚠️ T1+ 함정 (API 키 필수):
//   - EXA_API_KEY env가 없으면 서버 startup 시 fail 가능성
//   - probe-only 모드: EXA_API_KEY를 *dummy* 값으로 set하고 tools/list 응답이 오는지 시도
//   - Free tier 1,000 search credits/month (2026-05 기준, 외부 실행자 정책 확인)
//   - Neural search = LLM 기반 query expansion, 일반 keyword search보다 credit 소비 다를 수 있음
//
// 17차 docs 박제 — default vs deprecated 분리:
//   - active 3종: web_search_exa, web_fetch_exa, web_search_advanced_exa (opt-in)
//   - deprecated 7종: get_code_context_exa, company_research_exa, crawling_exa, people_search_exa, linkedin_search_exa, deep_researcher_start, deep_researcher_check, deep_search_exa
//   - deprecated 도구는 *사용 권고 X* (서버 측에서 advertise하지만 통합 메인테이너가 차후 제거 가능성)
//   - default 권고: 3종 `allow`, deprecated 7종 `deny` (advertise되더라도 frontmatter `tools:` allowlist에서 명시 제외)
//
// 사용법 (외부 실행자, API 키 보유 시점):
//   1. 패키지 출처 검증 ✓ (위 ⚠️ 룰)
//   2. `npm view exa-mcp-server repository` 또는 GitHub 직접 확인
//   3. EXA_API_KEY env set
//        Windows PowerShell: `$env:EXA_API_KEY="<key>"; node probe_exa.js`
//        Bash: `EXA_API_KEY=<key> node probe_exa.js`
//   4. COUNT=N 라인 + 도구 목록 → 17차 docs 박제와 매칭 확인 (active 3 + deprecated 7 = 10 가설, 또는 advertise는 active만 가능)
//   5. deprecated 도구가 advertise되는지가 *deprecated 운영 함의* 확정 자료 (advertise 안 하면 frontmatter allowlist에 적을 필요도 없음)

const { spawn } = require("child_process");

// === 환경별 수정 영역 ===
const NPX_PATH = "npx";
const PACKAGE_SPEC = process.env.EXA_PACKAGE || "exa-mcp-server";
const EXTRA_FLAGS = (process.env.EXA_FLAGS || "").split(/\s+/).filter(Boolean);
// =======================

const args = ["-y", PACKAGE_SPEC, ...EXTRA_FLAGS];
console.log(`[probe_exa] spawning: ${NPX_PATH} ${args.join(" ")}`);
console.log(`[probe_exa] EXA_API_KEY ${process.env.EXA_API_KEY ? "✓ set" : "⚠️ unset — startup fail 가능"}`);

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
        const deprecated = ["get_code_context_exa", "company_research_exa", "crawling_exa", "people_search_exa", "linkedin_search_exa", "deep_researcher_start", "deep_researcher_check", "deep_search_exa"];
        for (const t of tools) {
          const required = (t.inputSchema && t.inputSchema.required) || [];
          const props = (t.inputSchema && t.inputSchema.properties) || {};
          const allParams = Object.keys(props);
          const dep = deprecated.includes(t.name) ? "  ⚠️ deprecated" : "";
          console.log(`  - ${t.name}  required=[${required.join(",")}]  all=[${allParams.join(",")}]${dep}`);
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
    clientInfo: { name: "probe-exa", version: "0.0.1" },
  },
});
send({ jsonrpc: "2.0", method: "notifications/initialized", params: {} });
send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });

timeoutHandle = setTimeout(() => {
  console.error("TIMEOUT (60s) — npx가 exa-mcp-server 패키지를 첫 실행 시 다운로드. 네트워크 또는 캐시 확인. EXA_API_KEY 미설정 시 서버가 즉시 종료할 수 있음 (stderr 확인).");
  cleanExit(2);
}, 60000);
