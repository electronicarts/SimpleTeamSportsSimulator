# Copyright (C) 2020 Electronic Arts Inc.  All rights reserved.

import numpy as np


def format_state(game):
    # Fields supported by the game directly
    state = {field: game.state.series[field] for field in game.state.series.index}

    # Additional custom fields:
    state['tick'] = game.tick
    state['teams'] = []  # Just a convenience mapper player name => index
    for team in game.team_players:
        players = [player.name for player in team]
        state['teams'].append(players)

    state['prefixes'] = {}  # Another convenience mapper player name => prefix into data columns
    for player in game.players:
        state['prefixes'][player.name] = game.state.GetPlayerFieldPrefix(player)

    # Scoring probabilities for all the players, computed by the game.
    state['score_prob'] = {}
    for player in game.players:
        prob = game.PlayerShot(player, True, 0)
        state['score_prob'][player.name] = prob

    return state


class ClientAdapter(object):
    def __init__(self, game):
        self.game = game

        self.action = None
        self.state = None

    def receive_action(self, action):
        """ Custom handling. """
        self.action = action if action else {}

        # Check if the external app wants the game to load a specific state
        load_state = self.action.get("load_state")
        if load_state is not None:
            for key in self.game.state.series.index:
                self.game.state.SetField(key, load_state[key])

    def unpack_action(self, player):
        player_dct = self.action.get(player.name, {})
        # TODO: Here is an opportunity to run all kind of checks on the action and input.
        discrete_action = player_dct.get('action', None)
        continuous_input = np.array(player_dct.get('input', np.zeros(2)))
        return discrete_action, continuous_input

    def send_state(self):
        self.state = format_state(self.game)
        return self.state
