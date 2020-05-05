# Copyright (C) 2020 Electronic Arts Inc.  All rights reserved.

from sts2.game.game_state import GameState
from sts2.game.settings import STS2Event
from sts2.game.simulation import GameEvent


class Control:
    def __init__(self, game):
        self.game = game

    def Reset(self, game):
        self.game = game

    def GiveControl(self, player):
        index = self.game.team_players[player.team_side].index(player)
        self.game.state.SetField(GameState.CONTROL_INDEX, index)
        self.game.state.SetField(GameState.CONTROL_TEAM, player.team_side)
        self.game.game_event_history.AddEvent(
            GameEvent(self.game.tick, STS2Event.GAIN_CONTROL, player.name, ''))

    def GetControl(self):
        control_team = int(self.game.state.GetField(GameState.CONTROL_TEAM))
        control_player = int(self.game.state.GetField(GameState.CONTROL_INDEX))
        return self.game.team_players[control_team][control_player]

    def HasControl(self, player):
        return player is self.GetControl()
