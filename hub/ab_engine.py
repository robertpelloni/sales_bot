"""
Project Sirens - Multi-Armed Bandit A/B Testing Engine
Dynamically balances exploration and exploitation across sales frameworks
(e.g., Pattern Interrupt, Challenger, Consultative Selling) by evaluating
historical conversion rates (lead flags and positive staff feedback scores)
from the CRM interactions database.
"""

import math
import random
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.future import select
from sqlalchemy import func, case
from hub.database import Interaction, AsyncSession


DEFAULT_FRAMEWORKS = [
    "Pattern Interrupt Cold-Open",
    "Challenger Sales Framework",
    "Consultative Problem-Solver",
    "Assumptive Close Narrative"
]


class MultiArmedBanditEngine:
    """
    Implements Thompson Sampling, Epsilon-Greedy (with decay), and Upper Confidence Bound (UCB1)
    algorithms to dynamically route customer interactions to the highest converting retail sales frameworks.
    """

    def __init__(
        self,
        epsilon: float = 0.20,
        decay_rate: float = 0.99,
        min_epsilon: float = 0.05,
        default_method: str = "thompson"
    ):
        # Epsilon rate: random exploration probability
        self.initial_epsilon = epsilon
        self.epsilon = epsilon
        self.decay_rate = decay_rate
        self.min_epsilon = min_epsilon
        self.default_method = default_method
        self.default_frameworks = list(DEFAULT_FRAMEWORKS)
        # In-memory overrides or custom prior adjustments
        self.manual_priors: Dict[str, Dict[str, float]] = {}

    def decay_epsilon(self) -> float:
        """Decays epsilon by decay_rate down to min_epsilon threshold."""
        if self.epsilon > 0.0:
            self.epsilon = max(self.min_epsilon, self.epsilon * self.decay_rate)
        return self.epsilon

    def reset_parameters(self, epsilon: Optional[float] = None) -> None:
        """Resets exploration parameters and clears manual priors."""
        self.epsilon = epsilon if epsilon is not None else self.initial_epsilon
        self.manual_priors.clear()

    async def get_framework_performance(self, session: AsyncSession) -> Dict[str, Dict[str, Any]]:
        """
        Aggregates interaction statistics per sales framework:
        total trials, qualified leads (successes), feedback score sums, and conversion rates.
        """
        # Query total count and positive lead conversions grouped by framework
        stmt = (
            select(
                Interaction.sales_framework,
                func.count(Interaction.id).label("total_interactions"),
                func.sum(case((Interaction.is_lead == True, 1), else_=0)).label("leads_count"),
                func.sum(case((Interaction.feedback_score > 0, 1), else_=0)).label("positive_ratings")
            )
            .group_by(Interaction.sales_framework)
        )

        res = await session.execute(stmt)
        rows = res.all()

        stats: Dict[str, Dict[str, Any]] = {}
        for fw in self.default_frameworks:
            stats[fw] = {
                "trials": 0,
                "leads": 0,
                "positive_ratings": 0,
                "conversion_rate": 0.0,
                "ci_lower": 0.0,
                "ci_upper": 0.0,
                "alpha": 1.0 + self.manual_priors.get(fw, {}).get("alpha", 0.0),
                "beta": 1.0 + self.manual_priors.get(fw, {}).get("beta", 0.0)
            }

        for row in rows:
            fw_name = row.sales_framework
            if not fw_name or fw_name == "Unknown":
                continue

            total = int(row.total_interactions or 0)
            leads = int(row.leads_count or 0)
            pos_ratings = int(row.positive_ratings or 0)

            # Combined reward: each qualified lead counts as 1.0, positive rating counts as 0.5
            successes = leads + (0.5 * pos_ratings)
            failures = max(0.0, total - successes)

            conversion_rate = round((leads / total) * 100.0, 1) if total > 0 else 0.0

            # 95% Wilson confidence interval approximation for conversion rate
            ci_margin = 0.0
            if total > 0:
                p = leads / total
                # Standard error approximation
                ci_margin = 1.96 * math.sqrt((p * (1.0 - p)) / total) if total > 1 else 0.5
            ci_lower = max(0.0, round((conversion_rate / 100.0 - ci_margin) * 100.0, 1))
            ci_upper = min(100.0, round((conversion_rate / 100.0 + ci_margin) * 100.0, 1))

            base_prior_alpha = self.manual_priors.get(fw_name, {}).get("alpha", 0.0)
            base_prior_beta = self.manual_priors.get(fw_name, {}).get("beta", 0.0)

            stats[fw_name] = {
                "trials": total,
                "leads": leads,
                "positive_ratings": pos_ratings,
                "conversion_rate": conversion_rate,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper,
                "alpha": 1.0 + successes + base_prior_alpha,
                "beta": 1.0 + failures + base_prior_beta
            }

        return stats

    def sample_thompson(self, stats: Dict[str, Dict[str, Any]]) -> str:
        """
        Samples from Beta(alpha, beta) for each arm and selects the highest sampled value.
        Guarantees theoretical Bayesian regret bounds and continuous adaptation.
        """
        best_score = -1.0
        selected_arm = self.default_frameworks[0]

        for arm, data in stats.items():
            alpha = max(0.001, float(data.get("alpha", 1.0)))
            beta = max(0.001, float(data.get("beta", 1.0)))
            # Sample Beta distribution via standard random.betavariate
            try:
                sampled_val = random.betavariate(alpha, beta)
            except Exception:
                sampled_val = 0.5

            if sampled_val > best_score:
                best_score = sampled_val
                selected_arm = arm

        return selected_arm

    def select_epsilon_greedy(self, stats: Dict[str, Dict[str, Any]]) -> str:
        """
        With probability epsilon, explore randomly.
        With probability 1 - epsilon, exploit the arm with the highest empirical conversion rate.
        Applies exploration decay automatically on each evaluation.
        """
        if random.random() < self.epsilon:
            self.decay_epsilon()
            return random.choice(list(stats.keys()))

        self.decay_epsilon()
        best_rate = -1.0
        best_arm = self.default_frameworks[0]
        for arm, data in stats.items():
            rate = float(data.get("conversion_rate", 0.0))
            if rate > best_rate:
                best_rate = rate
                best_arm = arm

        return best_arm

    def select_ucb1(self, stats: Dict[str, Dict[str, Any]]) -> str:
        """
        Upper Confidence Bound (UCB1) algorithm:
        Score = empirical_mean + sqrt(2 * ln(total_trials) / arm_trials).
        Guarantees that unvisited or rarely explored arms are tested early,
        while converging to optimal conversion rates asymptotically.
        """
        total_trials = sum(int(d.get("trials", 0)) for d in stats.values())
        if total_trials == 0:
            return random.choice(list(stats.keys()))

        best_score = -1.0
        best_arm = self.default_frameworks[0]

        for arm, data in stats.items():
            trials = int(data.get("trials", 0))
            # Any arm with zero trials receives infinite priority to ensure initial exploration
            if trials == 0:
                return arm

            mean_reward = float(data.get("conversion_rate", 0.0)) / 100.0
            exploration_bonus = math.sqrt((2.0 * math.log(total_trials)) / trials)
            ucb_score = mean_reward + exploration_bonus

            if ucb_score > best_score:
                best_score = ucb_score
                best_arm = arm

        return best_arm

    async def allocate_next_framework(self, session: AsyncSession, method: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Selects the next sales framework to employ based on historical bandit performance.
        Supports 'thompson', 'epsilon_greedy', and 'ucb1'.
        Returns selected framework name and current stats dictionary.
        """
        algo = method or self.default_method
        stats = await self.get_framework_performance(session)

        if algo == "epsilon_greedy":
            chosen = self.select_epsilon_greedy(stats)
        elif algo == "ucb1":
            chosen = self.select_ucb1(stats)
        else:
            chosen = self.sample_thompson(stats)

        return chosen, stats


bandit_engine = MultiArmedBanditEngine()
