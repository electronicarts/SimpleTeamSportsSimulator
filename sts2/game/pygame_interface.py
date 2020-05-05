# Copyright (C) 2020 Electronic Arts Inc.  All rights reserved.
"""
Created on Thu Jun 28 12:37:57 2018

@author: csomers
"""
import datetime  # mas
import sys, copy, os
import pygame
import numpy

from sts2.game.game_state import GameState, Action
from sts2.game.player import HumanGamepadPlayer
from sts2.game.settings import TeamSide, GamePhase


class TextPrint:
    def __init__(self, screen):
        self.Reset()
        self.font = pygame.font.Font(None, 20)
        self.screen = screen

    def Print(self, s, pos=None, color=(0, 0, 0), align='left'):
        b = self.font.render(s, True, color)
        if pos is None:
            pos = [self.x, self.y]
            self.y += self.line_height

        if align is 'center':
            sx, sy = self.font.size(s)
            pos = pos[0] - sx // 2, pos[1] - sy // 2

        self.screen.blit(b, pos)

    def Reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15

    def Indent(self):
        self.x += 10

    def Unindent(self):
        self.x -= 10


def ScaleColor(color, scale):
    r = int(color.r * scale)
    g = int(color.g * scale)
    b = int(color.b * scale)
    return pygame.Color(r, g, b)


class InterfaceSettings:
    def __init__(self, framerate, dead_zone, x_scale, z_scale, rink_border, pause_frames,
                 keyboard_only):
        self.framerate = framerate
        self.dead_zone = dead_zone
        self.x_scale = x_scale
        self.z_scale = z_scale
        self.rink_border = rink_border
        self.pause_frames = pause_frames
        self.keyboard_only = keyboard_only


class GamePads:
    # rename whole class to controllers
    def __init__(self, settings):
        self.gamepads = []

        if not settings.keyboard_only:
            pygame.joystick.init()
            for i in range(pygame.joystick.get_count()):
                self.gamepads.append(GamePad(i, settings))
        self.gamepads.append(KeyboardController(len(self.gamepads), settings))

    def GetGamepad(self, index):
        if index >= len(self.gamepads):
            raise RuntimeError(
                "Error: required %d controllers but only have %d (have you prohibited gamepads?)" % (
                    index + 1, len(self.gamepads)))
        return self.gamepads[index]

    def GetGamepads(self):
        return self.gamepads

    def GetNumGamepads(self):
        return len(self.gamepads)

    def tick(self):
        for gamepad in self.gamepads:
            gamepad.Tick()


class Controller:
    BUTTON_A = 0
    BUTTON_B = 1
    BUTTON_X = 2
    BUTTON_Y = 3
    BUTTON_LB = 4
    BUTTON_RB = 5
    BUTTON_SELECT = 6
    BUTTON_START = 7
    BUTTON_L3 = 9
    BUTTON_R3 = 9

    BUTTONS = [BUTTON_A, BUTTON_B, BUTTON_X, BUTTON_Y, BUTTON_LB, BUTTON_RB, BUTTON_SELECT,
               BUTTON_START, BUTTON_L3, BUTTON_R3]

    def GetButton(self, button):
        return self.buttons[button]

    def GetButtonPhase(self, button):
        return self.button_phases[button]

    def GetButtonPress(self, button):
        return self.button_phases[button] == 1.0

    def GetButtonRlease(self, button):
        return self.button_phases[button] == -1.0


