## Experiment 14: Multi-Environment MPO for Autonomous Cloud Detection + Target Pointing

### Goal

Beat baseline on **image mission performance**, not reward. Optimize a new **mission score**:

```text
score = Σ_over_images (image_quality * coverage)
```

Reward may still include penalties, but **primary reported KPI = score**.

***

## Core changes

### 1) Training protocol: environment randomization curriculum

Train across many environments to prevent overfitting to one cloud/orbit realization.

**One experiment cycle**

* Sample env `E_i`
* `5` warmup episodes
* `30` training episodes
* Switch to new env
* Repeat for `N=10` environments

**Total**

* `10 * (5 + 30) = 350` episodes

**Environment randomization**
Randomize at least:

* orbit parameters / initial orbital phase
* cloud fields / cloud motion seeds
* lighting / observation geometry if available
* target distributions

***

### 2) Evaluation protocol

Use **unseen environments only**.

**Baseline eval**

* Run baseline on `5` fresh unseen envs
* Report average:
  * `score`
  * reward
  * images captured
  * mean image quality
  * coverage

**Autopilot eval**

* Use trained model
* Run on the **same unseen eval env set**
* Report same metrics
* Main comparison = **mean score**

***

### 3) Action space redesign

Do **not** let MPO output torque.

Instead:

* MPO outputs **target selection / pointing decision**
* Existing PD controller handles low-level attitude / torque tracking

This makes RL solve the higher-level problem:

> “Which target should I point at now?”

Suggested action space:

* discrete target index + optional “idle / continue tracking”

***

## Reward design

Train with:

```text
reward = α * score_gain
         + β * successful_capture_bonus
         - γ * missed_opportunity
         - δ * instability_penalty
         - ε * torque_penalty
```

But **torque penalty must be small** so it does not dominate.

Suggested starting weights:

* `α = 1.0`
* `β = 0.5`
* `γ = 0.2`
* `δ = 0.1`
* `ε = 0.01`

***

## Hyperparameter sweep

Run 3 variants only:

1. **Conservative**

* lr `3e-4`, batch `256`, horizon `256`

2. **Aggressive**

* lr `1e-3`, batch `512`, horizon `512`

3. **Best-shot**

* lr `5e-4`, batch `512`, horizon `512`, entropy/exploration slightly increased

***

## Implementation plan for Sonnet

1. Add `score` metric and logging
2. Separate **training reward** from **reported score**
3. Implement environment-switching trainer loop
4. Change policy output to target selection
5. Route action through PD pointing controller
6. Build unseen-env eval harness
7. Save best checkpoint by **eval score**, not reward

If you want, I can turn this into a **copy-paste implementation spec / prompt for Sonnet 4.8** next.

Cédric:
ok totally agree. now for the action space. The model should simply output a probability distribution of which target to point at so this would then give the following output: 50 + 1 (targets, shutter cmd) or lets say n_targets + 1. How do we go from gaussian to this 50 array. The probabilites have to add up to one after all in the n_targets array. It is very simple I have done it before in some other ML problem but I dont quite remember how to do it. We dont want this to just be figured out by AI so lets quickly only define this, I think the rest the model should be able to figure out from the codebase context.

