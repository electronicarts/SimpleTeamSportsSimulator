# Copyright (C) 2020 Electronic Arts Inc.  All rights reserved.

import numpy

from sts2.game.game_state import GameState, Action
from sts2.game.rules import Rules
from sts2.game.settings import TeamSide


class Player(object):

    def __init__(self, name, team_side):
        self.name = name
        self.team_side = team_side

    def Reset(self, game):
        self.ClearActionAndTime(game)
        self.ClearMotion(game)

    def IsHuman(self):
        return False

    def ClearMotion(self, game):
        self.SetPosition(game, numpy.zeros(2))
        self.SetVelocity(game, numpy.zeros(2))
        self.SetInput(game, numpy.zeros(2))

    def ClearActionAndTime(self, game):
        self.SetAction(game, Action.NONE)
        self.SetActionTime(game, 0)

    def GetPosition(self, game):
        return game.state.GetPlayerPosition(self)

    def SetPosition(self, game, position):
        game.state.SetPlayerPosition(self, position)

    def GetVelocity(self, game):
        return game.state.GetPlayerVelocity(self)

    def SetVelocity(self, game, velocity):
        game.state.SetPlayerVelocity(self, velocity)

    def GetInput(self, game):
        return game.state.GetPlayerInput(self)

    def SetInput(self, game, input):
        game.state.SetPlayerInput(self, input)

    def GetAction(self, game):
        return game.state.GetPlayerField(self, GameState.PLAYER_ACTION)

    def SetAction(self, game, action):
        game.state.SetPlayerField(self, GameState.PLAYER_ACTION, action)

    def GetActionTime(self, game):
        return game.state.GetPlayerField(self, GameState.PLAYER_ACTION_TIME)

    def SetActionTime(self, game, action_time):
        game.state.SetPlayerField(self, GameState.PLAYER_ACTION_TIME, action_time)

    def GetAttackingNetPos(self, game):
        return game.arena.net_position[TeamSide.Opposite(self.team_side)]

    def GetAttackDir(self, game):
        return numpy.sign(self.GetAttackingNetPos(game)[1])

    def RunVelocityMotionModel(self, game, desired_vel, action):
        rules = game.rules
        position = self.GetPosition(game)
        velocity = self.GetVelocity(game)

        accel_mag = numpy.linalg.norm(desired_vel)
        if accel_mag > rules.max_accel:
            desired_vel = desired_vel / accel_mag

        # scale desired acc by distance between normalized velocity and normalized acceleration
        norm_vel = velocity / rules.max_vel

        if action != Action.NONE:
            desired_vel = norm_vel

        actual_accel = (desired_vel - norm_vel) * rules.max_accel

        velocity += actual_accel

        vel_mag = numpy.linalg.norm(velocity)
        if vel_mag > rules.max_vel:
            velocity = velocity * rules.max_vel / vel_mag

        position += velocity

        self.SetPosition(game, position)
        self.SetVelocity(game, velocity)

    def RunMotionModel(self, game, input, action_frames):
        # acceleration model
        # i = i * (|i| - v . i)
        rules = game.rules
        position = self.GetPosition(game)
        velocity = self.GetVelocity(game)

        accel_mag = numpy.linalg.norm(input)
        if accel_mag > 1.0:  # rules.max_accel:
            input = input / accel_mag

        if game.rules.motion_model == Rules.MotionModel.ACCELERATION_MODEL:
            # scale desired acc by distance between normalized velocity and normalized acceleration
            norm_vel = velocity / rules.max_vel

            if action_frames:
                input = numpy.zeros(2)

            actual_accel = input * (
                    numpy.linalg.norm(input) - norm_vel.dot(input)) * rules.max_accel

            velocity += actual_accel
        elif game.rules.motion_model == Rules.MotionModel.PAC_MAN_MODEL:
            velocity = input

        vel_mag = numpy.linalg.norm(velocity)
        if vel_mag > rules.max_vel:
            velocity = velocity * rules.max_vel / vel_mag

        position += velocity

        self.SetPosition(game, position)
        self.SetVelocity(game, velocity)

    def IHaveControl(self, game):
        return game.control.GetControl() is self

    def GetTeamIndex(self, game):
        return game.team_players[self.team_side].index(self)

    def Stun(self, game, t):
        if t > 0:
            self.SetAction(game, Action.STUNNED)
            self.SetActionTime(game, t)

    def ResponseTime(self, game, t):
        self.SetActionTime(game, max(self.GetActionTime(game), t))

    def OnPlayStart(self, game):
        self.Reset(game)

    def RectifyInput(self, game):
        input = self.GetInput(game)
        input_mag = numpy.linalg.norm(input)
        if input_mag > 0.01:
            input = input / input_mag
        # force onto [-1,0,1] for each dimension
        input = numpy.round(input)
        self.SetInput(game, input)

    def Think(self, game, verbosity):
        self.SetAction(game, Action.NONE)

        self.SetActionTime(game, max(0, self.GetActionTime(game) - 1))
        self.SetInput(game, numpy.zeros(2))

        if self.GetActionTime(game) > 0:
            if verbosity: print(self.name,
                                "response time for %d more ticks" % self.GetActionTime(game))
            # stunned will show up in the training data so we know now to train on these samples
            self.SetAction(game, Action.STUNNED)
        else:
            self.custom_think(game, verbosity)

        self.RectifyInput(game)

    def custom_think(self, game, verbosity):
        pass


