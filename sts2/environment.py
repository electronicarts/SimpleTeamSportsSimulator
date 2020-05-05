# Copyright (C) 2020 Electronic Arts Inc.  All rights reserved.

import random
import numpy as np

from sts2.client_adapter import ClientAdapter
from sts2.game.game import Game
from sts2.game.game_state import Action
from sts2.game.player import SimplePlayer
from sts2.game.pygame_interface import PygameInterface, INTERFACE_SETTINGS
from sts2.game.rules import STANDARD_GAME_RULES
from sts2.game.settings import TeamSide


class AgentPlayer(SimplePlayer):
    def __init__(self, name, team_side):
        super().__init__(name, team_side)

    def custom_think(self, game, verbosity):
        discrete_action, continuous_input = game.client_adapter.unpack_action(self)
        if discrete_action is None:
            discrete_action = Action.NONE
        else:
            discrete_action = getattr(Action, discrete_action)
        self.SetAction(game, discrete_action)
        self.SetInput(game, continuous_input)


def get_game(num_home_players, num_away_players, num_home_agents, num_away_agents,
             timeout_ticks, verbosity=0):
    # Prepare players
    home_players = []
    for i in range(1, num_home_agents + 1):
        home_players.append(AgentPlayer('h_ai_' + str(i), TeamSide.HOME))
    for i in range(num_home_agents + 1, num_home_players + 1):
        home_players.append(SimplePlayer('h_npc_' + str(i), TeamSide.HOME))

    away_players = []
    for i in range(1, num_away_agents + 1):
        away_players.append(AgentPlayer('a_ai_' + str(i), TeamSide.AWAY))
    for i in range(num_away_agents + 1, num_away_players + 1):
        away_players.append(SimplePlayer('a_npc_' + str(i), TeamSide.AWAY))

    # Rules
    rules = STANDARD_GAME_RULES
    rules.max_tick = int(timeout_ticks)

    return Game(home_players + away_players, rules, verbosity=verbosity,
                client_adapter_cls=ClientAdapter)


def get_pygame(game):
    return PygameInterface(game, INTERFACE_SETTINGS)


class STS2Environment(object):

    def __init__(
            self,
            *,
            num_home_players=3,
            num_away_players=3,
            num_home_agents=0,
            num_away_agents=0,
            with_pygame=False,
            timeout_ticks=1e10):
        self.game = get_game(num_home_players, num_away_players, num_home_agents, num_away_agents,
                             timeout_ticks)

        self.pygame = get_pygame(self.game) if with_pygame else None

    def seed(self, seed):
        random.seed(seed)
        np.random.seed(seed)

    def reset(self):
        observation = self.game.client_adapter.send_state()
        return observation, ''

    def render(self):
        if self.pygame:
            self.pygame.HandleGameReplayFrame()

    def update(self):
        if self.pygame:
            self.pygame.update()
        else:
            self.game.update()

    def step(self, action):
        reward = None
        info = None

        self.game.client_adapter.receive_action(action)

        self.update()

        observation = self.game.client_adapter.send_state()
        done = observation.get('current_phase') == "GAME_OVER"
        return observation, reward, done, info
