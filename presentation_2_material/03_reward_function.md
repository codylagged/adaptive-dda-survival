# Reward function

pressure = 1 - remaining_health / max_health

R =
  w_survival * min(survival_time / target, 1)
  + w_health * (remaining_health / max_health)
  + w_score * tanh(score / score_scale)
  + w_kills * tanh(defeats / kill_scale)
  + w_challenge * clip(1 - |pressure - 0.40| / 0.50, 0, 1)
  - death_penalty if the player died

The challenge term peaks when about 40% of health has been lost. Full health and death both score poorly on that term. Weights live in `RewardWeights`.
