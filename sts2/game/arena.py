# Copyright (C) 2020 Electronic Arts Inc.  All rights reserved.

import numpy


class Arena:
    def __init__(self, arena_size):
        self.arena_size = arena_size
        self.max_x = arena_size[0] / 2
        self.min_x = -self.max_x
        self.max_z = arena_size[1] / 2
        self.min_z = -self.max_z
        self.mins = numpy.array([self.min_x, self.min_z])
        self.maxs = numpy.array([self.max_x, self.max_z])

        self.net_position = [numpy.array([0, self.max_z]), numpy.array([0, self.min_z])]

    def GetNormalizedCoord(self, pos):
        return (pos - self.mins) / (self.maxs - self.mins)

    def GetArenaCoordFromNormalized(self, pos):
        return pos * (self.maxs - self.mins) + self.mins