class SimplePlayer(Player):
    SHOOT_ARENA_DIST = 0.3
    SHOT_CHANCE = 0.3
    PASS_CHANCE = 0.8
    PLAY_RANDOMLY = False
    if PLAY_RANDOMLY:
        RANDOM_SHOT_CHANCE = 0.03
        RANDOM_PASS_CHANCE = 0.03
        RANDOM_SKATE_CHANCE = 0.9
    else:
        RANDOM_SHOT_CHANCE = 0.0
        RANDOM_PASS_CHANCE = 0.0
        RANDOM_SKATE_CHANCE = 0.0

    def __init__(self, name, team_side):
        super(SimplePlayer, self).__init__(name, team_side)

    def custom_think(self, game, verbosity):
        super(SimplePlayer, self).custom_think(game, verbosity)

        if verbosity: print('simple', self.name, 'thinking:', end=" ")
        control_player = game.control.GetControl()
        net_pos = self.GetAttackingNetPos(game)

        avg_teammate_pos = numpy.zeros(2)
        for teammate in game.team_players[self.team_side]:
            avg_teammate_pos += teammate.GetPosition(game)
        avg_teammate_pos /= len(game.team_players[self.team_side])
        center_delta = self.GetPosition(game) - avg_teammate_pos
        # IB: avoid division by zero:
        norm = numpy.linalg.norm(center_delta)
        center_dir = center_delta / (norm + 1e-10)

        if control_player is self:
            net_delta = net_pos - self.GetPosition(game)
            # move towards net
            self.SetInput(game, net_delta)
            net_dist = numpy.linalg.norm(net_delta)

            shoot_dist = self.SHOOT_ARENA_DIST * numpy.linalg.norm(
                numpy.array(game.arena.arena_size))
            shot_chance = game.PlayerShot(self, True, 0)
            # shoot if close
            shoot = self.RANDOM_SHOT_CHANCE == 0.0 and net_dist < shoot_dist and shot_chance > self.SHOT_CHANCE
            shoot = shoot or numpy.random.random() < self.RANDOM_SHOT_CHANCE
            if shoot:
                if verbosity:   print('shooting because %f < %f' % (net_dist, shoot_dist))
                self.SetAction(game, Action.SHOOT)
            else:
                lowest_net_dist = numpy.linalg.norm(self.GetPosition(game) - net_pos)
                for teammate, action in zip(game.team_players[self.team_side], Action.PASSES):
                    if teammate is self:
                        continue
                    if teammate.GetAction(game) == Action.STUNNED:
                        continue
                    net_dist = numpy.linalg.norm(teammate.GetPosition(game) - net_pos)
                    pass_chance = game.PlayerPass(self, teammate, True, 0)
                    should_pass = self.RANDOM_PASS_CHANCE == 0.0 and net_dist < lowest_net_dist and pass_chance > self.PASS_CHANCE
                    should_pass = should_pass or numpy.random.random() < self.RANDOM_PASS_CHANCE
                    if should_pass:
                        self.SetAction(game, action)
                        lowest_net_dist = net_dist
                        if verbosity: print('best pass net dist is', net_dist, self.action)

            if self.GetAction(game) == Action.NONE:
                if verbosity: print('move towards net')

        elif control_player:
            if numpy.random.random() < self.RANDOM_SKATE_CHANCE:
                self.SetInput(game, numpy.zeros(2))
            elif control_player.team_side == self.team_side:
                if verbosity: print('move up areana')
                # just move up arena
                dest = (self.GetAttackingNetPos(game) + self.GetPosition(game)) * 0.5 + center_dir * \
                       game.arena.arena_size[0] * 0.5
                input = dest - self.GetPosition(game)
                self.SetInput(game, input)
            else:
                # if the player is among m-closest to the controller, approach to gain possession
                M = 2  # TODO: move to the future game config file
                rank = game.players_by_distance_to_controller_by_team[self.team_side][self.name]
                if rank < M:
                    if verbosity: print('move towards to opposing controller')
                    target_pos = control_player.GetPosition(game)
                else:
                    # move towards opposing controller
                    if verbosity: print('move towards MIDWAY point to opposing controller')
                    target_pos = (control_player.GetPosition(
                        game) + control_player.GetAttackingNetPos(game)) * 0.5
                delta = target_pos - self.GetPosition(game)
                self.SetInput(game, delta)
        else:
            if verbosity: print("shouldn't reach here", control_player)


