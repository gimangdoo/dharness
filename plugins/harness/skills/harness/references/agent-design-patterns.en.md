# Agent Team Design Patterns

> **Read at phase:** Phase 4 (team pattern selection) + Phase 5 (apply pattern when defining agents). Re-read explicitly on cross-phase reference.

## Execution Modes: Agent Team vs Sub-agent

Understand the core difference between the two execution modes and pick the one that fits.

### Agent Team — Default Mode

The team leader composes a team via `TeamCreate`. Members run as independent Claude Code instances. Members communicate directly via `SendMessage` and self-coordinate through a shared task list (`TaskCreate` / `TaskUpdate`).

```
[Leader] ←→ [MemberA] ←→ [MemberB]
   ↕            ↕            ↕
   └──── Shared task list ────┘
```

**Core tools:**
- `TeamCreate`: create team + spawn members
- `SendMessage({to: name})`: message a specific member
- `SendMessage({to: "all"})`: broadcast (expensive — use rarely)
- `TaskCreate` / `TaskUpdate`: manage the shared task list

**Characteristics:**
- Members can talk, challenge, and verify each other directly
- Information exchange without going through the leader
- Self-coordinate via shared task list (members can request their own work)
- Idle members auto-notify the leader
- Plan-approval mode allows review before dangerous actions

**Constraints:**
- Only one team **active** per session (teams may be disbanded between Phases and a new team formed)
- No nested teams (a member cannot create its own team)
- Leader is fixed (no transfer)
- High token cost

**Team reformation pattern:**
When different specialist mixes are needed across Phases, save the previous team's artifacts to files → tear down the team → create a new team. Previous artifacts remain in `_workspace/` so the new team can Read them.

### Sub-agents — Lightweight Mode

A main agent spawns sub-agents via the `Agent` tool. Sub-agents return results to the main agent only and do not talk to each other.

```
[Main] → [SubA] → return result
       → [SubB] → return result
       → [SubC] → return result
```

**Core tool:**
- `Agent(prompt, subagent_type, run_in_background)`: spawn sub-agent

**Characteristics:**
- Lightweight and fast
- Results summarized back into the main context
- Token-efficient

**Constraints:**
- No inter-sub-agent communication
- Main handles all coordination
- No real-time collaboration or challenge

### Mode-Selection Decision Tree

```
Two or more agents?
├── Yes → Inter-agent communication needed?
│         ├── Yes → Agent Team (default)
│         │         Cross-verification, shared discovery, real-time feedback raise quality.
│         │
│         └── No → Sub-agents also viable
│                  Producer-verifier with result handoff only, expert pool, etc.
│
└── No (one agent) → Sub-agent
                     A single agent does not need a team.
```

> **Core principle:** Agent Team is the default. When choosing sub-agents, ask: "Is member-to-member communication truly unnecessary?"

---

## Agent Team Architecture Types

### 1. Pipeline
Sequential workflow. One agent's output is the next agent's input.

```
[Analyze] → [Design] → [Implement] → [Verify]
```

**Fits when:** Each stage depends strongly on the previous stage's artifact.
**Example:** Novel writing — worldbuilding → characters → plot → drafting → editing.
**Caution:** A bottleneck slows the entire pipeline. Design stages to be as independent as possible.
**Team-mode fit:** Strong sequential dependency limits team-mode upside. Useful only if parallel sub-stages exist within the pipeline.

### 2. Fan-out / Fan-in
Parallel work followed by result integration. Independent tasks executed simultaneously.

```
         ┌→ [ExpertA] ─┐
[Split] → ├→ [ExpertB] ─┼→ [Merge]
         └→ [ExpertC] ─┘
```

**Fits when:** The same input needs analysis from different perspectives/domains.
**Example:** Comprehensive research — official sources / media / community / background investigated in parallel → integrated report.
**Caution:** Merge-stage quality determines overall quality.
**Team-mode fit:** The most natural pattern for agent teams. **Must be built as an agent team.** Members share findings, challenge each other, and one agent's discovery can redirect another's investigation in real time — quality gain over solo investigation is large.

