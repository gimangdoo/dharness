# Team Tools API — 6-tool Signature Reference

> **Read at phase:** When using sub-agents in Phase 1/5/6/8 (isolated invocation patterns) + Phase 4 team design pseudocode verification.
>
> **Purpose**: Single-source schema reference for the six tools `TeamCreate` / `SendMessage` / `TaskCreate` / `TaskUpdate` / `TaskGet` / `TaskOutput`. Used by pseudocode sections in SKILL.md Phase 4·5·7, `agent-design-patterns.md`, `orchestrator-template.md`, `team-examples.md`.
>
> **Status taxonomy (2026-05-14)**:
> - `✅ verified` — Cataloged in the official Claude Code tool catalog + at least one real invocation trial logged.
> - `📜 docs-only` — Cited from the official Claude Code documentation only; no real invocation verified.
> - `❓ inferred` — Empirical inference (real call results + analogy with general Anthropic SDK signatures).
>
> **Phases that read this file**: Phase 4 (team composition) · Phase 5 (agent definition) · Phase 7 (orchestration). Each phase lazy-loads *only the relevant tool section* of this reference.

---

## §1 Tool Usage Scenario Matrix (Phase 4 Guide)

| Scenario | Tools Used | Notes |
|---|---|---|
| 2+ agent collaboration (default mode) | `TeamCreate` + `TaskCreate` + `SendMessage` | Template A baseline |
| One-shot isolated delegation | `Agent` (Claude Code built-in, out of scope for this reference) | Template B |
| Asynchronous task pool | `TaskCreate` + `TaskGet` + `TaskOutput` | Task pool + polling |
| Progress update | `TaskUpdate` | Status transitions |
| Inter-member data transfer | `SendMessage` | Inbox pattern |

---

## §2 `TeamCreate` ❓ inferred

**Purpose**: Create a team of two or more agents. Define the team name plus N members.

**Signature** (pseudo-schema — real-call trial logging recommended):

```yaml
TeamCreate:
  parameters:
    team_name: string         # required — team identifier (slug form)
    members:                  # required — member array (≥2)
      - name: string          # required — member identifier (slug)
        agent_type: string    # required — "general-purpose" | "Explore" | "Plan" | custom agent name
        model: string         # optional — "opus" | "sonnet" | "haiku" (default "opus")
        prompt: string        # required — role description + task instructions
        tools: [string]       # optional — per-member tool allowlist (synced with frontmatter `tools:`)
    description: string       # optional — one-line team purpose
  returns:
    team_id: string           # used by subsequent SendMessage / TaskCreate
    members: [object]         # detailed list of created members
```

**Failure modes** (empirical inference):
- Duplicate `team_name`: error when the same team name is created twice in one session.
- `members` < 2: one-shot delegation must use `Agent` (out of scope for this tool).
- Missing `agent_type`: `.claude/agents/{name}.md` does not exist and the name is not a built-in type.

**Example**:

```yaml
TeamCreate(
  team_name: "research-team"
  members:
    - name: "researcher"
      agent_type: "general-purpose"
      model: "opus"
      prompt: "Gather material related to domain X."
      tools: ["WebSearch", "WebFetch", "Read"]
    - name: "synthesizer"
      agent_type: "general-purpose"
      model: "opus"
      prompt: "Synthesize the gathered material."
      tools: ["Read", "Write"]
)
```

**Note**: The exact signature must be verified against the official Claude Code tool catalog plus a real invocation trial. P1-1 AC: log a real trial or invoke the `claude-code-guide` agent.

---

## §3 `SendMessage` ❓ inferred

**Purpose**: Deliver messages between team members. Inbox pattern — recipients poll on a subsequent turn.

**Signature**:

```yaml
SendMessage:
  parameters:
    team_id: string           # required — TeamCreate return value
    from: string              # required — sender member name
    to: string                # required — receiver member name
    content: string           # required — message body (markdown allowed)
    metadata: object          # optional — structured payload (key-value)
  returns:
    message_id: string        # for tracing
    delivered: boolean        # whether the inbox accepted it
```

**Failure modes**:
- `to` is not present in the team's members.
- `team_id` missing or session expired.
- Empty `content` string.

**Example**:

```yaml
SendMessage(
  team_id: "research-team-001"
  from: "researcher"
  to: "synthesizer"
  content: "Step-1 material gathering complete. See _workspace/01_researcher_findings.md."
)
```

---

## §4 `TaskCreate` ❓ inferred

**Purpose**: Register N tasks in the team's task pool. Dependencies and assignees may be specified.

**Signature**:

```yaml
TaskCreate:
  parameters:
    tasks:                    # required — task array
      - title: string         # required — task title
        description: string   # required — detailed instructions
        assignee: string      # optional — member name (unclaimed if omitted)
        depends_on: [string]  # optional — prerequisite task title or task_id
        priority: string      # optional — "high" | "medium" | "low" (default "medium")
        metadata: object      # optional
  returns:
    task_ids: [string]
```

