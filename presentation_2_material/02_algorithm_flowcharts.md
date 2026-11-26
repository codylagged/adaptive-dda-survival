# Algorithm flow

## Fixed

```
start
  |
  v
always return the chosen level
```

## Rule-based DDA

```
every rule_check_interval ticks
  |
  +-- cooldown not expired? --> stay
  |
  +-- health < 30%? --> step down
  |
  +-- recent damage high and health < 60%? --> step down
  |
  +-- health high AND survival long AND kill rate high? --> step up
  |
  +-- otherwise stay
```

## Epsilon-greedy bandit

```
on decision tick
  |
  +-- with probability epsilon: explore (uniform)
  |
  +-- else: exploit (highest Q, ties broken randomly)
  |
  v
play that difficulty for check_interval ticks
  |
  v
observe reward R for the window
  |
  v
Q(a) <- Q(a) + (R - Q(a)) / N(a)
```