### 3. Expert Pool
Route to an appropriate specialist depending on context.

```
[Router] → { ExpertA | ExpertB | ExpertC }
```

**Fits when:** Different input types need different handling.
**Example:** Code review — call only the security / performance / architecture expert that matches the area.
**Caution:** Router classification accuracy is the linchpin.
**Team-mode fit:** Sub-agents fit better — only the needed expert is invoked, so a standing team is unnecessary.

### 4. Producer-Reviewer
A producer and a reviewer agent work in pairs.

```
[Produce] → [Review] → (on issue) → [Produce] retry
```

**Fits when:** Artifact quality matters and objective verification criteria exist.
**Example:** Webtoon — artist produces → reviewer inspects → regenerate problematic panels.
**Caution:** Set a max retry count (2–3) to prevent infinite loops.
**Team-mode fit:** Agent team is useful. SendMessage carries real-time feedback between producer and reviewer.

### 5. Supervisor
A central agent manages task state and dynamically distributes work to lower agents.

```
         ┌→ [WorkerA]
[Supervisor] ─┼→ [WorkerB]    ← supervisor distributes dynamically based on state
         └→ [WorkerC]
```

**Fits when:** Workload varies or distribution must be decided at runtime.
**Example:** Large-scale code migration — supervisor analyzes file list and assigns batches to workers.
**Difference from fan-out:** Fan-out pre-assigns work; supervisor adjusts as work progresses.
**Caution:** Keep delegation units large so the supervisor does not become the bottleneck.
**Team-mode fit:** The agent team's shared task list maps naturally onto the supervisor pattern. TaskCreate registers tasks; members self-claim.

### 6. Hierarchical Delegation
A higher agent delegates recursively to lower agents. Complex problems decomposed in stages.

```
[Lead] → [SubleadA] → [WorkerA1]
                    → [WorkerA2]
       → [SubleadB] → [WorkerB1]
```

**Fits when:** The problem decomposes naturally into a hierarchy.
**Example:** Full-stack app — lead → frontend lead → (UI / logic / tests) + backend lead → (API / DB / tests).
**Caution:** Depth ≥3 amplifies latency and context loss. Keep within 2 levels.
**Team-mode fit:** Agent teams cannot nest (members cannot create teams). Implement level-1 as a team and level-2 as sub-agents, or flatten into a single team.

## Composite Patterns

Composite patterns are more common than single patterns in practice:

| Composite | Composition | Example |
|----------|-------------|---------|
| **Fan-out + Producer-Reviewer** | Parallel produce → individual review | Multilingual translation — 4 languages in parallel → native reviewer per language |
| **Pipeline + Fan-out** | Some sequential stages parallelized | Analysis (sequential) → implementation (parallel) → integration test (sequential) |
| **Supervisor + Expert Pool** | Supervisor dynamically calls experts | Customer-inquiry routing — supervisor classifies then assigns the right expert |

### Execution Mode for Composite Patterns

**Use an agent team for every composite pattern by default.** Active member-to-member communication is the main driver of output quality.

| Scenario | Recommended Mode | Reason |
|---------|------------------|--------|
| **Research + Analysis** | Agent team | Investigators share findings, discuss conflicting info in real time |
| **Design + Implementation + Verification** | Agent team | Feedback loop between designer ↔ implementer ↔ verifier |
| **Supervisor + Workers** | Agent team | Dynamic assignment via shared task list, progress visibility across workers |
| **Producer + Reviewer** | Agent team | Real-time feedback between producer and reviewer minimizes rework |

> Mix sub-agents in only when a single agent runs a fully isolated one-shot task.

## Agent Type Selection

Specify the type via the `Agent` tool's `subagent_type` parameter. Team members may also use custom agent definitions.

