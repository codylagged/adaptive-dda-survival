# Test cases and results

The pytest suite covers:

- Fixed difficulty does not change under pressure
- Rule-based steps down on low health, steps down on a damage spike, steps up on strong performance, and respects the cooldown
- Bandit sample-average update, pure exploitation, and pure exploration
- CSV logger columns and append behaviour
- Engine damage, time limit, and manual control

Sample batch results (scripted player) are in `data/sessions.csv` and `data/experiment_summary.json`. Interactive rounds from the window use session ids that start with `interactive-` and are kept separate on the statistics screen.
