# Copyright (C) 2020 Electronic Arts Inc.  All rights reserved.

class Rules:
    class MotionModel:
        ACCELERATION_MODEL = "ACCELERATION_MODEL"
        PAC_MAN_MODEL = "PAC_MAN_MODEL"

    class LayoutConstraint:
        NONE = "NONE"
        CROSSOVER_CONSTRAINT = "CROSSOVER_CONSTRAINT"

    def __init__(self, max_tick, arena_size, player_radius, max_vel, max_accel,
                 min_intercept_chance, max_intercept_chance, max_intercept_dist,
                 player_intercept_speed, check_stun_time, shot_response_time, pass_response_time,
                 receive_response_time, shot_distance_accuracy_scale, enable_player_collisions,
                 motion_model, layout_constraint):
        self.max_tick = max_tick
        self.arena_size = arena_size
        self.player_radius = player_radius
        self.max_vel = max_vel
        self.max_accel = max_accel
        self.min_intercept_chance = min_intercept_chance
        self.max_intercept_chance = max_intercept_chance
        self.max_intercept_dist = max_intercept_dist
        self.player_intercept_speed = player_intercept_speed
        self.check_stun_time = check_stun_time
        self.shot_response_time = shot_response_time
        self.pass_response_time = pass_response_time
        self.receive_response_time = receive_response_time
        self.shot_distance_accuracy_scale = shot_distance_accuracy_scale
        self.enable_player_collisions = enable_player_collisions
        self.motion_model = motion_model
        self.layout_constraint = layout_constraint


PACMAN_GAME_RULES = Rules(
    max_tick=15 * 20, arena_size=(18, 36), player_radius=0.75, max_vel=0.5,
    max_accel=0.05, min_intercept_chance=0.0, max_intercept_chance=0.9,
    max_intercept_dist=5.0, player_intercept_speed=0.1, check_stun_time=20,
    shot_response_time=10, pass_response_time=10, receive_response_time=15,
    shot_distance_accuracy_scale=4.0, enable_player_collisions=False,
    motion_model=Rules.MotionModel.PAC_MAN_MODEL,
    layout_constraint=Rules.LayoutConstraint.CROSSOVER_CONSTRAINT)

SIMPLE_GAME_RULES = Rules(
    max_tick=15 * 30, arena_size=(18, 36), player_radius=0.75, max_vel=0.5,
    max_accel=0.05, min_intercept_chance=0.0, max_intercept_chance=0.9,
    max_intercept_dist=5.0, player_intercept_speed=0.1, check_stun_time=20,
    shot_response_time=10, pass_response_time=10, receive_response_time=15,
    shot_distance_accuracy_scale=4.0, enable_player_collisions=True,
    motion_model=Rules.MotionModel.ACCELERATION_MODEL,
    layout_constraint=Rules.LayoutConstraint.NONE)

STANDARD_GAME_RULES = Rules(
    max_tick=15 * 30, arena_size=(18, 36), player_radius=0.75, max_vel=0.5,
    max_accel=0.05, min_intercept_chance=0.5, max_intercept_chance=1.0,
    max_intercept_dist=3.5, player_intercept_speed=0.05, check_stun_time=20,
    shot_response_time=10, pass_response_time=10, receive_response_time=15,
    shot_distance_accuracy_scale=4.0, enable_player_collisions=True,
    motion_model=Rules.MotionModel.ACCELERATION_MODEL,
    layout_constraint=Rules.LayoutConstraint.NONE)

PREDICTABLE_INTERCEPTION_GAME_RULES = Rules(
    max_tick=15 * 30, arena_size=(18, 36), player_radius=0.75, max_vel=0.5,
    max_accel=0.05, min_intercept_chance=1.0, max_intercept_chance=1.0,
    max_intercept_dist=2.5, player_intercept_speed=0.0, check_stun_time=20,
    shot_response_time=10, pass_response_time=10, receive_response_time=15,
    shot_distance_accuracy_scale=4.0, enable_player_collisions=True,
    motion_model=Rules.MotionModel.ACCELERATION_MODEL,
    layout_constraint=Rules.LayoutConstraint.NONE)
