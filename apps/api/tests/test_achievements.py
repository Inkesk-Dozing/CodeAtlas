import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_achievements_catalog():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/achievements/catalog")
        assert response.status_code == 200
        data = response.json()
        assert data["total_available"] >= 9
        assert "pull-shark" in data["achievements"]
        assert "starstruck" in data["achievements"]
        assert "pair-extraordinaire" in data["achievements"]

@pytest.mark.asyncio
async def test_user_achievements():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/achievements/user/octocat")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "octocat"
        assert "completion_rate" in data
        assert len(data["achievements"]) >= 9
        pull_shark = next(a for a in data["achievements"] if a["id"] == "pull-shark")
        assert "current_count" in pull_shark
        assert "progress_percentage" in pull_shark

@pytest.mark.asyncio
async def test_user_achievements_with_overrides():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Override with 130 PRs (should unlock Silver Pull Shark: 128 threshold)
        response = await client.get("/api/v1/achievements/user/testdev?merged_prs=130")
        assert response.status_code == 200
        data = response.json()
        pull_shark = next(a for a in data["achievements"] if a["id"] == "pull-shark")
        assert pull_shark["unlocked"] is True
        assert pull_shark["current_tier"] == "Silver"
        assert pull_shark["next_tier"] == "Gold"
        assert pull_shark["remaining_for_next_tier"] == (1024 - 130)

@pytest.mark.asyncio
async def test_ai_achievement_context():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/achievements/ai-context/torvalds")
        assert response.status_code == 200
        data = response.json()
        assert "<github_achievements user=\"torvalds\"" in data["prompt_context"]
        assert "### 🏆 GitHub Achievement Profile: @torvalds" in data["markdown_card"]
        assert len(data["actionable_next_steps"]) > 0
        assert data["raw_stats"]["username"] == "torvalds"

