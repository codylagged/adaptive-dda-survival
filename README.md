# Comparative analysis of adaptive game difficulty

**Student:** Nandini Parmar
**Guide:** Prof. Vineeta Rathore

**Title:** Comparative Analysis of Adaptive Game Difficulty Using Rule-Based Dynamic Difficulty Adjustment and Epsilon-Greedy Multi-Armed Bandits in a 2D Survival Game.

This repository is a 2D survival game used to compare three difficulty policies:

- fixed easy, medium, and hard
- rule-based dynamic difficulty adjustment
- epsilon-greedy multi-armed bandit

`python main.py` opens the Pygame window. The window sends keyboard movement and attack into `GameEngine` and draws `render_snapshot()`. It does not keep a second copy of the difficulty rules. `python main.py --console` still runs the old scripted demo and appends three rows to the CSV.

The batch results in `data/sessions.csv` were produced by a scripted player. They are not human-subject results. Rounds finished in the window are logged with a session id that starts with `interactive-`, and the statistics screen keeps those rows separate from the experiment bars.

## Setup on Windows

From PowerShell, in this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If activation is blocked by execution policy, run the tools by path instead of activating:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest tests -v
```

`pygame-ce` is installed so the game can `import pygame`. On this machine (CPython 3.15.2), the plain `pygame` 2.6.1 package had no wheel and the source build failed. The simulation modules still do not import pygame themselves.

## Run each piece

| What | Command |
| --- | --- |
| Play the game | `python main.py` |
| Unit tests | `python -m pytest tests -v` |
| Scripted one-session demo | `python main.py --console` |
| Fixed-difficulty check | `python -m experiments.test_fixed` |
| Rule table and 8 live sessions | `python -m experiments.test_rule_based` |
| Bandit formula, explore, exploit | `python -m experiments.test_bandit` |
| Full comparison, fresh CSV logs | `python -m experiments.run_experiments --fresh --sessions 24` |

Run those commands from the project root so `backend` and `experiments` import cleanly.

`python main.py --console` appends three demo rows to `data/sessions.csv`. The comparison command with `--fresh` replaces `data/sessions.csv` and `data/decisions.csv` with that run only. Playing in the window appends a row only when a round actually ends, and that row's session id starts with `interactive-`.

## Layout

```
backend/            simulation, three controllers, reward, CSV logger
frontend/           Pygame window, menu, match, results charts
experiments/        runnable checks and the batch comparison
tests/              pytest suite
data/               sessions.csv, decisions.csv, experiment summary
presentation_2_material/   backend diagrams and slides
presentation_3_material/   frontend screenshots and slides
main.py
```

## What a session does

Each tick lasts 0.1 seconds. The player stands in the centre and attacks the nearest enemy within range. Enemies spawn on the border, walk inward, and strike when they reach attack range. The session ends when health reaches 0 (`health_depleted`) or the tick limit is reached (`time_limit`).

Difficulty changes enemy speed, spawn interval, damage, health, attack range, attack cooldown, and the score multiplier. Presets live in `backend/game_config.py`.

## Three policies

**Fixed.** `FixedDifficulty("easy" | "medium" | "hard")` returns that label forever.

**Rules.** `RuleBasedDDA` reviews the player every `rule_check_interval` ticks. Health under 30% steps the difficulty down one level. A recent damage spike steps it down when health is also below 60%. High health, enough survival time, and a high kill rate step it up. A cooldown (`rule_min_ticks_between_changes`) blocks another change. Thresholds are constructor arguments.

**Bandit.** `EpsilonGreedyBandit` has arms `easy`, `medium`, and `hard`. With probability epsilon it explores uniformly. Otherwise it picks the arm with the largest Q, breaking ties at random. After the reward for that spell of difficulty is known:

```
Q(a) = Q(a) + (R - Q(a)) / N(a)
```

`N(a)` is incremented before the division. Q starts at 0. The same object is kept across bandit sessions in the batch runner so the estimates actually accumulate. Rule sessions and fixed sessions do not share that memory. Each of those sessions starts clean.

## Reward

`backend/reward_system.py` documents every term. The session reward written to `sessions.csv` uses the full time horizon as the survival target. The bandit learns from the same formula applied to each decision window, with the window length as the survival target. Those two numbers are related and they are not the same column. The comparison table uses the session reward for every mode.

The challenge term peaks when about 40% of health has been lost. A full health bar and a death both score worse on that term than a session near the target. Weights are in `RewardWeights`.

## Data columns

`data/sessions.csv` includes session id, experimental mode, selected difficulty, survival time, final score, remaining health, enemies defeated, difficulty changes, reward, and timestamp. Initial difficulty, dominant difficulty, game-over reason, seed, and tick count are stored as well.

`data/decisions.csv` stores every controller decision, the reason, the Q estimate when the controller is the bandit, and the reward observed for the spell of difficulty that decision started.

## Tests

The suite checks:

- fixed difficulty does not change
- rules step up, step down, and honour the cooldown
- a live session steps down when an enemy collapses health
- bandit exploration, exploitation, tie breaking, and the sample-average update
- one bandit update per selection inside a session
- CSV columns and appended rows
- damage, the time limit, health depletion, spawning, and manual control

## Presentation material

After the tests and the batch run, generate the diagrams and the slides:

```powershell
python presentation_2_material\build_presentation.py
```

The slide numbers and the result tables are read from the pytest output and from `data/experiment_summary.json`. Re-run the experiments before regenerating the slides if you change a preset.

Frontend slides, with screenshots taken from the Pygame screens:

```powershell
python presentation_3_material\capture_screenshots.py
python presentation_3_material\build_presentation.py
```

The capture script does not append to the experiment CSV.

## Play

WASD or the arrow keys move. Hold Space to attack the nearest enemy in reach. P or Esc pauses. A round is written to the CSV only when health reaches 0 or the time limit is reached. Leaving from the pause menu does not write a row.

The playable round lasts up to 60 seconds. The batch experiments still use the 20-second default. Enemy presets are the same in both.

```python
engine.manual_control = True
while not engine.game_over:
    engine.set_external_action({"move_x": move_x, "move_y": move_y, "attack": attack})
    engine.step()
    snapshot = engine.render_snapshot()
```

Leave `manual_control` false to keep the scripted survivor used by the experiments.