Yes — this should be a **categorical policy**, not a Gaussian. For discrete actions, the policy outputs **logits** of size `n_targets + 1`, and those become probabilities with **softmax**, which guarantees they sum to 1. RL policies commonly use **Categorical** for discrete action spaces and **Gaussian** for continuous ones. [\[github.com\]](https://github.com/tsmatz/reinforcement-learning-tutorials/blob/master/02-policy-gradient.ipynb), [\[github.com\]](https://github.com/DLR-RM/stable-baselines3/blob/master/stable_baselines3/common/distributions.py)

```python
import torch
from torch import nn
from torch.distributions import Categorical

class Actor(nn.Module):
    def __init__(self, obs_dim: int, n_actions: int) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, n_actions),  # logits for n_targets + 1 actions
        )

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        return self.net(obs)  # return logits, not softmax
```

Then:

```python
logits = actor(obs)                         # shape: [batch, n_targets + 1]
dist = Categorical(logits=logits)          # internally does softmax
action = dist.sample()                     # training
log_prob = dist.log_prob(action)

probs = torch.softmax(logits, dim=-1)      # only if you want to inspect probabilities
greedy_action = torch.argmax(logits, dim=-1)  # eval/inference if deterministic
```

A good clean definition for your case:

* actions `0 .. n_targets-1` → point to target `i`
* action `n_targets` → shutter / capture now

Important: **prefer `Categorical(logits=logits)` over manually softmaxing first**; it is mathematically equivalent but typically more numerically stable. [\[stackoverflow.com\]](https://stackoverflow.com/questions/60531143/how-to-adapt-ppo-from-continuous-to-discrete-action-spaces), [\[stackoverflow.com\]](https://stackoverflow.com/questions/73289414/i-am-trying-to-implement-ppo-from-stable-baselines3-for-my-custom-environment-i)

So the one-line answer is:

> Replace the Gaussian head `(mu, sigma)` with a single linear layer producing `n_targets + 1` logits, then use a **Categorical** distribution over those logits. [\[github.com\]](https://github.com/tsmatz/reinforcement-learning-tutorials/blob/master/02-policy-gradient.ipynb), [\[github.com\]](https://github.com/DLR-RM/stable-baselines3/blob/master/stable_baselines3/common/distributions.py)

If you want, I can next write the exact **action-space spec text** for Sonnet 4.8 in 5–10 lines.

Cédric:
okay now of course in eval we want the greedy action but how should we choose the non greedy action in training? or how is exploration encouraged?

Use **sampling from the categorical policy during training** and **argmax at eval**. That’s the standard discrete-action replacement for Gaussian exploration in continuous control. The network outputs **logits**; a `Categorical(logits=logits)` turns them into a probability distribution and `sample()` gives the non-greedy action. `argmax(logits)` is the greedy eval action. [\[github.com\]](https://github.com/DLR-RM/stable-baselines3/blob/master/stable_baselines3/common/distributions.py), [\[stackoverflow.com\]](https://stackoverflow.com/questions/73289414/i-am-trying-to-implement-ppo-from-stable-baselines3-for-my-custom-environment-i)

```python
logits = actor(obs)                     # [batch, n_targets + 1]
dist = Categorical(logits=logits)

# training
action = dist.sample()                 # stochastic exploration
log_prob = dist.log_prob(action)
entropy = dist.entropy()

# eval
greedy_action = torch.argmax(logits, dim=-1)
```

### How exploration is encouraged

* **Inherent stochastic sampling:** if target 7 has 0.55 and target 12 has 0.25, both get tried during training. That is your main exploration mechanism. [\[github.com\]](https://github.com/tsmatz/reinforcement-learning-tutorials/blob/master/02-policy-gradient.ipynb), [\[stackoverflow.com\]](https://stackoverflow.com/questions/73289414/i-am-trying-to-implement-ppo-from-stable-baselines3-for-my-custom-environment-i)
* **Entropy bonus:** add `-beta * entropy` to the loss (or equivalently `+ beta * entropy` to the objective) so the policy does not collapse too early to one target. This is the cleanest knob for “more exploration.” [\[github.com\]](https://github.com/DLR-RM/stable-baselines3/blob/master/stable_baselines3/common/distributions.py), [\[github.com\]](https://github.com/XinJingHao/PPO-Discrete-Pytorch)
* **Optional temperature:** divide logits by `T` before the distribution. `T > 1` flattens probabilities → more exploration early in training. [\[github.com\]](https://github.com/LxzGordon/Deep-Reinforcement-Learning-with-pytorch/blob/master/algorithm/policy%20gradient/DDPG_discrete/gumbel_softmax.py), [\[stackoverflow.com\]](https://stackoverflow.com/questions/34240703/what-are-logits-what-is-the-difference-between-softmax-and-softmax-cross-entrop)

### What I’d do here

Use:

* **training:** `Categorical(logits=logits).sample()`
* **eval:** `argmax(logits)`
* **loss:** PPO/MPO objective **plus entropy bonus**
* start with `entropy_coef = 0.01` and decay if needed. [\[github.com\]](https://github.com/DLR-RM/stable-baselines3/blob/master/stable_baselines3/common/distributions.py), [\[github.com\]](https://github.com/XinJingHao/PPO-Discrete-Pytorch)

For your setup, this is enough. No epsilon-greedy needed unless learning gets stuck. [\[github.com\]](https://github.com/tsmatz/reinforcement-learning-tutorials/blob/master/02-policy-gradient.ipynb), [\[stackoverflow.com\]](https://stackoverflow.com/questions/73289414/i-am-trying-to-implement-ppo-from-stable-baselines3-for-my-custom-environment-i)

If you want, I can write the exact 6-line spec for the action head and training/eval selection logic for PyTorch.
