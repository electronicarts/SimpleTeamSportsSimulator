
# STS2: Simple Team Sports Simulator 

STS2 is a multi-agent reinforcement learning environment for generic team sports games. While preserving a gym-like interface, this environment adopts a compact state abstraction which is a lower-dimensional engineered representation of game state rather than frame buffer.

Future updates to this document will incoude additional descriptions of how the game works and will cover its probabilistic model, physics, goal, rules, POMDP, etc.

## Installation

### Python
Requirements: Python 3.6+
```bash
pip install -r requirements.txt
```

### Conda *(recommended)*
```bash 
conda create --name sts2 python=3.6
conda activate sts2

pip install -r requirements.txt  
```

## Quick Start
The following code will launch a 3 vs 3 game with all players as NPC (heuristic AI, driven by probabilistic model). 

```python
from sts2.environment import STS2Environment

env = STS2Environment(num_home_players=3, # Number of home-team players
                      num_away_players=3, # Number of away-team players
                      num_home_agents=0,  # Number of home-team agent players
                      num_away_agents=0,  # Number of away-team agent players
                      with_pygame=True,   # Turn on pygame feature, so that you can `render()`
                      timeout_ticks=1e3)  # Max-length of one round of game
obs, info = env.reset()
while True:
    obs, r, done, info = env.step(None)
    env.render()
```

### Game State
A sample game state (in json format) and corresponding explanation:
```python
{
    # Field geometry, doesn't change.
    'arena_min_x': -9.0,
    'arena_max_x': 9.0,
    'arena_min_z': -18.0,
    'arena_max_z': 18.0,
    'away_net_x': 0.0,
    'away_net_z': -18.0,
    'home_net_x': 0.0,
    'home_net_z': 18.0,
    'home_attack_z': 1.0,
    'away_attack_z': -1.0,

    # Who controls the ball?
    'control_team': 0,  # Tells which team controls the puck; home = 0, away = 1
    'control_index': 0,  # Tells which player controls the puck the index is within the control team.

    'home_score': 0.0,
    'away_score': 0.0,

    # Players location, velocity etc. 
    # AI-controlled players have "_ai_" infix, NPC players have "_npc_" instead.
    'home_players': 1.0,
    'away_players': 1.0,

    'home0_name': 'h_ai_1', # Just a name, used when input actions
    'home0_is_human': 0,
    'home0_pos_x': 8.25,
    'home0_pos_z': -17.25,
    'home0_vel_x': 0.0,
    'home0_vel_z': 0.0,
    'home0_input_x': 1.0, # the 'current' action it is following
    'home0_input_z': -1.0, # the 'current' action it is following
    'home0_action': 'NONE', # the 'current' action it is following
    'home0_action_time': 0, # the remaining action time (action could take more than 1 tick)
    
    'away0_name': 'a_npc_1',
    'away0_is_human': 0,
    'away0_pos_x': -8.25,
    'away0_pos_z': 17.25,
    'away0_vel_x': 0.0,
    'away0_vel_z': 0.0,
    'away0_input_x': -1.0,
    'away0_input_z': 1.0,
    'away0_action': 'NONE',
    'away0_action_time': 0,
    
    # Game information
    # Game phase will have [PRE_GAME, START_PLAY, GAME_ON, STOPPAGE_GOAL, STPPAGE_TIMEUP, GAME_OVER]
    'previous_phase': 'GAME_ON',
    'current_phase': 'GAME_ON',
    'tick': 446
}
```


### Action Space

Action space will each player will have two parts: discrete action and continuous input (image you are playing the game with a xbox controller).
Discrete action: `SHOOT`, `PASS_1`, `PASS_2`, `PASS_3`, `PASS_4`, `PASS_5`, `BLOCK`, `NONE`
Continuous input defines accelerations in *x-z* plane. The accelerationin the game is normalized to 1 so that $[1, 1]$ becomes $[1/\sqrt{2}, 1/\sqrt{2}]$.

A sample action input: 
```python
{
    "h_ai_1": {
        "action": "NONE",
        "input": [1, -1]
    },
    "a_ai_1": {
        "action": "NONE",
        "input": [-1, 1]
    },
}
```

## Contributors:
* Caedmon Somers (EA Vancouver)
* Jason Rupert  (EA Vancouver)
* Yunqi Zhao (EA Digital Platform)
* Igor Borovikov (EA Digital Platform)
* Jiachen Yang (Georgia Institute of Technology)
* Ahmad Beirami (EA Digital Platform)


## Citation
Please consider citing the repository if you use our code:
```latex
@misc{sts2_ea_2020,
    author       = {Caedmon Somers, Jason Rupert, Yunqi Zhao, Igor Borovikov, Jiachen Yang, Ahmad Beirami},
    title        = {{Simple Team Sports Simulator (STS2)}},
    month        = feb,
    year         = 2020,
    version      = {1.0.0},
    publisher    = {Github},
    url          = {https://github.com/electronicarts/SimpleTeamSportsSimulator}
}
```

