#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import random

from consts import L, R, U, D, CLOCKWISE, COUNTERCLOCKWISE
from point import Point
from block import Block, GhostBlock


class MetaTetro(type):
    """
    Save the different shapes of Tetrominoes
    """

    def __init__(cls, name, bases, dico):
        type.__init__(cls, name, bases, dico)
        Tetromino.classes.append(cls)
        Tetromino.nb_classes += 1


class Tetromino:
    """
    Geometric Tetris® shape formed by four Minos connected along their sides.
    A total of seven possible Tetriminos can be made using four Minos.
    """

    COORDS = NotImplemented
    SUPER_ROTATION_SYSTEM = (
        {
            COUNTERCLOCKWISE: ((0, 0), (R, 0), (R, U), (0, 2 * D), (R, 2 * D)),
            CLOCKWISE: ((0, 0), (L, 0), (L, U), (0, 2 * D), (L, 2 * D)),
        },
        {
            COUNTERCLOCKWISE: ((0, 0), (R, 0), (R, D), (0, 2 * U), (R, 2 * U)),
            CLOCKWISE: ((0, 0), (R, 0), (R, D), (0, 2 * U), (R, 2 * U)),
        },
        {
            COUNTERCLOCKWISE: ((0, 0), (L, 0), (L, U), (0, 2 * D), (L, 2 * D)),
            CLOCKWISE: ((0, 0), (R, 0), (R, U), (0, 2 * D), (R, 2 * D)),
        },
        {
            COUNTERCLOCKWISE: ((0, 0), (L, 0), (L, D), (0, 2 * U), (L, 2 * U)),
            CLOCKWISE: ((0, 0), (L, 0), (L, D), (0, 2 * D), (L, 2 * U)),
        },
    )

    classes = []
    nb_classes = 0
    random_bag = []

    def __new__(cls):
        """
        Return a Tetromino using the 7-bag Random Generator
        Tetris uses a “bag” system to determine the sequence of Tetriminos
        that appear during game play.
        This system allows for equal distribution among the seven Tetriminos.
        The seven different Tetriminos are placed into a virtual bag,
        then shuffled into a random order.
        This order is the sequence that the bag “feeds” the Next Queue.
        Every time a new Tetrimino is generated and starts its fall within the Matrix,
        the Tetrimino at the front of the line in the bag is placed at the end of the Next Queue,
        pushing all Tetriminos in the Next Queue forward by one.
        The bag is refilled and reshuffled once it is empty.
        """
        if not cls.random_bag:
            cls.random_bag = random.sample(cls.classes, cls.nb_classes)
        return super().__new__(cls.random_bag.pop())

    def __init__(self):
        self.orientation = 0
        self.rotation_point_5_used = False
        self.rotated_last = False

    def insert_into(self, matrix, position):
        self.matrix = matrix
        self.minoes = tuple(Block(Point(*coord) + position) for coord in self.COORDS)

    def _try_movement(self, next_coords_generator, trail=0, update=True):
        """
        Test if self can fit in the Grid with new coordinates,
        i.e. all cells are empty.
        If it can, change self's coordinates and return True.
        Else, make no changes and return False
        Update the Grid if there is no drop trail
        """
        futures_coords = []
        for p in next_coords_generator:
            if not self.matrix.is_empty_cell(p):
                return False
            futures_coords.append(p)

        for block, future_coord in zip(self.minoes, futures_coords):
            block.coord = future_coord
            block.trail = trail
        if update:
            self.matrix.update()
        return True

    def move(self, horizontally, vertically, trail=0, update=True):
        """
        Try to translate self horizontally or vertically
        The Tetrimino in play falls from just above the Skyline one cell at a time,
        and moves left and right one cell at a time.
        Each Mino of a Tetrimino “snaps” to the appropriate cell position at the completion of a move,
        although intermediate Tetrimino movement appears smooth.
        Only right, left, and downward movement are allowed.
        Movement into occupied cells and Matrix walls and floors is not allowed
        Update the Grid if there is no drop trail
        """
        if self._try_movement(
            (block.coord + Point(horizontally, vertically) for block in self.minoes),
            trail,
            update
        ):
            self.rotated_last = False
            return True
        else:
            return False

    def rotate(self, direction=CLOCKWISE):
        """
        Try to rotate self through 90° CLOCKWISE or COUNTERCLOCKWISE around its center
        Tetriminos can rotate clockwise and counterclockwise using the Super Rotation System.
        This system allows Tetrimino rotation in situations that
        the original Classic Rotation System did not allow,
        such as rotating against walls.
        Each time a rotation button is pressed,
        the Tetrimino in play rotates 90 degrees in the clockwise or counterclockwise direction.
        Rotation can be performed while the Tetrimino is Auto-Repeating left or right.
        There is no Auto-Repeat for rotation itself.
        """
        rotated_coords = tuple(
            mino.coord.rotate(self.minoes[0].coord, direction) for mino in self.minoes
        )

        for rotation_point, movement in enumerate(self.SUPER_ROTATION_SYSTEM[self.orientation][direction]):
            if self._try_movement(coord + Point(*movement) for coord in rotated_coords):
                self.orientation = (self.orientation + direction) % 4
                self.rotated_last = True
                if rotation_point == 4:
                    self.rotation_point_5_used = True
                return True
        return False

    def soft_drop(self):
        """
        Causes the Tetrimino to drop at an accelerated rate (s.AUTO_REPEAT_RATE)
        from its current location
        """
        return self.move(0, D, trail=1)

    def hard_drop(self, show_trail=True, update=True):
        """
        Causes the Tetrimino in play to drop straight down instantly from its
        current location and Lock Down on the first Surface it lands on.
        It does not allow for further player manipulation of the Tetrimino in play.
        """
        trail = 0
        while self.move(0, D, trail=trail, update=update):
            if show_trail:
                trail += 1
        return trail
    
    def t_spin(self):
        return ""


