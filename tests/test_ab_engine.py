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