class HumanKeyboardPlayer(Player):
    def __init__(self, name, team_side):
        super(HumanKeyboardPlayer, self).__init__(name, team_side)

    def custom_think(self, game, verbosity):
        super(HumanKeyboardPlayer, self).custom_think(game, verbosity)

        i = input(self.name + '> ')
        if i == 'exit':
            sys.exit()

        accel_map = {'q': [-1.0, 1.0], 'w': [0.0, 1.0], 'e': [1.0, 1.0],
                     'a': [-1.0, 0.0], 'd': [1.0, 0.0],
                     'z': [-1.0, -1.0], 'x': [0.0, -1.0], 'c': [1.0, -1.0]}
        accel = accel_map.get(i, [0.0, 0.0])
        self.SetInput(game, numpy.array(accel))
        if i is ' ':
            self.SetAction(game, Action.SHOOT)
        elif i is '1':
            self.SetAction(game, Action.PASS_1)
        elif i is '2':
            self.SetAction(game, Action.PASS_2)
        elif i is '3':
            self.SetAction(game, Action.PASS_3)
        elif i is '4':
            self.SetAction(game, Action.PASS_4)
        elif i is '5':
            self.SetAction(game, Action.PASS_5)
        elif i is 'b':
            self.SetAction(game, Action.BLOCK)


class HumanGamepadPlayer(Player):
    def __init__(self, name, team_side):
        super(HumanGamepadPlayer, self).__init__(name, team_side)
        self.gamepad = None

    def IsHuman(self):
        return True

    def SetGamepad(self, gamepad):
        self.gamepad = gamepad

    def custom_think(self, game, verbosity):
        # super(HumanGamepadPlayer, self).CustomThink(game, verbosity)
        Player.custom_think(self, game, verbosity)

        assert (self.gamepad != None)

        ls = numpy.round(self.gamepad.GetLS())  # quantize LS to make it easier
        rt = self.gamepad.GetRT()
        rs = self.gamepad.GetRS()

        shot_trigger = rs[1] < -0.9
        pass_trigger = rt > 0.5

        self.SetInput(game, ls)
        if shot_trigger:
            self.SetAction(game, Action.SHOOT)
        elif pass_trigger:
            self.SetAction(game, Action.NONE)
            best_dot = -1.0
            teammates = game.team_players[self.team_side]
            for teammate, action in zip(teammates, Action.PASSES):
                if teammate is self:
                    continue
                delta = teammate.GetPosition(game) - self.GetPosition(game)
                dist = numpy.linalg.norm(delta)
                if dist < 0.001:
                    direction = numpy.array([1.0, 0.0])
                else:
                    direction = delta / dist
                dot = ls.dot(direction)
                if dot > best_dot:
                    self.SetAction(game, action)
                    best_dot = dot

    def WantsTogglePause(self):
        return self.gamepad.WantsTogglePause()

    def WantsQuit(self):
        return self.gamepad.WantsQuit()
