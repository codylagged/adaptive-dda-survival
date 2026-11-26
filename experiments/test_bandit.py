"""Walk through exploration, exploitation, and the sample-average update.

Usage:

    python -m experiments.test_bandit
"""

from __future__ import annotations

from backend.bandit import EpsilonGreedyBandit


def main() -> None:
    print("Sample-average update")
    bandit = EpsilonGreedyBandit(epsilon=0.0, seed=0)
    print("  start Q(medium)=0, N(medium)=0")
    first = bandit.update("medium", 1.0)
    print(f"  after R=1.0: Q={first:.4f} N={bandit.counts['medium']}  (0 + (1-0)/1 = 1)")
    second = bandit.update("medium", 0.0)
    print(f"  after R=0.0: Q={second:.4f} N={bandit.counts['medium']}  (1 + (0-1)/2 = 0.5)")
    if abs(first - 1.0) > 1e-9 or abs(second - 0.5) > 1e-9:
        raise SystemExit("Update did not match Q + (R - Q) / N")
    if bandit.estimates["easy"] != 0.0 or bandit.estimates["hard"] != 0.0:
        raise SystemExit("Update changed an arm that was not selected")

    print()
    print("Exploitation (epsilon = 0) with Q(hard) highest")
    greedy = EpsilonGreedyBandit(epsilon=0.0, seed=1)
    greedy.estimates["easy"] = 0.2
    greedy.estimates["medium"] = 0.4
    greedy.estimates["hard"] = 0.8
    choices = [greedy.select_action() for _ in range(8)]
    print("  selections:", ", ".join(f"{action}/{kind}" for action, kind in choices))
    if any(action != "hard" or kind != "exploit" for action, kind in choices):
        raise SystemExit("Epsilon 0 did not exploit the best arm")

    print()
    print("Exploration (epsilon = 1) over 90 draws")
    explorer = EpsilonGreedyBandit(epsilon=1.0, seed=5)
    draws = [explorer.select_action()[0] for _ in range(90)]
    counts = {arm: draws.count(arm) for arm in explorer.actions}
    print(f"  counts: {counts}")
    print(f"  explore={explorer.exploration_count} exploit={explorer.exploitation_count}")
    if explorer.exploitation_count != 0 or any(counts[arm] == 0 for arm in explorer.actions):
        raise SystemExit("Epsilon 1 did not explore across the three arms")

    print()
    print("Learning trace, epsilon = 0.1, one reward per arm pulled")
    learner = EpsilonGreedyBandit(epsilon=0.1, seed=9)
    # Scripted rewards: easy is dull, medium is best, hard is poor.
    # This trace only checks that Q moves. It is not a game result.
    scripted_reward = {"easy": 0.35, "medium": 0.80, "hard": 0.15}
    for step in range(1, 16):
        action, kind = learner.select_action()
        updated = learner.update(action, scripted_reward[action])
        print(
            f"  step {step:02d}  {kind:8} {action:6}  "
            f"Q[{action}]={updated:.3f}  N={dict(learner.counts)}"
        )
    ranking = sorted(learner.estimates, key=learner.estimates.get, reverse=True)
    print(f"  estimate ranking after 15 scripted pulls: {ranking}")
    print(f"  Q = { {arm: round(learner.estimates[arm], 3) for arm in learner.actions} }")


if __name__ == "__main__":
    main()
