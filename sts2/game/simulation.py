# Copyright (C) 2020 Electronic Arts Inc.  All rights reserved.

import pandas


class GameHistoryEntry:
    def __init__(self, tick, state, player_identity_list, player_policy_list, player_action_list,
                 player_value_estimate_list, player_reward_list):
        self.tick = tick
        self.state = state
        self.player_identity_list = player_identity_list
        self.player_policy_list = player_policy_list
        self.player_action_list = player_action_list
        self.player_reward_list = player_reward_list
        self.player_value_estimate_list = player_value_estimate_list

    def Show(self):
        print('tick:', self.tick, 'state:', self.state, 'identity:', self.player_identity_list,
              'policy:', self.player_policy_list, 'action:', self.player_action_list, 'reward:',
              self.player_reward_list, 'value:', self.player_value_estimate_list)


class GameEvent:
    def __init__(self, tick, event_type, source_player_name, target_player_name):
        self.tick = tick
        self.event_type = event_type
        self.source_player_name = source_player_name
        self.target_player_name = target_player_name


class GameEventHistory:
    def __init__(self):
        self.event_list = []

    def AddEvent(self, e):
        self.event_list.append(e)

    def EventMatches(self, e, event_type=None, min_tick=None, max_tick=None,
                     source_player_name=None, target_player_name=None):
        if event_type is not None and e.event_type != event_type:
            return False

        if min_tick is not None and e.tick < min_tick:
            return False

        if max_tick is not None and e.tick > max_tick:
            return False

        if source_player_name is not None and e.source_player_name != source_player_name:
            return False

        if target_player_name is not None and e.target_player_name != target_player_name:
            return False

        return True

    def FindEvents(self, event_type=None, min_tick=None, max_tick=None, source_player_name=None,
                   target_player_name=None):
        l = []
        for e in self.event_list:
            if self.EventMatches(e, event_type, min_tick, max_tick, source_player_name,
                                 target_player_name):
                l.append(e)

        return l

    def FindMostRecentEvent(self, event_type=None, min_tick=None, max_tick=None,
                            source_player_name=None, target_player_name=None):
        for e in self.event_list[-1::-1]:
            if self.EventMatches(e, event_type, min_tick, max_tick, source_player_name,
                                 target_player_name):
                return e
        return None

    def EventListToDataFrame(self, l=None):
        if l is None:
            l = self.event_list

        df = pandas.DataFrame(columns=['tick', 'event_type', 'source_player', 'target_player'])
        i = 0
        for e in l:
            df.loc[i, 'tick'] = e.tick
            df.loc[i, 'event_type'] = e.event_type
            df.loc[i, 'source_player'] = e.source_player_name
            df.loc[i, 'target_player'] = e.target_player_name
            i += 1

        return df


class Simulation:
    NUM_AGENTS_INVOLVED = 0  # must override in derived class
    WIN_REWARD = 1.0
    LOSS_REWARD = -1.0

    def __init__(self, players, verbosity=0):
        self.players = players
        self.verbosity = max(0, verbosity)
        self.tick = 0
        self.player_identity_list = [None] * len(players)  # subclass should fill
        self.game_state_history = []
        self.game_state_vector = None
        self._WipePlayerActionsAndRewardsForThisTick()
        self.game_event_history = GameEventHistory()

    def update(self, record_game_state=True):
        if self.verbosity > 1:
            self.ShowState()

        self._WipePlayerActionsAndRewardsForThisTick()
        self.CustomTick()
        if record_game_state:
            self._AddGameStateHistoryForThisTick()
        self.tick += 1

    def Simulate(self):
        # this method need not be overridden and can be called from a different context if needed

        if self.verbosity:
            print('Simulation.Simulate() verbosity', self.verbosity)

        while not self.IsSimulationComplete():
            self.update()

        if self.verbosity:
            self.ShowState()

    def _WipePlayerActionsAndRewardsForThisTick(self):
        self.player_action_list = [None] * len(self.players)
        self.player_reward_list = [0.0] * len(self.players)
        self.player_policy_list = [None] * len(self.players)
        self.player_value_estimate_list = [0.0] * len(self.players)

    def _AddGameStateHistoryForThisTick(self):
        h = GameHistoryEntry(self.tick, self.GetHashableGameStateVector(),
                             self.player_identity_list, self.player_policy_list,
                             self.player_action_list, self.player_value_estimate_list,
                             self.player_reward_list)
        self.game_state_history.append(h)

    def CustomTick(self):
        # override this method with simulation specific logic
        pass

    def IsSimulationComplete(self):
        # should return true if simulation is complete
        raise NotImplementedError

    def ShowState(self):
        # helper method for debugging
        raise NotImplementedError

    def GetHashableGameStateVector(self):
        # should return game state *from before this tick*
        # *must be hashable for easy table generation, etc, best way is to convert to tuple*
        raise NotImplementedError