class TetroI(Tetromino, metaclass=MetaTetro):
    """
    Tetromino shaped like a capital I
    four minoes in a straight line
    """

    COORDS = (0, 0), (L, 0), (R, 0), (2 * R, 0)
    SUPER_ROTATION_SYSTEM = (
        {
            COUNTERCLOCKWISE: ((0, D), (L, D), (2 * R, D), (L, U), (2 * R, 2 * D)),
            CLOCKWISE: ((R, 0), (L, 0), (2 * R, 0), (L, D), (2 * R, 2 * U)),
        },
        {
            COUNTERCLOCKWISE: ((L, 0), (R, 0), (2 * L, 0), (R, U), (2 * L, 2 * D)),
            CLOCKWISE: ((0, D), (L, D), (2 * R, D), (L, U), (2 * R, 2 * D)),
        },
        {
            COUNTERCLOCKWISE: ((0, U), (R, U), (2 * L, U), (R, D), (2 * L, 2 * U)),
            CLOCKWISE: ((L, 0), (R, 0), (2 * L, 0), (R, U), (2 * L, 2 * D)),
        },
        {
            COUNTERCLOCKWISE: ((R, 0), (L, 0), (2 * R, 0), (L, D), (2 * R, 2 * U)),
            CLOCKWISE: ((0, U), (R, U), (2 * L, U), (R, D), (2 * L, 2 * U)),
        },
    )


class TetroT(Tetromino, metaclass=MetaTetro):
    """
    Tetromino shaped like a capital T
    a row of three minoes with one added above the center
    Can perform a T-Spin
    """

    COORDS = (0, 0), (L, 0), (0, U), (R, 0)
    
    T_SLOT = ((L, U), (R, U), (R, D), (L, D))

    def __init__(self):
        super().__init__()

    def t_spin(self):
        """
        Detects T-Spins:
        this action can be achieved by first landing a T-Tetrimino,
        and before it Locks Down, rotating it in a T-Slot
        (any Block formation such that when the T-Tetrimino is spun into it,
        any three of the four cells diagonally adjacent to the center of self
        are occupied by existing Blocks.)
        """
        if not self.rotated_last:
            return ""
        
        if self.rotation_point_5_used:
            return "T-Spin"
        
        center = self.minoes[0].coord
        pa = center + Point(*self.T_SLOT[self.orientation])
        pb = center + Point(*self.T_SLOT[(self.orientation+1)%4])
        pc = center + Point(*self.T_SLOT[(self.orientation+2)%4])
        pd = center + Point(*self.T_SLOT[(self.orientation+3)%4])

        a = not self.matrix.is_empty_cell(pa)
        b = not self.matrix.is_empty_cell(pb)
        c = not self.matrix.is_empty_cell(pc)
        d = not self.matrix.is_empty_cell(pd)

        if a and b and (c or d):
            return "T-Spin"
        elif c and d and (a or b):
            return "Mini T-Spin"
        else:
            return ""


class TetroZ(Tetromino, metaclass=MetaTetro):
    """
    Tetromino shaped like a capital Z
    two stacked horizontal dominoes with the top one offset to the left
    """

    COORDS = (0, 0), (L, U), (0, U), (R, 0)


class TetroS(Tetromino, metaclass=MetaTetro):
    """
    Tetromino shaped like a capital S
    two stacked horizontal dominoes with the top one offset to the right
    """

    COORDS = (0, 0), (0, U), (L, 0), (R, U)


class TetroL(Tetromino, metaclass=MetaTetro):
    """
    Tetromino shaped like a capital L
    a row of three minoes with one added above the right side
    """

    COORDS = (0, 0), (L, 0), (R, 0), (R, U)


class TetroJ(Tetromino, metaclass=MetaTetro):
    """
    Tetromino shaped like a capital J
    a row of three minoes with one added above the left side
    """

    COORDS = (0, 0), (L, U), (L, 0), (R, 0)


class TetroO(Tetromino, metaclass=MetaTetro):
    """
    Square shape
    four minoes in a 2×2 square.
    """

    COORDS = (R, 0), (0, 0), (R, U), (0, U)

    def rotate(self, direction=1):
        """ irrelevant """
        return False


class GhostPiece(Tetromino):
    """
    A graphical representation of where the Tetrimino in play will come to rest
    if it is dropped from its current position.
    """

    def __new__(cls, piece):
        return object.__new__(cls)

    def __init__(self, piece):
        self.matrix = piece.matrix
        self.minoes = tuple(
            GhostBlock(Point(mino.coord.x, mino.coord.y)) for mino in piece.minoes
        )
        self.hard_drop(show_trail=False, update=False)