class KeyboardController(Controller):
    def __init__(self, index, settings):
        self.index = 0
        self.settings = settings
        self.ls = numpy.zeros(2)
        self.rs = numpy.zeros(2)
        self.buttons = numpy.zeros(len(self.BUTTONS))
        self.button_phases = numpy.zeros(len(self.BUTTONS))

    def Tick(self):
        self.ls = numpy.zeros(2)
        self.rs = numpy.zeros(2)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.ls[0] -= 1.0

        if keys[pygame.K_RIGHT]:
            self.ls[0] += 1.0

        if keys[pygame.K_UP]:
            self.ls[1] -= 1.0

        if keys[pygame.K_DOWN]:
            self.ls[1] += 1.0

        if keys[pygame.K_SPACE]:
            self.rs[1] = -1.0

    def GetLS(self):
        return self.ls

    def GetRT(self):
        return 0.0  # TODO

    def GetLT(self):
        return 0.0  # TOOD

    def GetRS(self):
        return self.rs

    def WantsToggleReplayContinue(self):
        return self.GetButtonPress(Controller.BUTTON_A)

    def WantsTogglePause(self):
        return self.GetButtonPress(Controller.BUTTON_START)

    def GetReplayScrubSpeed(self):
        scrub = (self.GetRT() - self.GetLT()) * 4.0
        if abs(scrub) < 0.1:
            scrub = 0.0
        return scrub

    def GetReplaySingleStep(self):
        if self.GetButtonPress(Controller.BUTTON_LB):
            return -1
        if self.GetButtonPress(Controller.BUTTON_RB):
            return 1
        return 0

    def WantsQuit(self):
        self.GetButton(Controller.BUTTON_LB) and self.GetButton(Controller.BUTTON_RB)


class GamePad(Controller):
    def __init__(self, index, settings):
        self.index = 0
        self.settings = settings
        self.joystick = pygame.joystick.Joystick(index)
        self.joystick.init()
        self.buttons = numpy.zeros(len(self.BUTTONS))
        self.button_phases = numpy.zeros(len(self.BUTTONS))

    def Tick(self):
        old_buttons = copy.copy(self.buttons)
        for button in self.BUTTONS:
            self.buttons[button] = self.joystick.get_button(button)
        self.button_phases = self.buttons - old_buttons

    def GetAxes(self, a1, a2):
        stick = numpy.array([self.joystick.get_axis(a1), self.joystick.get_axis(a2)])
        if numpy.linalg.norm(stick) < self.settings.dead_zone:
            stick = numpy.zeros(2)
        return stick

    def GetLS(self):
        return self.GetAxes(0, 1)

    def GetRT(self):
        return max(0.0, -self.joystick.get_axis(2))

    def GetLT(self):
        return max(0.0, self.joystick.get_axis(2))

    def GetRS(self):
        return self.GetAxes(4, 3)

    def WantsToggleReplayContinue(self):
        return self.GetButtonPress(GamePad.BUTTON_A)

    def WantsTogglePause(self):
        return self.GetButtonPress(GamePad.BUTTON_START)

    def GetReplayScrubSpeed(self):
        scrub = (self.GetRT() - self.GetLT()) * 4.0
        if abs(scrub) < 0.1:
            scrub = 0.0
        return scrub

    def GetReplaySingleStep(self):
        if self.GetButtonPress(GamePad.BUTTON_LB):
            return -1
        if self.GetButtonPress(GamePad.BUTTON_RB):
            return 1
        return 0

    def WantsQuit(self):
        self.GetButton(GamePad.BUTTON_LB) and self.GetButton(GamePad.BUTTON_RB)


