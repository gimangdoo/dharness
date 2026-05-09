---
name: memory-curate
description: |
  cm-curator 에이전트가 observations를 클러스터링하고, confidence를 갱신하고,
  skill 승격을 판정할 때 사용하는 스킬. 클러스터링 알고리즘, decay half-life,
  승격 임계치를 정의한다. "메모리 클러스터링", "클러스터 정리", "skill 승격 판정" 시 참조.
---

# memory-curate

observations 클러스터링, confidence 갱신, skill memory 승격 판정 규칙을 정의한다.

## 클러스터링 알고리즘

### 입력
새로운 observation_ids 목록 (cm-digester로부터)

### 처리 흐름

```
1. 각 observation의 content + tags 읽기
2. 기존 clusters와 주제 유사성 비교 (FTS5 키워드 겹침 기준)
3. 유사도 > 0.6: 기존 cluster에 병합
4. 유사도 ≤ 0.6: 신규 cluster 생성
5. 병합된 cluster의 confidence 업데이트
6. 오래된 cluster decay 적용
```

### 유사도 계산 (S4 이전: 키워드 기반)

```python
# 간단 키워드 겹침 비교 (sqlite-vec 없을 때)
def similarity(obs_tags, cluster_tags):
    obs_set = set(obs_tags)
    cluster_set = set(cluster_tags)
    if not obs_set or not cluster_set:
        return 0.0
    return len(obs_set & cluster_set) / len(obs_set | cluster_set)

# 유사도 0.6 이상 → 같은 cluster
```

### 유사도 계산 (S4 이후: 벡터 기반)

sqlite-vec의 cosine_distance 사용:
```sql
SELECT cluster_id, cosine_distance(embedding, ?) as dist
FROM clusters
ORDER BY dist ASC
LIMIT 5;
```
거리 < 0.4 → 병합 (cosine_distance 0 = 완전 동일, 1 = 완전 다름)

## Confidence 갱신 규칙

### 증가 조건

| 이벤트 | 증가량 |
|--------|--------|
| 새 observation 병합 | +0.05 |
| 메모리 검색에서 조회됨 | +0.03 |
| 사용자가 "유용함" 피드백 | +0.10 |
| Do 항목이 완료됨 (다음 세션에서) | +0.08 |

### Decay (감소) 규칙

- Half-life: 30일 (30일 미조회 시 confidence × 0.5)
- 연속 decay 하한: 0.05 (완전히 0이 되지 않음)
- decay 적용 시점: cm-curator 실행마다 마지막 조회일 확인

```python
import math
days_unused = (today - last_accessed).days
if days_unused >= 30:
    decay_factor = 0.5 ** (days_unused / 30)
    new_confidence = max(0.05, current_confidence * decay_factor)
```

## 승격 임계치

| 조건 | 판정 |
|------|------|
| confidence ≥ 0.80 | 승격 후보 (사용자 확인 요청) |
| confidence 0.50 ~ 0.79 | 유지 (계속 관찰) |
| confidence < 0.20 | 제거 후보 (사용자 확인 요청) |
| 멤버 observations ≥ 5 | 승격 후보 가중치 +0.10 |

## 승격 프로세스

승격은 **반드시 사용자 확인 후** 실행한다:

```
1. cm-curator → 사용자에게 승격 후보 알림
   "클러스터 '{theme}' 승격 후보 (confidence: 0.82, 7개 세션에서 관찰)
    .claude/skills/{name}/SKILL.md를 생성합니다. 진행할까요? [y/n]"

2. 사용자 승인 시:
   a. .claude/skills/{name}/SKILL.md 생성 (cluster 내용 기반)
   b. CLAUDE.md 변경 이력 업데이트
   c. cluster.promoted = ".claude/skills/{name}/SKILL.md" 기록
   d. telemetry: memory_promoted 이벤트 append
   e. 위 a-d는 atomic (실패 시 전체 rollback)

3. 사용자 거부 시:
   - cluster confidence 재조정 (-0.10)
   - 거부 학습: 30일간 재승격 제안 억제
```

## 클러스터 파일 형식

`_workspace/_memory/clusters/{cluster_id}.md`:

```markdown
---
cluster_id: c_{6자 hex}
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
last_accessed: YYYY-MM-DD
confidence: 0.0-1.0
member_count: <n>
member_observations: [obs_ids]
promoted: false | "<skill_path>"
tags: [<topic_keywords>]
---

## 주제
{클러스터의 핵심 주제 1-2문장}

## 반복 패턴
{관찰된 반복 동작 또는 지식 패턴}

## 근거
{어떤 세션에서, 어떤 상황에서 관찰됐는지}
```

## 제거 프로세스

confidence < 0.05 또는 사용자 요청 시:

```
1. 사용자에게 확인 요청
2. cluster 파일 삭제
3. member observations에서 cluster_id 참조 제거
4. telemetry: memory_decayed 이벤트
```