### Built-in Types

| Type | Tool Access | Suited For |
|------|------------|-----------|
| `general-purpose` | Full (incl. WebSearch, WebFetch) | Web research, general-purpose work |
| `Explore` | Read-only (no Edit/Write) | Codebase exploration, analysis |
| `Plan` | Read-only (no Edit/Write) | Architecture design, planning |

### Custom Types

Define an agent at `.claude/agents/{name}.md` and call it with `subagent_type: "{name}"`. Custom agents get full tool access.

### Selection Criteria

| Situation | Recommended | Reason |
|-----------|-------------|--------|
| Role is complex, reused across sessions | **Custom type** (`.claude/agents/`) | Persona and work principles managed in a file |
| Simple investigation/collection, prompt is enough | **`general-purpose`** + detailed prompt | No agent file needed, instructions embedded in the prompt |
| Read-only code work (analysis / review) | **`Explore`** | Prevents accidental file edits |
| Design/planning only | **`Plan`** | Focused on analysis, prevents code changes |
| Implementation that edits files | **Custom type** | Full tool access + specialized instructions |

**Principle:** Define every agent as a file at `.claude/agents/{name}.md`. Even built-in types should have an agent-definition file that records role, principles, and protocol. A file enables reuse across sessions, and explicit team-communication protocol secures collaboration quality.

**Model:** All agents use `model: "opus"`. Always pass `model: "opus"` when calling the Agent tool.

## Agent Definition Structure

```markdown
---
name: agent-name
description: "1–2 sentence role description. List trigger keywords."
---

# Agent Name — one-line role summary

You are a [role] expert in [domain].

## Core Role
1. role1
2. role2

## Work Principles
- principle1
- principle2

## Input / Output Protocol
- Input: [from where, what]
- Output: [to where, what]
- Format: [file format, structure]

## Team Communication Protocol (Agent-Team Mode)
- Message receive: [from whom, what messages]
- Message send: [to whom, what messages]
- Task request: [what kind of work to request from the shared task list]

## Error Handling
- [behavior on failure]
- [behavior on timeout]

## Collaboration
- relationship with other agents
```

## Agent Separation Criteria

| Criterion | Separate | Combine |
|-----------|----------|---------|
| Specialization | Distinct domains → separate | Overlapping domains → combine |
| Parallelism | Can run independently → separate | Strictly sequential → consider combining |
| Context | Large context burden → separate | Light and fast → combine |
| Reusability | Used by other teams → separate | Only this team uses it → consider combining |

## Skill vs Agent Distinction

| Aspect | Skill | Agent |
|--------|-------|-------|
| Definition | Procedural knowledge + tool bundle | Expert persona + behavioral principles |
| Location | `.claude/skills/` | `.claude/agents/` |
| Trigger | User-request keyword matching | Explicit invocation via the Agent tool |
| Size | Small to large (workflow) | Small (role definition) |
| Purpose | "How is it done" | "Who does it" |

A skill is the **procedural guide** an agent consults while doing work.
An agent is the **expert role definition** that uses skills.

## Skill ↔ Agent Linking

Three ways an agent can use a skill:

| Method | Implementation | Fits |
|--------|----------------|------|
| **Skill-tool invocation** | Agent prompt instructs `call /skill-name via the Skill tool` | Skill is an independent workflow the user can call too |
| **Inline in prompt** | Include the skill content directly in the agent definition | Skill is short (≤50 lines) and exclusive to this agent |
| **Reference load** | `Read` the skill's references/ file on demand | Skill content is large and only conditionally needed |

Recommendation: high reuse → Skill tool; exclusive → inline; bulky → reference load.

---

## P7-2 POC note (2026-05-15, Option B)

English POC of the Korean source. Coexists with the `.md` original until real-session dogfood telemetry confirms parity. Cross-references in other docs continue to point at the `.md` file.
