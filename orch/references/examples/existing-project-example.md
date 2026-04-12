# Example: Adding a Feature to an Existing Project

Demonstrates the `new-feature-existing` pipeline for extending an existing codebase.

## User request

```
"Add a notification system to this project. Users should get in-app notifications 
and email digests."
```

## Stage 1: Dispatch

Dispatch detects an existing project:
- Source code files found: `src/`, `package.json`, `tsconfig.json`
- Git history exists with 47 commits
- User says "this project" (existing codebase signal)
- Routes to `new-feature-existing` pipeline

```bash
python ${SKILL_DIR}/scripts/run.py init-run --pipeline new-feature-existing
```

Output:
```json
{
  "run_id": "20260412-140000-b3c4",
  "run_dir": "harness-output/runs/20260412-140000-b3c4",
  "pipeline": "new-feature-existing"
}
```

Message to user: "I see this is an existing TypeScript project. I'll start by exploring the codebase, then gather requirements for the notification feature, design the architecture extension, implement it, and generate tests. Starting with codebase exploration."

## Stage 2: Pipeline execution

### Steps 0-3: ex (automatic exploration)

All four `ex` stages run automatically without user interaction:

- **ex:scan** — discovers project structure, entry points, build system (npm/TypeScript)
- **ex:detect** — identifies tech stack: Express.js, TypeScript, PostgreSQL, Redis
- **ex:analyze** — maps component relationships: auth module, user module, project module, API routes
- **ex:map** — infers architecture: layered monolith, repository pattern, event-based internal communication

Produces: EX-SM-001, EX-TS-001, EX-CR-001, EX-AI-001

These artifacts now provide context for the downstream skills — re:elicit knows what already exists, arch:design knows the current architecture to extend.

### Step 4: re:elicit

RE skill receives EX artifacts as upstream context. It knows the existing system and focuses the dialogue on the new feature:

- Turn 1: "Your project already has a user module with sessions and a Redis cache. For notifications, do you want to extend the existing Redis pub/sub for real-time, or add a separate message queue?"
  - User: "Extend Redis pub/sub, keep it simple"
- Turn 2: "For email digests, batch frequency?"
  - User: "Daily at 9am user's local time"

### Step 5: re:spec

Produces requirements scoped to the notification feature only.

### Step 6: arch:design

Architecture skill sees both EX artifacts (existing architecture) and RE artifacts (new requirements):

- Proposes adding a NotificationService component alongside existing services
- Uses existing Redis pub/sub for real-time delivery
- Adds a scheduled worker for email digests using existing Bull queue library
- No new infrastructure needed

### Step 7: impl:generate

Implementation skill generates code that follows existing patterns:
- Uses existing repository pattern for notification storage
- Follows existing Express middleware patterns for WebSocket upgrade
- Extends existing user preferences for notification settings

### Step 8: qa:generate

QA generates test cases that integrate with existing test framework (Jest, detected by ex).

## Completion

```bash
python ${SKILL_DIR}/scripts/run.py complete --run 20260412-140000-b3c4
```

Total steps: 9 (4 automatic ex + 5 feature development)
User dialogue turns: ~4 (re:elicit 2 + arch:design 2)
