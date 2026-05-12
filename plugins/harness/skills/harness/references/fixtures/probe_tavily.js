// §10 Step 2 fixture — pre-install JSON-RPC stdio probe for Tavily MCP (T1+)
//
// ⚠️ 패키지 출처 검증 (§8-3 안전 룰) — probe도 코드 실행이다:
//   - 본 스크립트는 `tavily-mcp` (npm, github.com/tavily-ai/tavily-mcp) Tavily 메인테이너 패키지를 spawn
//   - 미trust 변형(`mcp-tavily`, `@<scope>/tavily-mcp` 등 이름 spoofing)은 install과 동일 위협 모델 — 사용자 명시 trust 후에만 사용
//
// ⚠️ T1+ 함정 (API 키 필수):
//   - TAVILY_API_KEY env가 없으면 서버 startup 시 fail 가능성 — 일부 MCP는 initialize는 통과시키고 tool call 시 fail (실측 필요)
//   - probe-only 모드: TAVILY_API_KEY를 *dummy* 값으로 set하고 tools/list 응답이 오는지 시도
//   - Free tier 1,000 credits/month (2026-05 기준, search=1 credit, extract=1 credit/url, 외부 실행자 정책 확인)
//
// ⚠️ 도구명 하이픈 — *첫 케이스* (sequential-thinking 패턴과 다름):
//   - sequential-thinking은 서버명에만 하이픈, 도구명은 `sequentialthinking` (합성형)
//   - tavily는 *도구명 자체에 하이픈*: `tavily-search`, `tavily-extract`, `tavily-map`, `tavily-crawl`
//   - frontmatter `tools:` 참조 시 `mcp__tavily__tavily-search` 형태 추정 — §11-1 6차 사이클 enum 규칙(하이픈 보존)으로 정상 작동 가설, 첫 실 enum 시 검증 필수
//
// 사용법 (외부 실행자, API 키 보유 시점):
//   1. 패키지 출처 검증 ✓ (위 ⚠️ 룰)
//   2. `npm view tavily-mcp repository` 또는 GitHub 직접 확인
//   3. TAVILY_API_KEY env set
//        Windows PowerShell: `$env:TAVILY_API_KEY="<key>"; node probe_tavily.js`
//        Bash: `TAVILY_API_KEY=<key> node probe_tavily.js`
//   4. COUNT=N 라인과 도구 목록을 §3 인벤토리 tavily 행 enumeration 박제 (17차 docs 박제 4종 매칭 확인)
//   5. 추가 검증: 다음 세션 SessionStart deferred tool list에서 `mcp__tavily__tavily-*` 4종이 *하이픈 보존*되는지 확인 — 새로운 §11-1 케이스로 박제
//
// 17차 docs 박제 예상 enum:
//   - tavily-search   required=[query]                  (web search)
//   - tavily-extract  required=[urls]                   (URL 본문 추출)
//   - tavily-map      required=[url]                    (사이트 구조 매핑)
//   - tavily-crawl    required=[url]                    (도메인 크롤)
//   (총 4종, 모두 read-only — default 권고 4종 `allow`, T1+ quota 게이트는 `ask`)

const { spawn } = require("child_process");

// === 환경별 수정 영역 ===
const NPX_PATH = "npx";
const PACKAGE_SPEC = process.env.TAVILY_PACKAGE || "tavily-mcp@latest";
// =======================

const args = ["-y", PACKAGE_SPEC];
console.log(`[probe_tavily] spawning: ${NPX_PATH} ${args.join(" ")}`);
console.log(`[probe_tavily] TAVILY_API_KEY ${process.env.TAVILY_API_KEY ? "✓ set" : "⚠️ unset — startup fail 가능"}`);

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
    clientInfo: { name: "probe-tavily", version: "0.0.1" },
  },
});
send({ jsonrpc: "2.0", method: "notifications/initialized", params: {} });
send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });

timeoutHandle = setTimeout(() => {
  console.error("TIMEOUT (60s) — npx가 tavily-mcp@latest 패키지를 첫 실행 시 다운로드. 네트워크 또는 캐시 확인. TAVILY_API_KEY 미설정 시 서버가 즉시 종료할 수 있음 (stderr 확인).");
  cleanExit(2);
}, 60000);
