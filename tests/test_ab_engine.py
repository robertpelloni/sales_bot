import pytest
from hub.ab_engine import MultiArmedBanditEngine, DEFAULT_FRAMEWORKS


def test_bandit_initialization():
    engine = MultiArmedBanditEngine(epsilon=0.15)
    assert engine.epsilon == 0.15
    assert len(engine.default_frameworks) == len(DEFAULT_FRAMEWORKS)


def test_thompson_sampling_selection():
    engine = MultiArmedBanditEngine()
    stats = {
        "LowArm": {"alpha": 1.0, "beta": 100.0, "conversion_rate": 1.0},
        "HighArm": {"alpha": 100.0, "beta": 1.0, "conversion_rate": 99.0}
    }

    # HighArm has an overwhelming Beta(100, 1) prior vs Beta(1, 100)
    selections = [engine.sample_thompson(stats) for _ in range(50)]
    assert selections.count("HighArm") > 45


def test_epsilon_greedy_selection():
    # Epsilon = 0 (pure exploitation)
    greedy_engine = MultiArmedBanditEngine(epsilon=0.0)
    stats = {
        "ArmA": {"conversion_rate": 12.0},
        "ArmB": {"conversion_rate": 45.0},
        "ArmC": {"conversion_rate": 5.0}
    }
    for _ in range(20):
        chosen = greedy_engine.select_epsilon_greedy(stats)
        assert chosen == "ArmB"

    # Epsilon = 1.0 (pure exploration)
    explore_engine = MultiArmedBanditEngine(epsilon=1.0)
    selections = {explore_engine.select_epsilon_greedy(stats) for _ in range(50)}
    assert len(selections) > 1


def test_decay_epsilon():
    engine = MultiArmedBanditEngine(epsilon=0.20, decay_rate=0.5, min_epsilon=0.06)
    assert engine.decay_epsilon() == 0.10
    # Decaying again would hit 0.05, but min_epsilon is 0.06
    assert engine.decay_epsilon() == 0.06
    assert engine.decay_epsilon() == 0.06

    # Test reset restores initial epsilon
    engine.reset_parameters()
    assert engine.epsilon == 0.20


def test_ucb1_selection():
    engine = MultiArmedBanditEngine()
    # If one arm has 0 trials, UCB1 must prioritize it immediately
    stats = {
        "ArmTested": {"trials": 100, "conversion_rate": 80.0},
        "ArmUnexplored": {"trials": 0, "conversion_rate": 0.0}
    }
    assert engine.select_ucb1(stats) == "ArmUnexplored"

    # With all arms visited, higher empirical mean + exploration bonus wins
    stats_visited = {
        "ArmWeak": {"trials": 100, "conversion_rate": 10.0},
        "ArmStrong": {"trials": 100, "conversion_rate": 90.0}
    }
    assert engine.select_ucb1(stats_visited) == "ArmStrong"


@pytest.mark.asyncio
async def test_ab_config_and_reset_endpoints():
    from httpx import AsyncClient, ASGITransport
    import base64
    from hub.main import app

    auth_str = "admin:password"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    headers = {"Authorization": f"Basic {b64_auth}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=headers) as ac:
        # Test getting bandit allocations and config
        res = await ac.get("/api/ab/allocations")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert "config" in data

        # Test updating bandit config via API
        update_res = await ac.post("/api/ab/config", json={
            "epsilon": 0.12,
            "decay_rate": 0.95,
            "min_epsilon": 0.02,
            "default_method": "ucb1"
        })
        assert update_res.status_code == 200
        assert update_res.json()["config"]["epsilon"] == 0.12
        assert update_res.json()["config"]["default_method"] == "ucb1"

        # Test selecting framework with default method (ucb1)
        select_res = await ac.post("/api/ab/select_framework")
        assert select_res.status_code == 200
        assert select_res.json()["method"] == "ucb1"
        assert "selected_framework" in select_res.json()

        # Test resetting bandit parameters
        reset_res = await ac.post("/api/ab/reset")
        assert reset_res.status_code == 200
        assert reset_res.json()["status"] == "success"
