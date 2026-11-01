# CodeAtlas GitHub Achievement Tracker & AI Context API

The **CodeAtlas Achievement Engine** tracks, estimates, and forecasts GitHub profile achievements (mirroring community analyzers like `gitbadgecheck.vercel.app`), providing both standard REST JSON endpoints and token-budgeted AI prompt contexts (`<github_achievements>`) designed for integration into external AI copilots, agents, and developer assistants.

---

## 📊 Architectural Flow & Integration Map

```mermaid
flowchart TD
    subgraph SCM_Layer["GitHub Public Data Layer"]
        UserEvents["GitHub Public Events & PR History"]
        Discussions["Repository Discussions Accepted Answers"]
        Stars["Repository Star Thresholds"]
    end

    subgraph CodeAtlas_Engine["CodeAtlas Achievement & Forecast Engine"]
        Tracker["Achievement Calculator & Tier Solver"]
        Catalog["Canonical Registry (9 Active & Legacy Badges)"]
        AIPackager["AI Context Packager & Token Budgeter"]
    end

    subgraph Client_AI_Apps["Consumer Ecosystem"]
        Dashboard["Web UI / Dashboard (GitBadgeCheck Mirror)"]
        ExternalAI["External AI Apps / LLM Copilots (Your App)"]
    end

    UserEvents --> Tracker
    Discussions --> Tracker
    Stars --> Tracker
    Catalog --> Tracker
    Tracker --> AIPackager
    Tracker -->|GET /api/v1/achievements/user/{user}| Dashboard
    AIPackager -->|GET /api/v1/achievements/ai-context/{user}| ExternalAI
```

---

## 🏆 Supported GitHub Achievements & Tier Matrix

| Badge ID | Badge Name | Category | Unlock Metric | Tiers & Thresholds | Optimization Tips |
|---|---|---|---|---|---|
| `pull-shark` | **Pull Shark** 🦈 | Active | Merged Pull Requests | **Base**: 2 \| **Bronze**: 16 \| **Silver**: 128 \| **Gold**: 1,024 | Squash/rebase merges across public repositories count. |
| `starstruck` | **Starstruck** 🌟 | Active | Top Repo Star Count | **Base**: 16 \| **Bronze**: 128 \| **Silver**: 512 \| **Gold**: 4,096 | Maintain open-source libraries, CLI utilities, or awesome lists. |
| `pair-extraordinaire` | **Pair Extraordinaire** 👯 | Active | Co-Authored Merged Commits | **Base**: 1 \| **Bronze**: 10 \| **Silver**: 24 \| **Gold**: 48 | Include git trailer: `Co-authored-by: Name <email>`. |
| `galaxy-brain` | **Galaxy Brain** 🧠 | Active | Accepted Discussion Answers | **Base**: 2 \| **Bronze**: 8 \| **Silver**: 16 \| **Gold**: 32 | Provide answers in repo Discussions marked as accepted by author. |
| `quickdraw` | **Quickdraw** ⚡ | Active | Rapid Issue/PR Closes | **Base**: 1 ($\le 5$ min close) | Open and close an issue or PR within 5 minutes. |
| `yolo` | **YOLO** 🎯 | Active | Unreviewed Merges | **Base**: 1 (No review merge) | Merge a PR on a personal repo without branch protection checks. |
| `public-sponsor` | **Public Sponsor** 💖 | Active | Active GitHub Sponsorships | **Base**: 1 Sponsor | Sponsor an open-source contributor with public visibility enabled. |
| `arctic-code-vault` | **Arctic Code Vault** ❄️ | Legacy | 02/02/2020 Snapshot Commits | **Legacy**: 1 (Historical) | Preserved for contributors active before Feb 2020 snapshot. |
| `mars-2020` | **Mars 2020** 🚀 | Legacy | NASA Mars Helicopter Libs | **Legacy**: 1 (Historical) | Preserved for contributors to open source libs used by JPL Ingenuity. |

---

## 🚀 API Reference & Usage Guide

Base URL: `http://localhost:8000/api/v1/achievements` (or your deployed API gateway).

### 1. Retrieve Global Achievements Catalog
* **Endpoint**: `GET /api/v1/achievements/catalog`
* **Purpose**: Inspect all 9 canonical badges, tier thresholds, multipliers, and descriptions.

#### Example Request:
```bash
curl -X GET "http://localhost:8000/api/v1/achievements/catalog"
```

#### Example Response (Excerpt):
```json
{
  "catalog_version": "2026.1",
  "provider": "CodeAtlas GitBadgeCheck Engine",
  "total_available": 9,
  "achievements": {
    "pull-shark": {
      "id": "pull-shark",
      "name": "Pull Shark",
      "category": "active",
      "description": "Merged pull requests into repositories.",
      "icon": "🦈",
      "metric_name": "merged_prs",
      "tiers": [
        {"tier": "Base", "threshold": 2, "multiplier": "x1"},
        {"tier": "Bronze", "threshold": 16, "multiplier": "x2"},
        {"tier": "Silver", "threshold": 128, "multiplier": "x3"},
        {"tier": "Gold", "threshold": 1024, "multiplier": "x4"}
      ]
    }
  }
}
```

---

### 2. Track User Achievement Progress & Live Forecasts
* **Endpoint**: `GET /api/v1/achievements/user/{username}`
* **Purpose**: Returns the full profile breakdown: current tier, next unlock target, progress percentage, remaining contributions needed, and estimated developer XP.
* **Optional Query Overrides** (for testing or manual sync):
  - `merged_prs`: integer
  - `max_stars`: integer
  - `coauthored_commits`: integer
  - `accepted_answers`: integer

