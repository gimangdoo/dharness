# verify_11_3_p3b.ps1 — §11-3 P3-(b) user-scope gate 격리 측정 (v2 — quote escape 픽스)
#
# 13차 사이클 closure(project-scope settings.json 토글 = 0 효과 empirical) 후속.
# `~/.claude.json` projects.{<derived>}.{enabledMcpjsonServers,hasTrustDialogAccepted}의
# *진짜 gate 채널* 식별을 위해 각 키를 단독 토글해 deferred pool M2를 측정한다.
#
# 사용법: 외부 PowerShell 세션 또는 dharness 세션의 `!` prefix에서 실행:
#   PS> powershell -NoProfile -ExecutionPolicy Bypass -File <abs>\verify_11_3_p3b.ps1
#
# v2 변경: PowerShell→Node 인자에 `"`(예: `["sqlite"]`) 직접 임베드 시 native exe escape로 strip되는
#         문제를 env var 경유로 회피. 모든 `"`는 node 스크립트 내부(JS string)에 격리.
#
# 차단 사유: dharness 본 세션의 auto-mode classifier가 `~/.claude.json` user-scope 쓰기를
#          연속 호출하면 *후속* 쓰기를 일관 차단한다 (15차 사이클 empirical, §10-7 4번 룰 확정).

$ErrorActionPreference = "Stop"
$proj = "C:/Users/user01/dharness-probe-test"
$json = ($env:USERPROFILE -replace '\\','/') + "/.claude.json"
$prompt = "system-reminder의 deferred tool 명단에서 'mcp__'로 시작하는 도구 이름만 줄당 하나씩 그대로 보고. 다른 설명 없이 도구명만. 없으면 NONE."

function Show-Gate($label) {
    $env:DH_JSON = $json
    $env:DH_PROJ = $proj
    $out = node -e "const fs=require('fs'),d=JSON.parse(fs.readFileSync(process.env.DH_JSON,'utf8')),e=d.projects[process.env.DH_PROJ];console.log(JSON.stringify({en:e.enabledMcpjsonServers,tr:e.hasTrustDialogAccepted,dis:e.disabledMcpjsonServers}))"
    Write-Output ("[gate $label] $out")
}

function Set-Gate($enabled, $trust, $disabled) {
    # disabled: $true → disabledMcpjsonServers=["sqlite"] (명시 차단) / $false → []
    if ($null -eq $disabled) { $disabled = $false }
    $env:DH_JSON = $json
    $env:DH_PROJ = $proj
    $env:DH_EN  = if ($enabled)  { '1' } else { '0' }
    $env:DH_TR  = if ($trust)    { '1' } else { '0' }
    $env:DH_DIS = if ($disabled) { '1' } else { '0' }
    node -e "const fs=require('fs'),p=process.env.DH_JSON,k=process.env.DH_PROJ,d=JSON.parse(fs.readFileSync(p,'utf8'));d.projects[k].enabledMcpjsonServers=process.env.DH_EN==='1'?['sqlite']:[];d.projects[k].hasTrustDialogAccepted=process.env.DH_TR==='1';d.projects[k].disabledMcpjsonServers=process.env.DH_DIS==='1'?['sqlite']:[];fs.writeFileSync(p,JSON.stringify(d,null,2));" | Out-Null
}

function Measure-One($label) {
    Set-Location $proj
    Write-Output ""
    Write-Output "=== $label ==="
    Show-Gate $label
    $result = claude -p $prompt 2>&1
    $count = ($result | Where-Object { $_ -match '^mcp__' } | Measure-Object).Count
    Write-Output "[result count=$count]"
    Write-Output $result
    Write-Output ""
}

Write-Output "===== verify_11_3_p3b v3 — P3-(b) 4-key gate full matrix ====="
Write-Output ""

# B5 — gate 4 ON (baseline, 13차 B1 재현)
Set-Gate -enabled $true -trust $true -disabled $false
Measure-One "B5 (gate ALL ON - baseline)"

# B6 — enabledMcpjsonServers=[] 단독 OFF
Set-Gate -enabled $false -trust $true -disabled $false
Measure-One "B6 (enabledMcpjsonServers=[] ONLY)"

# B7 — hasTrustDialogAccepted=false 단독 OFF (enabled 복원)
Set-Gate -enabled $true -trust $false -disabled $false
Measure-One "B7 (hasTrustDialogAccepted=false ONLY)"

# B8 (v3 신규) — disabledMcpjsonServers=["sqlite"] 명시 차단 단독 ON (trust 복원, 다른 키 ALL ON)
Set-Gate -enabled $true -trust $true -disabled $true
Measure-One "B8 (disabledMcpjsonServers=['sqlite'] ONLY — 명시 차단)"

# Final restore — gate 4 ON (disabled=[] 포함)
Set-Gate -enabled $true -trust $true -disabled $false
Show-Gate "FINAL (restored)"

Write-Output ""
Write-Output "===== Done. 결과를 fixtures/verify_11_3.md '측정 로그'에 행 추가 ====="
Set-Location $PSScriptRoot