**5–6 tasks per team member is the sweet spot** (orchestrator-template.md doctrine).

**Failure modes**:
- `depends_on` references a non-existent task (errors on cycle detection).
- `assignee` not found in the member list.

**Example**:

```yaml
TaskCreate(
  tasks:
    - title: "Domain X first-pass gathering"
      description: "Use WebSearch on three keywords; save results to _workspace/01_researcher.md."
      assignee: "researcher"
    - title: "Synthesize gathered material"
      description: "Take _workspace/01_researcher.md as input; produce _workspace/02_synthesizer.md."
      assignee: "synthesizer"
      depends_on: ["Domain X first-pass gathering"]
)
```

---

## §5 `TaskUpdate` ❓ inferred

**Purpose**: Transition task state. The assignee calls this during execution.

**Signature**:

```yaml
TaskUpdate:
  parameters:
    task_id: string           # required
    status: string            # optional — "pending" | "in_progress" | "completed" | "blocked" | "deleted"
    owner: string             # optional — change assignee
    description: string       # optional — update
    metadata: object          # optional — merge
    addBlocks: [string]       # optional — task_ids that this task blocks
    addBlockedBy: [string]    # optional — task_ids that block this task
  returns:
    task: object              # the full updated task
```

**Status workflow**: `pending` → `in_progress` → `completed`. `blocked` records a delay reason. `deleted` is a permanent removal.

---

## §6 `TaskGet` ❓ inferred

**Purpose**: Fetch the details of a single task.

**Signature**:

```yaml
TaskGet:
  parameters:
    task_id: string           # required
  returns:
    task: object              # title / description / status / owner / blockedBy / blocks / metadata / comments
```

---

## §7 `TaskOutput` ❓ inferred

**Purpose**: Fetch a task's *output*. The assignee records the output on completion; downstream tasks consume it via this tool.

**Signature**:

```yaml
TaskOutput:
  parameters:
    task_id: string           # required
    format: string            # optional — "raw" | "markdown" | "json" (default "raw")
  returns:
    output: string | object   # task output
    produced_at: string       # ISO timestamp
```

**File-based output pattern (consistent with orchestrator-template.md)**: The assignee writes its result to `_workspace/{phase}_{name}_{artifact}.{ext}` and records it via `TaskUpdate(metadata: {output_path: "..."})`. Downstream tasks then `TaskGet` + read the path directly — `TaskOutput` is used for the *inline result* pattern (small outputs).

---

## §8 Call Pattern — Orchestrator Synthesis (Phase 7 Guide)

```yaml
# 1) Form the team
team = TeamCreate(team_name: "{domain}-team", members: [...])

# 2) Register the task pool
tasks = TaskCreate(tasks: [
  {title: "step1", assignee: "{m1}"},
  {title: "step2", assignee: "{m2}", depends_on: ["step1"]}
])

# 3) (Optional) Progress monitoring — polling pattern
for task_id in tasks:
  task = TaskGet(task_id: task_id)
  if task.status == "blocked":
    handle_block(task)

# 4) Inter-member communication — inbox pattern
SendMessage(team_id: team.team_id, from: "{m1}", to: "{m2}", content: "Step-1 output at _workspace/01_m1.md")

# 5) Update task state
TaskUpdate(task_id: tasks[0], status: "completed", metadata: {output_path: "_workspace/01_m1.md"})

# 6) Downstream task consumes the output
output = TaskOutput(task_id: tasks[0])
```

---

## §9 Verification Doctrine (P1-1 AC Alignment)

This reference is a *placeholder* — real-call trial logging is required to refine it.

| AC | Logging Method | Priority |
|---|---|---|
| Refine signatures | (a) Cite the official Claude Code tool catalog URL / (b) Call the `claude-code-guide` agent / (c) Log a trial-and-error real call | 🔴 High |
| Return-value schemas | Log the raw result of a trial call | 🔴 High |
| Failure modes | Log responses to deliberate error calls (e.g., duplicate `team_name`, missing `assignee`) | 🟡 Mid |
| Call examples | Verify that the §8 patterns match real calls | 🟡 Mid |

**Doctrine**: While P1-1 is in progress this reference remains at ❓ inferred; it is promoted to ✅ verified by trial logging. Pseudocode sections in SKILL.md / `agent-design-patterns.md` / `orchestrator-template.md` / `team-examples.md` keep their cross-links to this reference.

---

## Notes

- User confirmation (2026-05-14): P1-1 task priority 🔴 High — directly depended on by Sp2 (self-critique sub-agents). Sub-agent calls depend on the trustworthiness of this tool schema.
- Source logging: at authoring time this reference is at the ❓ inferred stage; promotion is a separate cycle.

---

## P7-1 POC note (2026-05-14)

This file is the English POC of `team-tools-api.md`. The Korean version remains the source of truth until the **PLAN.md P7-2 task** (KR/EN bilingual trigger regression — 40 utterances against description matching, currently `todo`) confirms parity. Both files coexist during the POC; cross-references in other documents continue to point at `team-tools-api.md`.
