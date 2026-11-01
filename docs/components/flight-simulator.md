# CodeAtlas Flight Simulator Component Specification

## Purpose
The CodeAtlas Flight Simulator provides an in-browser, zero-friction virtual sandbox that trains new developers on Git workflows, repository mechanics, and monorepo collaboration. It demystifies Git commands, pull request lifecycles, automated CI bot reviews, and upstream merge conflict resolution in a safe, risk-free environment before contributors submit changes to upstream production repositories.

## System Dependencies
- **WebContainer / WASM Virtual File System**: Client-side execution of virtual Git operations and file edits.
- **FastAPI (`routers/flight_simulator.py`)**: Mission catalog orchestration, simulated pull request processing, automated review bot evaluation, and progress persistence.
- **AI Feedback Engine (`services/flight_reviewer.py`)**: Multi-persona reviewer generating realistic, actionable code review comments and CI check diagnostics.
- **Zustand (`flightStore.ts`) & React UI (`apps/web`)**: Interactive terminal, step-by-step mission checklist, visual commit graph tree, and PR simulation modal.

## Big-O Algorithmic Complexity

| Operation | Time Complexity | Space Complexity | Description |
|---|---|---|---|
| Virtual Git Command Execution | $O(F)$ | $O(F)$ | Executing virtual `add`, `commit`, `branch`, or `checkout` across $F$ files in virtual memory |
| Merge Conflict Detection | $O(L_1 + L_2)$ | $O(L_1 + L_2)$ | Line-by-line three-way diff between base, local, and remote files with $L_1, L_2$ lines |
| AI Review Bot Evaluation | $O(T_{\text{diff}})$ | $O(T_{\text{diff}})$ | Parsing patch token count $T_{\text{diff}}$ and evaluating against mission acceptance rules |
| Mission State Verification | $O(1)$ | $O(1)$ | Validating virtual commit tree against cryptographic target state hash |

## Architectural Modules & Execution Flows

```
┌─────────────────────────────────┐
│     Mission Track Selector      │
│  (Beginner, Branching, Conflicts│
└─────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐      ┌─────────────────────────────┐
│  In-Browser Virtual Git Shell   │ ───▶ │ Visual Commit Tree Renderer │
│  (Fork, Branch, Commit, Rebase) │      │ (Live Interactive DAG View) │
└─────────────────────────────────┘      └─────────────────────────────┘
                 │                                      │
                 ▼                                      ▼
┌─────────────────────────────────┐      ┌─────────────────────────────┐
│   Simulated Pull Request Bot    │ ───▶ │ Automated CI Diagnostic Run │
│ (Linters, Style, Code Reviews)  │      │ (Tests, Types, Status Checks)│
└─────────────────────────────────┘      └─────────────────────────────┘
                 │                                      │
                 ▼                                      ▼
┌─────────────────────────────────┐      ┌─────────────────────────────┐
│ Conflict Resolution Sandbox     │ ───▶ │ Credential Unlock Gate      │
│ (3-Way Merge Markers & Fixing)  │      │ (Awards Ed25519 Badges)     │
└─────────────────────────────────┘      └─────────────────────────────┘
```

### 1. In-Browser Virtual Git Shell
- Simulates standard Git CLI commands (`git status`, `git add`, `git commit`, `git checkout -b`, `git rebase`, `git merge`) in local browser memory.
- Synchronizes with a real-time visual Directed Acyclic Graph (DAG) rendering the active branch pointer, commit nodes, and HEAD state.

### 2. Simulated Pull Request & Bot Review Workflow
- Allows learners to open simulated pull requests against a mock upstream monorepo.
- Triggers simulated GitHub Actions workflows (ESLint, TypeCheck, Unit Tests) with educational failure explanations.
- AI Review Bot comments with constructive feedback on commit message hygiene, modularity, and test coverage.

### 3. Upstream Conflict Resolution Mission
- Dynamically injects an intentional merge conflict from the upstream branch into the contributor's working branch.
- Renders standard Git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) in a Monaco editor with interactive "Accept Current", "Accept Incoming", or "Accept Both" controls.
- Confirms successful conflict resolution, stage, and final merge commit before unlocking the "Git Flight Certified" achievement.