#### Example Request:
```bash
curl -X GET "http://localhost:8000/api/v1/achievements/user/octocat"
```

#### Example Response (Excerpt):
```json
{
  "username": "octocat",
  "total_unlocked": 7,
  "total_achievements": 9,
  "completion_rate": 77.8,
  "active_badges": 6,
  "legacy_badges": 1,
  "highest_rank_badge": "Pull Shark (Silver)",
  "estimated_xp": 2650,
  "achievements": [
    {
      "id": "pull-shark",
      "name": "Pull Shark",
      "category": "active",
      "icon": "🦈",
      "unlocked": true,
      "current_tier": "Silver",
      "current_multiplier": "x3",
      "current_count": 130,
      "next_tier": "Gold",
      "next_threshold": 1024,
      "remaining_for_next_tier": 894,
      "progress_percentage": 0.2,
      "tips": "Submit and merge PRs across public repositories. Squash or rebase merges count.",
      "tiers": [
        {"tier": "Base", "threshold": 2, "multiplier": "x1", "unlocked": true},
        {"tier": "Bronze", "threshold": 16, "multiplier": "x2", "unlocked": true},
        {"tier": "Silver", "threshold": 128, "multiplier": "x3", "unlocked": true},
        {"tier": "Gold", "threshold": 1024, "multiplier": "x4", "unlocked": false}
      ]
    }
  ]
}
```

---

### 3. AI-Optimized Context Endpoint (For Your AI App)
* **Endpoint**: `GET /api/v1/achievements/ai-context/{username}`
* **Purpose**: Specifically structured to be consumed by external AI applications (ChatGPT, Claude, LangChain, custom AI copilot). It returns:
  1. `prompt_context`: Token-optimized XML block ready to paste directly into LLM system or user prompts.
  2. `markdown_card`: Clean GitHub Flavored Markdown card ready for chat render.
  3. `actionable_next_steps`: Ranked list of steps the user should take right now to unlock their next badge tier.

#### Example Request:
```bash
curl -X GET "http://localhost:8000/api/v1/achievements/ai-context/octocat"
```

#### Example Response:
```json
{
  "prompt_context": "<github_achievements user=\"octocat\" unlocked=\"7/9\" xp=\"2650\">\n  <status highest_rank=\"Pull Shark (Silver)\" completion_rate=\"77.8%\">\n  <unlocked_badges>\n    <badge id=\"pull-shark\" name=\"Pull Shark\" tier=\"Silver\" count=\"130\" progress=\"0.2%\" />\n    <badge id=\"pair-extraordinaire\" name=\"Pair Extraordinaire\" tier=\"Bronze\" count=\"12\" progress=\"14.3%\" />\n  </unlocked_badges>\n  <recommended_next_actions>\n    <action priority=\"1\">Advance Pair Extraordinaire to Silver: Needs 12 more pair extraordinaire contributions. Action: Add 'Co-authored-by: Name <email>' git trailer in commit messages for merged PRs.</action>\n    <action priority=\"2\">Unlock Galaxy Brain: Needs 2 galaxy brain events. Action: Provide helpful answers in repository Discussions where maintainers mark answers accepted.</action>\n  </recommended_next_actions>\n</github_achievements>",
  "markdown_card": "### 🏆 GitHub Achievement Profile: @octocat\n- **Completion**: 7/9 badges (77.8%) | **XP**: 2650\n- **Highest Rank**: Pull Shark (Silver)\n\n#### Unlocked Badges\n- 🦈 Pull Shark [Silver] (130 count)\n- 👯 Pair Extraordinaire [Bronze] (12 count)\n\n#### Next Targets to Unlock\n- 🧠 Galaxy Brain (Requires 2 count)",
  "raw_stats": {
    "username": "octocat",
    "total_unlocked": 7,
    "total_achievements": 9,
    "estimated_xp": 2650,
    "completion_rate": 77.8
  },
  "actionable_next_steps": [
    "Advance Pair Extraordinaire to Silver: Needs 12 more co-authored commits.",
    "Unlock Galaxy Brain: Needs 2 accepted discussion answers."
  ]
}
```

---

## 🤖 How to Integrate into Your External AI App

### Python (LangChain / OpenAI / Anthropic)
```python
import httpx
from openai import OpenAI

client = OpenAI()

async def get_developer_achievements_for_ai(username: str) -> str:
    async with httpx.AsyncClient() as http:
        resp = await http.get(f"http://localhost:8000/api/v1/achievements/ai-context/{username}")
        data = resp.json()
        return data["prompt_context"]

# Inject directly into your LLM prompt
prompt_context = await get_developer_achievements_for_ai("octocat")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": f"You are a developer career coach. Here is the user's verified GitHub achievement profile:\n{prompt_context}"},
        {"role": "user", "content": "What should I work on today to level up my open source profile?"}
    ]
)
print(response.choices[0].message.content)
```

### TypeScript / Node.js
```typescript
import axios from 'axios';

interface AIAchievementContext {
  prompt_context: string;
  markdown_card: string;
  actionable_next_steps: string[];
}

export async function fetchAIAchievements(username: string): Promise<AIAchievementContext> {
  const { data } = await axios.get<AIAchievementContext>(
    `http://localhost:8000/api/v1/achievements/ai-context/${username}`
  );
  return data;
}
```

