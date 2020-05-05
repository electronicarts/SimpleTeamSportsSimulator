# Copyright (C) 2020 Electronic Arts Inc.  All rights reserved.

import numpy


class Physics:
    def __init__(self, game):
        self.game = game

    def Update(self, verbosity):
        self.BoardCollisionUpdate(max(0, verbosity - 1))
        self.PlayerCollisionUpdate(max(0, verbosity - 1))

    def BoardCollisionUpdate(self, verbosity):
        # rectify collisions against boards
        arena = self.game.arena

        radius = self.game.rules.player_radius
        min_x = arena.min_x + radius
        max_x = arena.max_x - radius
        min_z = arena.min_z + radius
        max_z = arena.max_z - radius
        for player in self.game.players:
            position = player.GetPosition(self.game)
            velocity = player.GetVelocity(self.game)

            if position[0] < min_x:
                position[0] = min_x
                velocity[0] = 0
            if position[0] > max_x:
                position[0] = max_x
                velocity[0] = 0
            if position[1] < min_z:
                position[1] = min_z
                velocity[1] = 0
            if position[1] > max_z:
                position[1] = max_z
                velocity[1] = 0

            player.SetPosition(self.game, position)
            player.SetVelocity(self.game, velocity)

    def PlayerCollisionUpdate(self, verbosity):
        for player1 in self.game.players:
            for player2 in self.game.players:
                if player1 is player2:
                    continue

                if numpy.linalg.norm(player1.GetPosition(self.game) - player2.GetPosition(
                        self.game)) <= self.game.rules.player_radius * 2:
                    control_player = self.game.control.GetControl()

                    if self.game.rules.enable_player_collisions:
                        center = (player1.GetPosition(self.game) + player2.GetPosition(
                            self.game)) * 0.5
                        avg_vel = (player1.GetVelocity(self.game) + player2.GetVelocity(
                            self.game)) * 0.5
                        for player in [player1, player2]:
                            delta = player.GetPosition(self.game) - center
                            dist = numpy.linalg.norm(delta)
                            if dist > 0.001:
                                direction = delta / dist
                            else:
                                direction = numpy.array([1.0, 0.0])

                            player.SetPosition(self.game,
                                               center + direction * self.game.rules.player_radius * 1.01)
                            player.SetVelocity(self.game, avg_vel)

                    if player1 is control_player and player1.team_side != player2.team_side and player2.GetActionTime(
                            self.game) == 0:
                        self.game.CompleteCheck(player1, player2)
                    elif player2 is control_player and player2.team_side != player1.team_side and player1.GetActionTime(
                            self.game) == 0:
                        self.game.CompleteCheck(player2, player1)

    def InterceptTest(self, source, target, players, verbosity):
        # test each player in list for interception
        # if not intercepted the pass/shot would be successful
        # interception is a probability based on the ratio of the distance from the interceptor to
        # the intercept point and the distance of the intercept point from the start
        # as a baseline the probability is simply the ratio, so if the interceptor distance is 0 (along the path)
        # the interception is 100% and if the interceptor is just as far away it is 0%
        # the interception priority goes to the closest player to the start
        traj_delta = (target - source)
        traj_distance = numpy.linalg.norm(traj_delta) + 1e-10
        traj_dir = traj_delta / traj_distance

        if verbosity:
            print('intercept test tick %d %f,%f to %f,%f' % (
                self.game.tick, source[0], source[1], target[0], target[1]))

        through_chance = 1.0
        intercepting_player = None
        shortest_intercept = traj_distance + 1.0
        for player in players:
            # project player onto trajectory to find unconstrained intercept point
            player_source_delta = player.GetPosition(self.game) - source
            intercept_source_dist = traj_dir.dot(player_source_delta)
            # if behind the trajectory there is no intercept
            if intercept_source_dist > 0.0:
                # find distance from player to intercept
                if intercept_source_dist > traj_distance:
                    # adjust intercept point if source or target is closer
                    if verbosity: print(
                        'player %s intercept_source_dist %f > %f moving intercept to target' % (
                            player.name, intercept_source_dist, traj_distance))
                    intercept = target
                    intercept_source_dist = traj_distance
                else:
                    intercept = source + traj_dir * intercept_source_dist

                player_intercept_dist = numpy.linalg.norm(player.GetPosition(self.game) - intercept)

                closest_dist = max(0.0,
                                   player_intercept_dist - self.game.rules.player_intercept_speed * intercept_source_dist)
                if closest_dist > self.game.rules.max_intercept_dist:
                    prob = 0.0
                else:
                    prob = (self.game.rules.max_intercept_chance - self.game.rules.min_intercept_chance) \
                           * closest_dist / self.game.rules.max_intercept_dist + self.game.rules.min_intercept_chance

                through_chance *= 1.0 - prob

                if closest_dist < shortest_intercept:
                    r = numpy.random.random()
                    # prob = 1.0 - self.game.rules.intercept_scale * player_intercept_dist / traj_distance
                    if r < prob:
                        intercepting_player = player
                        shortest_intercept = closest_dist
                        if verbosity: print(
                            'player %s random %f < probability %f so intercepted' % (
                                player.name, r, prob), 'closest_dist', closest_dist,
                            'player_intercept_dist', player_intercept_dist, 'intercept_source_dist',
                            intercept_source_dist)
                    else:
                        if verbosity: print(
                            'player %s random %f > probability %f so not intercepted' % (
                                player.name, r, prob), 'closest_dist', closest_dist,
                            'player_intercept_dist', player_intercept_dist, 'intercept_source_dist',
                            intercept_source_dist)
                else:
                    if verbosity: print(
                        'player %s player_intercept_dist %f >= shortest_intercept %f so skipping' % (
                            player.name, player_intercept_dist, shortest_intercept))
            else:
                if verbosity: print('player %s intercept_source_dist %f is behind' % (
                    player.name, intercept_source_dist))

        return intercepting_player, through_chance
