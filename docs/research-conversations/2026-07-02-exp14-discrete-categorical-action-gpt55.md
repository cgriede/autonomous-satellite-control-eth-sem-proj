# Research conversation — Exp 14 discrete action head (GPT 5.5)

**Date:** 2026-07-02  
**Context:** Work conversation with GPT 5.5 while scoping Exp 14 (`ml_mpo_multienv_target_select`).  
**Pipeline doc:** [14-mpo-multienv-target-select.md](../experiments/pipeline/1-built/14-mpo-multienv-target-select.md)

Raw exchange preserved for the categorical-policy design decision. Experiment charter (multi-env training, mission score, eval protocol) lives in the pipeline Phase 0 doc.

---

## Operator (Cédric)

> ok totally agree. now for the action space. The model should simply output a probability distribution of which target to point at so this would then give the following output: 50 + 1 (targets, shutter cmd) or lets say n_targets + 1. How do we go from gaussian to this 50 array. The probabilites have to add up to one after all in the n_targets array. It is very simple I have done it before in some other ML problem but I dont quite remember how to do it. We dont want this to just be figured out by AI so lets quickly only define this, I think the rest the model should be able to figure out from the codebase context.

## GPT 5.5

Yes — this should be a **categorical policy**, not a Gaussian. For discrete actions, the policy outputs **logits** of size `n_targets + 1`, and those become probabilities with **softmax**, which guarantees they sum to 1. RL policies commonly use **Categorical** for discrete action spaces and **Gaussian** for continuous ones.

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

Action semantics:

* actions `0 .. n_targets-1` → point to target `i`
* action `n_targets` → shutter / capture now

Important: **prefer `Categorical(logits=logits)` over manually softmaxing first**; it is mathematically equivalent but typically more numerically stable.

One-line answer:

> Replace the Gaussian head `(mu, sigma)` with a single linear layer producing `n_targets + 1` logits, then use a **Categorical** distribution over those logits.

---

## Operator (Cédric)

> okay now of course in eval we want the greedy action but how should we choose the non greedy action in training? or how is exploration encouraged?

## GPT 5.5

Use **sampling from the categorical policy during training** and **argmax at eval**. That's the standard discrete-action replacement for Gaussian exploration in continuous control.

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

* **Inherent stochastic sampling:** if target 7 has 0.55 and target 12 has 0.25, both get tried during training.
* **Entropy bonus:** add `-beta * entropy` to the loss (or equivalently `+ beta * entropy` to the objective) so the policy does not collapse too early to one target.
* **Optional temperature:** divide logits by `T` before the distribution. `T > 1` flattens probabilities → more exploration early in training.

### Recommended setup

* **training:** `Categorical(logits=logits).sample()`
* **eval:** `argmax(logits)`
* **loss:** PPO/MPO objective **plus entropy bonus**
* start with `entropy_coef = 0.01` and decay if needed.

No epsilon-greedy needed unless learning gets stuck.

---

## Operator note (mission score definition)

> The score is: `np.sum([image.quality * image.coverage for image in image_captures])`
>
> The images are stored per `SimulationStateSeries` with `dt` as the index; most are zero because there is a limited image budget.


can we model the action interaction like this such that when we get a very even distribution (or maybe just another second boolean would be easier so n_targets + shutter + move. we move towards the target the NN has the highest action probability, but we only send the torque to the reaction wheel if the model sends the move command. imagine it like this. me as a human I would control the satellite like this: I set the target on a navball. then I press the key to move towards the direction. It might be that I want to observe on the way so not go full speed, so I only press the key shortly and afterwards let the spacecraft turn slowly into the direction of the target i set, when i apply move / power again I can go faster until the controller wants to slow down. imagine it like a control algorithm that can be turned on or off. I think in kerbal space program they make you hold position if you have the stability system on but for the NN I think this version could avctually better where it continues moving. what do you think?