class PygameInterface:
    img_id = 0  # Mas
    game_start_time = None  # Mas

    def __init__(self, game, settings, replay=False):
        # os.environ['SDL_VIDEO_WINDOW_POS'] = str(0) + "," + str(0)
        # os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()

        pygame.display.set_caption("Simple Sports Simulation")

        self.game = game
        self.settings = settings
        self.gamepads = GamePads(settings)
        self.keyboard_controller = KeyboardController(0, settings)
        self.screen_x = settings.x_scale * self.game.arena.arena_size[0]
        self.screen_z = settings.z_scale * self.game.arena.arena_size[1]

        self.screen = pygame.display.set_mode((self.screen_x, self.screen_z))
        fname = os.path.split(__file__)[-1]
        rink_png = os.path.abspath(__file__).replace(fname, 'ea_rink.png')
        self.bg_image = pygame.image.load(rink_png)

        self.clock = pygame.time.Clock()
        self.done = False
        self.pause_frames = 0

        self.last_was_goal = False

        self.replay_speed = 1.0
        self.replay_step = 0
        self.replay_frame = -1
        if replay:
            self.replay_frame = 0

        self.text_print = TextPrint(self.screen)

    def GetNextGameFrame(self):
        if self.replay_frame >= 0:
            # we are in replay
            if self.pause_frames == 0:
                self.replay_frame += int(numpy.round(self.replay_speed))
                self.replay_frame += self.replay_step

            self.replay_frame = numpy.clip(self.replay_frame, 0,
                                           len(self.game.game_state_history) - 1)

            return self.game.game_state_history[self.replay_frame].state

        # we are in live game
        if self.game.IsSimulationComplete():
            return None

        if self.AllowSimulation():
            self.game.update()

        return self.game.game_state_history[-1].state

    def ProcessReplayInputs(self):
        wants_quit = False
        replay_continue_toggle = False
        replay_scrub_speed = 0.0
        replay_step = 0

        for gamepad in self.gamepads.GetGamepads():
            replay_continue_toggle = replay_continue_toggle or gamepad.WantsToggleReplayContinue()
            replay_scrub_speed += gamepad.GetReplayScrubSpeed()
            wants_quit = wants_quit or gamepad.WantsQuit()
            replay_step += gamepad.GetReplaySingleStep()
            wants_toggle_pause = gamepad.WantsTogglePause()

        if self.IsInReplay():
            # if self.replay_speed == 0.0 and replay_continue_toggle:
            #	self.replay_speed = 1.0
            # elif self.replay_speed > 0.0 and replay_continue_toggle:
            #	self.replay_speed = 0.0
            # elif replay_scrub_speed != 0.0:
            self.replay_speed = replay_scrub_speed
            self.replay_step = replay_step

            if wants_toggle_pause:
                if self.IsInReplay():
                    self.replay_frame = -1
                else:
                    self.replay_frame = len(self.game.game_state_history) - 1

        return wants_quit

    def ProcessHumanPlayerMetaInputs(self):
        wants_toggle_pause = False
        wants_quit = False

        for player in self.game.players:
            if isinstance(player, HumanGamepadPlayer):
                wants_toggle_pause = wants_toggle_pause or player.WantsTogglePause()
                wants_quit = wants_quit or player.WantsQuit()

        if wants_toggle_pause:
            if self.IsInReplay():
                self.replay_frame = -1
            else:
                self.replay_frame = len(self.game.game_state_history) - 1

        return wants_quit

    def IsInReplay(self):
        return self.replay_frame != -1

    def BindControllers(self):
        humans = 0
        for player in self.game.players:
            if player.IsHuman():
                # this may assert if there are not as many gamepads as humans
                controller = self.gamepads.GetGamepad(humans)
                print("controller is", controller)
                player.SetGamepad(controller)
                humans += 1

    def UnBindControllers(self):
        for player in self.game.players:
            if player.IsHuman():
                player.SetGamepad(None)

    def Run(self):
        self.BindControllers()

        while not self.done:
            self.update()

        self.UnBindControllers()

    def update(self):
        # show a frame and wait for framerate

        self.done = False

        # update button phases, etc
        self.gamepads.tick()

        if self.IsInReplay():
            self.done = self.done or self.ProcessReplayInputs()
        else:
            self.done = self.done or self.ProcessHumanPlayerMetaInputs()

        # --- Event Processing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.done = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.done = True

        self._frame = None
        # handle live game or replay
        if not self.done:
            self._frame = self.GetNextGameFrame()

        if self._frame is None:
            # just end this current game
            self.done = True

        if self.done:
            self.Quit()

    def HandleGameReplayFrame(self):
        self.Draw(self._frame)
        self.UpdatePause(self._frame)
        # self.SaveImage()

    def SaveImage(self):
        if self.game_start_time is None:
            self.game_start_time = "c:\\NHL_Games\\" + datetime.date.today().isoformat() + '_%05d.PNG'
        surface = pygame.display.get_surface()
        fname = self.game_start_time % self.img_id
        self.img_id += 1
        pygame.image.save(surface, fname)

    def UpdatePause(self, game_state):
        if self.pause_frames > 0:
            self.pause_frames -= 1
            if self.pause_frames == 0:
                self.pause_frames = -1
        elif self.pause_frames < 0:
            self.pause_frames += 1
        else:
            if not self.IsInReplay():
                if game_state.current_phase in [GamePhase.STOPPAGE_GOAL]:
                    self.Pause(self.settings.pause_frames)
                    self.last_was_goal = True

                elif self.last_was_goal:
                    self.Pause(self.settings.pause_frames)
                    self.last_was_goal = False

    def Draw(self, game_state):
        self.DrawRink(game_state)
        self.DrawPlayers(game_state)
        self.DrawActions(game_state)

        self.text_print.Reset()
        # if self.replay_frame > -1:
        # 	self.text_print.Print("Replay %d/%d" % (self.replay_frame, len(self.game.game_state_history) - 1)) # TODO: kernelize
        # else:
        # 	self.text_print.Print("Tick %d/%d" % (self.game.tick, self.game.rules.max_tick)) # TODO: kernelize

        self.text_print.Print("H:%d A:%d" % (game_state.home_score, game_state.away_score))
        self.text_print.Print("%s -> %s" % (game_state.previous_phase, game_state.current_phase))
        if self.pause_frames:
            self.text_print.Print("Pausing %d" % self.pause_frames)

        # Limit frame rate and swap back buffer
        try:
            self.clock.tick(self.settings.framerate)
            pygame.display.flip()
        except KeyboardInterrupt:
            self.Quit()
            sys.exit()

    def GameCoordToScreenCoord(self, x, z=None):
        if z is None and type(x) is type(()):
            x, z = x
        X = (x - self.game.arena.min_x) * self.settings.x_scale
        Z = (z - self.game.arena.min_z) * self.settings.z_scale
        return X, Z

    def DrawRink(self, game_state):
        image = self.bg_image
        image = pygame.transform.rotate(image, 90)
        image = pygame.transform.scale(image, (self.screen_x, self.screen_z))
        self.screen.blit(image, (0, 0))

    def DrawPlayers(self, game_state):
        colours = [pygame.Color('red'), pygame.Color('white')]

        # ideally this works without the original player objects, just the series object

        for team_side, colour, prefix in zip(TeamSide.TEAMSIDES, colours, ['H', 'A']):
            # i = 1
            team_prefix = GameState.TEAMSIDE_PREFIXES[team_side]

            # why is this a float???
            for player_index in range(int(game_state[team_prefix + GameState.TEAM_PLAYERS])):
                use_color = copy.copy(colour)
                name = game_state[team_prefix + str(player_index) + GameState.PLAYER_NAME]
                posx = game_state[team_prefix + str(player_index) + GameState.PLAYER_POS_X]
                posz = game_state[team_prefix + str(player_index) + GameState.PLAYER_POS_Z]
                inputx = game_state[team_prefix + str(player_index) + GameState.PLAYER_INPUT_X]
                inputz = game_state[team_prefix + str(player_index) + GameState.PLAYER_INPUT_Z]
                has_control = game_state[GameState.CONTROL_TEAM] == team_side and game_state[
                    GameState.CONTROL_INDEX] == player_index
                action_time = game_state[
                    team_prefix + str(player_index) + GameState.PLAYER_ACTION_TIME]

                input_scale = 1.0
                x, z = self.GameCoordToScreenCoord(posx, posz)
                ix, iz = self.GameCoordToScreenCoord(posx + inputx * input_scale,
                                                     posz + inputz * input_scale)
                try:
                    x, z = int(x), int(z)
                except:
                    print(x, z, posx, posz)
                    x, z = 0, 0
                if action_time > 0:
                    use_color = ScaleColor(use_color, 0.5)

                if has_control:
                    pygame.draw.circle(self.screen, pygame.Color('black'), (x, z), int(
                        self.game.rules.player_radius * 1.4 * self.settings.x_scale), 0)

                draw_radius = self.game.rules.player_radius
                if game_state[team_prefix + str(player_index) + GameState.PLAYER_IS_HUMAN]:
                    pygame.draw.circle(self.screen, pygame.Color('orange'), (x, z),
                                       int(draw_radius * self.settings.x_scale), 0)
                    draw_radius *= 0.8

                pygame.draw.line(self.screen, pygame.Color('yellow'), (x, z), (ix, iz), 2)

                pygame.draw.circle(self.screen, use_color, (x, z),
                                   int(draw_radius * self.settings.x_scale), 0)
                self.text_print.Print(name, (x, z), align='center')

        # i += 1 # TODO: player names in game state

    def DrawActions(self, game_state):
        width = 3

        for team_side in TeamSide.TEAMSIDES:
            team_prefix = GameState.TEAMSIDE_PREFIXES[team_side]
            other_team_prefix = GameState.TEAMSIDE_PREFIXES[
                TeamSide.Opposite(team_side)]
            team_players = int(game_state[team_prefix + GameState.TEAM_PLAYERS])
            control_team = game_state[GameState.CONTROL_TEAM]
            control_index = game_state[GameState.CONTROL_INDEX]
            control_posx = game_state[GameState.TEAMSIDE_PREFIXES[control_team] + str(
                control_index) + GameState.PLAYER_POS_X]
            control_posz = game_state[GameState.TEAMSIDE_PREFIXES[control_team] + str(
                control_index) + GameState.PLAYER_POS_Z]

            for player_index in range(team_players):
                player_action = game_state[
                    team_prefix + str(player_index) + GameState.PLAYER_ACTION]
                posx = game_state[team_prefix + str(player_index) + GameState.PLAYER_POS_X]
                posz = game_state[team_prefix + str(player_index) + GameState.PLAYER_POS_Z]

                if player_action is Action.SHOOT:
                    colour = pygame.Color('black')
                    if game_state[GameState.CURRENT_PHASE] != GamePhase.STOPPAGE_GOAL:
                        colour = pygame.Color('red')
                        pygame.draw.line(self.screen, pygame.Color('black'),
                                         self.GameCoordToScreenCoord(posx, posz),
                                         self.GameCoordToScreenCoord(control_posx, control_posz),
                                         width)

                    net_posx = game_state[other_team_prefix + GameState.TEAM_NET_X]
                    net_posz = game_state[other_team_prefix + GameState.TEAM_NET_Z]
                    pygame.draw.line(self.screen, colour, self.GameCoordToScreenCoord(posx, posz),
                                     self.GameCoordToScreenCoord(net_posx, net_posz), width)
                elif player_action in Action.PASSES:
                    for teammate_index, action in zip(range(team_players), Action.PASSES):
                        if action is player_action:
                            teammate_posx = game_state[
                                team_prefix + str(teammate_index) + GameState.PLAYER_POS_X]
                            teammate_posz = game_state[
                                team_prefix + str(teammate_index) + GameState.PLAYER_POS_Z]
                            colour = pygame.Color('black')

                            has_control = control_team == team_side and control_index == teammate_index
                            if not has_control:
                                colour = pygame.Color('red')
                                pygame.draw.line(self.screen, pygame.Color('black'),
                                                 self.GameCoordToScreenCoord(posx, posz),
                                                 self.GameCoordToScreenCoord(control_posx,
                                                                             control_posz), width)
                            pygame.draw.line(self.screen, colour,
                                             self.GameCoordToScreenCoord(posx, posz),
                                             self.GameCoordToScreenCoord(teammate_posx,
                                                                         teammate_posz), width)

    def Pause(self, pause):
        self.pause_frames = pause

    def AllowSimulation(self):
        return self.pause_frames <= 0

    def Quit(self):
        pygame.quit()


KEYBOARD_ONLY = False
# accelerated
# INTERFACE_SETTINGS = InterfaceSettings(framerate=1000, x_scale=30, z_scale=30, rink_border=0, dead_zone=0.2, pause_frames=15)

# slow	
# INTERFACE_SETTINGS = InterfaceSettings(framerate=5, x_scale=30, z_scale=30, rink_border=0, dead_zone=0.2, pause_frames=15)

# normal
INTERFACE_SETTINGS = InterfaceSettings(framerate=15, x_scale=20, z_scale=20, rink_border=0,
                                       dead_zone=0.2, pause_frames=15, keyboard_only=KEYBOARD_ONLY)
