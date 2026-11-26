# Architecture

The simulation lives in `backend/`. The Pygame window in `frontend/` is a viewer and input source. It does not contain a second copy of the difficulty rules.

```
main.py
  |
  +-- frontend/app.py          screen loop, shared bandit
  |     |
  |     +-- session.py         builds Fixed / Rule / Bandit agents
  |     +-- game_screen.py     sends keyboard actions, draws snapshot
  |
  +-- backend/game_engine.py   tick loop, spawning, combat, adaptation
        |
        +-- fixed_difficulty.py
        +-- rule_based_dda.py
        +-- bandit.py
        +-- reward_system.py
        +-- data_logger.py
```

The engine calls `agent.start_session()` once and `agent.decide(metrics)` on decision ticks. The bandit also receives `agent.update(difficulty, reward)` after each window.
