# Copyright (C) 2020 Electronic Arts Inc.  All rights reserved.


import pandas
import numpy

from sts2.game.settings import TeamSide


class Action:
    SHOOT = "SHOOT"
    PASS_1 = "PASS_1"
    PASS_2 = "PASS_2"
    PASS_3 = "PASS_3"
    PASS_4 = "PASS_4"
    PASS_5 = "PASS_5"
    PASSES = [PASS_1, PASS_2, PASS_3, PASS_4, PASS_5]
    BLOCK = "BLOCK"
    STUNNED = "STUNNED"
    NONE = "NONE"
    ACTION_LIST = [SHOOT, PASS_1, PASS_2, PASS_3, PASS_4, PASS_5, BLOCK, STUNNED, NONE]
    NUM = len(ACTION_LIST)


class GameState:
    TICK = "tick"

    CURRENT_PHASE = 'current_phase'
    PREVIOUS_PHASE = 'previous_phase'

    ARENA_MIN_X = 'arena_min_x'
    ARENA_MAX_X = 'arena_max_x'
    ARENA_MIN_Z = 'arena_min_z'
    ARENA_MAX_Z = 'arena_max_z'

    HOME = TeamSide.GetName(TeamSide.HOME)
    AWAY = TeamSide.GetName(TeamSide.AWAY)
    TEAMSIDE_PREFIXES = [HOME, AWAY]

    # per-team properites
    TEAM_NET_X = '_net_x'
    TEAM_NET_Z = '_net_z'
    TEAM_SCORE = '_score'
    TEAM_ATTACK_Z = '_attack_z'
    TEAM_PLAYERS = '_players'

    # per-player properties
    PLAYER_NAME = "_name"
    PLAYER_IS_HUMAN = "_is_human"
    PLAYER_POS_X = "_pos_x"
    PLAYER_POS_Z = "_pos_z"
    PLAYER_VEL_X = "_vel_x"
    PLAYER_VEL_Z = "_vel_z"
    PLAYER_INPUT_X = "_input_x"
    PLAYER_INPUT_Z = "_input_z"
    PLAYER_ACTION = "_action"
    PLAYER_ACTION_TIME = "_action_time"

    CONTROL_TEAM = "control_team"
    CONTROL_INDEX = "control_index"

    def __init__(self, game):
        self.game = game
        self.series = pandas.Series()
        self.Init()

    def Init(self):
        # static values that don't change
        # WARNING: assumes home and away don't switch sides
        self.SetField(self.ARENA_MIN_X, self.game.arena.min_x, init=True)
        self.SetField(self.ARENA_MAX_X, self.game.arena.max_x, init=True)
        self.SetField(self.ARENA_MIN_Z, self.game.arena.min_z, init=True)
        self.SetField(self.ARENA_MAX_Z, self.game.arena.max_z, init=True)

        self.SetField(self.CONTROL_TEAM, TeamSide.HOME, init=True)
        self.SetField(self.CONTROL_INDEX, 0, init=True)

        # set up fields for team values
        for teamside, sidename in zip(TeamSide.TEAMSIDES, self.TEAMSIDE_PREFIXES):
            self.SetTeamField(teamside, self.TEAM_NET_X, self.game.arena.net_position[teamside][0],
                              init=True)
            self.SetTeamField(teamside, self.TEAM_NET_Z, self.game.arena.net_position[teamside][1],
                              init=True)
            self.SetTeamField(teamside, self.TEAM_ATTACK_Z,
                              numpy.sign(self.game.arena.net_position[teamside][1]), init=True)
            self.SetTeamField(teamside, self.TEAM_SCORE, 0, init=True)
            self.SetTeamField(teamside, self.TEAM_PLAYERS, len(self.game.team_players[teamside]),
                              init=True)

        # set up fields for player values
        for player in self.game.players:
            self.SetPlayerField(player, self.PLAYER_NAME, player.name, init=True)
            self.SetPlayerField(player, self.PLAYER_IS_HUMAN, int(player.IsHuman()), init=True)
            self.SetPlayerPosition(player, numpy.zeros(2))
            self.SetPlayerVelocity(player, numpy.zeros(2))
            self.SetPlayerInput(player, numpy.zeros(2))
            self.SetPlayerField(player, self.PLAYER_ACTION, Action.NONE, init=True)
            self.SetPlayerField(player, self.PLAYER_ACTION_TIME, 0, init=True)

    def GetSnapshot(self):  # MAS, generic OpenAI-like use
        return {field: self.series[field] for field in self.series.index}

    def SetFromSnapshot(self, json_data):  # MAS, used for MCTS load game state
        """No asserts, assuming json_data matches the columns."""
        for field, value in json_data:
            self.series[field] = value

    def GetField(self, field):
        return self.series[field]

    def SetField(self, field, value, init=False):
        assert (init or field in self.series)
        self.series[field] = value

    def GetTeamFieldPrefix(self, teamside):
        return TeamSide.GetName(teamside)

    def GetTeamFieldName(self, teamside, field):
        return self.GetTeamFieldPrefix(teamside) + field

    def GetTeamField(self, teamside, field):
        return self.GetField(self.GetTeamFieldName(teamside, field))

    def SetTeamField(self, teamside, field, value, init=False):
        field_name = self.GetTeamFieldPrefix(teamside) + field
        assert (init or field_name in self.series)
        self.series[field_name] = value

    def GetPlayerFieldPrefix(self, player):
        team_index = self.game.team_players[player.team_side].index(player)
        return TeamSide.GetName(player.team_side) + str(team_index)

    def GetPlayerField(self, player, field):
        return self.series[self.GetPlayerFieldPrefix(player) + field]

    def SetPlayerField(self, player, field, value, init=False):
        field_name = self.GetPlayerFieldPrefix(player) + field

        # ensure we are not adding incorrect fields through assignment
        assert (init or field_name in self.series)

        self.series[field_name] = value

    def GetPlayerPosition(self, player):
        prefix = self.GetPlayerFieldPrefix(player)
        return numpy.array(
            [self.series[prefix + self.PLAYER_POS_X], self.series[prefix + self.PLAYER_POS_Z]])

    def SetPlayerPosition(self, player, pos):
        prefix = self.GetPlayerFieldPrefix(player)
        self.series[prefix + self.PLAYER_POS_X] = pos[0]
        self.series[prefix + self.PLAYER_POS_Z] = pos[1]

    def GetPlayerVelocity(self, player):
        prefix = self.GetPlayerFieldPrefix(player)
        return numpy.array(
            [self.series[prefix + self.PLAYER_VEL_X], self.series[prefix + self.PLAYER_VEL_Z]])

    def SetPlayerVelocity(self, player, pos):
        prefix = self.GetPlayerFieldPrefix(player)
        self.series[prefix + self.PLAYER_VEL_X] = pos[0]
        self.series[prefix + self.PLAYER_VEL_Z] = pos[1]

    def GetPlayerInput(self, player):
        prefix = self.GetPlayerFieldPrefix(player)
        return numpy.array(
            [self.series[prefix + self.PLAYER_INPUT_X], self.series[prefix + self.PLAYER_INPUT_Z]])

    def SetPlayerInput(self, player, pos):
        prefix = self.GetPlayerFieldPrefix(player)
        self.series[prefix + self.PLAYER_INPUT_X] = pos[0]
        self.series[prefix + self.PLAYER_INPUT_Z] = pos[1]
