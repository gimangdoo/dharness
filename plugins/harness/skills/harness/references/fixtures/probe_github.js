// §10 Step 2 fixture — pre-install JSON-RPC stdio probe for GitHub MCP (T1+)
//
// ⚠️ 패키지 출처 검증 (§8-3 안전 룰) — probe도 코드 실행이다:
//   - 본 스크립트는 `ghcr.io/github/github-mcp-server` (Docker, github.com/github/github-mcp-server) GitHub 공식 메인테이너 이미지를 spawn
//   - 17차 docs 박제 정정: **npm 패키지 없음** — Docker 이미지 또는 Go 바이너리만 지원
//   - 미trust 변형(`mcp-github`, `@<scope>/github-mcp` npm 패키지 등 이름 spoofing — 공식 채널 아님)은 install과 동일 위협 모델
//   - 대체 채널: `go build -o github-mcp-server ./cmd/github-mcp-server && ./github-mcp-server stdio` (Go toolchain 보유 시) — Docker 미설치 환경
//
// ⚠️ T1+ 함정 (PAT 필수, scope 명시 권고):
//   - GITHUB_PERSONAL_ACCESS_TOKEN env 없으면 startup 시 즉시 fail
//   - PAT 생성 시 *최소 권한*: `repo`(private 필요 시), `read:user`, `read:org` 권장 — write scope는 fine-grained로 분리
//   - Fine-grained PAT 권고 — classic PAT는 모든 repo 접근 권한 부여로 blast radius 큼
//
// ⚠️ toolset 필터 (Layer A) — 본 fixture의 핵심 측정 의도:
//   - GITHUB_TOOLSETS env로 advertise 도구 *자체*를 줄임 — 합성 산출물 inline `mcpServers:` 패턴 §5-1-b의 default
//   - default toolsets 5종: `context`, `repos`, `issues`, `pull_requests`, `users`
//   - 추가 toolsets 14종: `actions`, `code_security`, `copilot`, `dependabot`, `discussions`, `gists`, `git`, `labels`, `notifications`, `orgs`, `projects`, `secret_protection`, `security_advisories`, `stargazers`
//   - 특수 값: `all` (전부 advertise), `default` (default 5종)
//   - 본 probe는 환경 변수로 toolset 조합을 변경하여 *advertise 도구 카운트 차이*를 측정 — §3-1 매트릭스 github 행에 *toolset당 도구 카운트* 박제 자료
//
// 사용법 (외부 실행자, PAT 보유 시점):
//   1. 패키지 출처 검증 ✓ (위 ⚠️ 룰) — ghcr.io/github/* 또는 github.com/github/github-mcp-server 직접 확인
//   2. Docker 가용 확인 (`docker --version`) 또는 Go binary 빌드
//   3. PAT 생성 (fine-grained, 최소 권한) — `https://github.com/settings/personal-access-tokens/new`
//   4. env set:
//        Windows PowerShell: `$env:GITHUB_PERSONAL_ACCESS_TOKEN="<pat>"; $env:GITHUB_TOOLSETS="pull_requests"; node probe_github.js`
//        Bash: `GITHUB_PERSONAL_ACCESS_TOKEN=<pat> GITHUB_TOOLSETS=pull_requests node probe_github.js`
//   5. COUNT=N + 도구 목록 → §3 인벤토리 github 행 + §3-1 매트릭스 external-integration profile *toolset별 도구 카운트* 박제
//   6. 측정 의도 (3종 비교):
//        (a) GITHUB_TOOLSETS="pull_requests"      → 단일 toolset 도구 풀
//        (b) GITHUB_TOOLSETS="default"            → 5 toolsets 도구 풀
//        (c) GITHUB_TOOLSETS="all"                → 19 toolsets 도구 풀
//        — Layer A 서버 측 advertise 필터의 *empirical 절감 비율* 측정 (§1 [^A] 셀의 server-side 채널 — 13·15·16차에 미측정 남은 분기)

const { spawn } = require("child_process");

// === 환경별 수정 영역 ===
const DOCKER_PATH = process.env.DOCKER_PATH || "docker";
const IMAGE = process.env.GITHUB_MCP_IMAGE || "ghcr.io/github/github-mcp-server";
const TOOLSETS = process.env.GITHUB_TOOLSETS || "default";
// =======================

const args = [
  "run", "-i", "--rm",
  "-e", `GITHUB_PERSONAL_ACCESS_TOKEN=${process.env.GITHUB_PERSONAL_ACCESS_TOKEN || ""}`,
  "-e", `GITHUB_TOOLSETS=${TOOLSETS}`,
  IMAGE,
];
console.log(`[probe_github] spawning: ${DOCKER_PATH} ${args.map(a => a.startsWith("GITHUB_PERSONAL") ? "GITHUB_PERSONAL_ACCESS_TOKEN=<redacted>" : a).join(" ")}`);
console.log(`[probe_github] GITHUB_PERSONAL_ACCESS_TOKEN ${process.env.GITHUB_PERSONAL_ACCESS_TOKEN ? "✓ set" : "⚠️ unset — startup fail"}`);
console.log(`[probe_github] GITHUB_TOOLSETS=${TOOLSETS} (default 5종 / "all" 19종)`);

const child = spawn(DOCKER_PATH, args, {
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
        console.log(`TOOLSETS=${TOOLSETS}`);
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
      // ignore non-JSON noise (Docker pull 진행 로그 등)
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
    clientInfo: { name: "probe-github", version: "0.0.1" },
  },
});
send({ jsonrpc: "2.0", method: "notifications/initialized", params: {} });
send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });

timeoutHandle = setTimeout(() => {
  console.error("TIMEOUT (120s) — Docker pull 또는 GitHub MCP startup stuck. (a) Docker 자체 시작 확인 (b) ghcr.io 네트워크 확인 (c) PAT 유효성 확인 (Github Settings → Personal access tokens).");
  cleanExit(2);
}, 120000);
