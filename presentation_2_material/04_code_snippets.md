# Code snippets

## Bandit update

```python
def update(self, action: str, reward: float) -> float:
    self.counts[action] += 1
    previous = self.estimates[action]
    updated = previous + (float(reward) - previous) / self.counts[action]
    self.estimates[action] = updated
    return updated
```

## Rule evaluation order

```python
if ticks_since_change < self.min_ticks_between_changes:
    return self._stay(current, "cooldown")
if health_ratio < self.low_health:
    return self._shift(current, -1, "health_below_threshold")
```

## Engine adaptation tick

if the agent adapts and the tick is a decision tick, the engine records the window reward and asks the agent for the next difficulty.
