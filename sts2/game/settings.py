# Copyright (C) 2020 Electronic Arts Inc.  All rights reserved.

class TeamSide:
    HOME = 0
    AWAY = 1
    TEAMSIDES = [HOME, AWAY]
    NUM_TEAMSIDES = len(TEAMSIDES)

    @staticmethod
    def GetName(side):
        return ["home", "away", "BOTHTEAM"][side]

    @staticmethod
    def Opposite(side):
        return TeamSide.AWAY - side


class GamePhase:
    PRE_GAME = "PRE_GAME"
    START_PLAY = "START_PLAY"
    GAME_ON = "GAME_ON"
    STOPPAGE_GOAL = "STOPPAGE_GOAL"
    STOPPAGE_TIMEUP = "STOPPAGE_TIMEUP"
    GAME_OVER = "GAME_OVER"


class STS2Event:
    GAME_START = "GAME_START"
    GAME_END = "GAME_END"
    GOAL = "GOAL"
    SHOT = "SHOT"
    MISSED_SHOT = "MISSED_SHOT"
    SHOT_BLOCK = "SHOT_BLOCK"
    CHECK = "CHECK"
    PASS = "PASS"
    PASS_COMPLETE = "PASS_COMPLETE"
    PASS_INTERCEPT = "PASS_INTERCEPT"
    GAIN_CONTROL = "GAIN_CONTROL"


# for RL policy
class Outputs:
    LS_0 = 0
    LS_1 = 1
    LS_2 = 2
    LS_3 = 3
    LS_4 = 4
    LS_5 = 5
    LS_6 = 6
    LS_7 = 7
    LS__ = 8
    LS_LIST = [LS_0, LS_1, LS_2, LS_3, LS_4, LS_5, LS_6, LS_7, LS__]
    SKATE = 9
    SHOOT = 10
    PASS = 11
    OUTPUT_LIST = LS_LIST + [SKATE, SHOOT, PASS]
    NUM = len(OUTPUT_LIST)
