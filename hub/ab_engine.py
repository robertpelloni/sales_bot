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
    Implements Thompson Sampling and Epsilon-Greedy algorithms to dynamically
    route customer interactions to the highest converting retail sales frameworks.
    """

    def __init__(self, epsilon: float = 0.20):
        # Epsilon rate: 20% random exploration, 80% exploitation of best empirical arm
        self.epsilon = epsilon
        self.default_frameworks = list(DEFAULT_FRAMEWORKS)

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
                "alpha": 1.0,  # Prior for Beta distribution (successes + 1)
                "beta": 1.0    # Prior for Beta distribution (failures + 1)
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

            stats[fw_name] = {
                "trials": total,
                "leads": leads,
                "positive_ratings": pos_ratings,
                "conversion_rate": conversion_rate,
                "alpha": 1.0 + successes,
                "beta": 1.0 + failures
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
        """
        if random.random() < self.epsilon:
            return random.choice(list(stats.keys()))

        best_rate = -1.0
        best_arm = self.default_frameworks[0]
        for arm, data in stats.items():
            rate = float(data.get("conversion_rate", 0.0))
            if rate > best_rate:
                best_rate = rate
                best_arm = arm

        return best_arm

    async def allocate_next_framework(self, session: AsyncSession, method: str = "thompson") -> Tuple[str, Dict[str, Any]]:
        """
        Selects the next sales framework to employ based on historical bandit performance.
        Returns selected framework name and current stats dictionary.
        """
        stats = await self.get_framework_performance(session)

        if method == "epsilon_greedy":
            chosen = self.select_epsilon_greedy(stats)
        else:
            chosen = self.sample_thompson(stats)

        return chosen, stats


bandit_engine = MultiArmedBanditEngine()
