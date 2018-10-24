#!/usr/bin/env python3
# Python 3.6
import hlt
from hlt import constants
from hlt.positionals import Direction
import logging
from operator import itemgetter
import random

""" <<<Game Begin>>> """
game = hlt.Game()

# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("MyPythonBot")
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))


def move_towards_target(ship, target):
    return game_map.naive_navigate(ship, target)


def move_towards_higher_halite(ship, map):
    move_choice = Direction.North
    halite = map[ship.position.directional_offset(Direction.North)].halite_amount

    if map[ship.position.directional_offset(Direction.East)].halite_amount > halite:
        move_choice = Direction.East
        halite = map[ship.position.directional_offset(Direction.East)].halite_amount

    if map[ship.position.directional_offset(Direction.West)].halite_amount > halite:
        move_choice = Direction.West
        halite = map[ship.position.directional_offset(Direction.West)].halite_amount

    if map[ship.position.directional_offset(Direction.South)].halite_amount > halite:
        move_choice = Direction.South

    return move_choice


def move_towards_lower_halite(ship, map):
    move_choice = Direction.North
    halite = map[ship.position.directional_offset(Direction.North)].halite_amount

    if map[ship.position.directional_offset(Direction.East)].halite_amount < halite:
        move_choice = Direction.East
        halite = map[ship.position.directional_offset(Direction.East)].halite_amount

    if map[ship.position.directional_offset(Direction.West)].halite_amount < halite:
        move_choice = Direction.West
        halite = map[ship.position.directional_offset(Direction.West)].halite_amount

    if map[ship.position.directional_offset(Direction.South)].halite_amount < halite:
        move_choice = Direction.South

    return move_choice


""" <<<Game Loop>>> """
ship_states = {}
ship_targets = {}
while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map
    command_queue = []
    next_turn_positions = []

    cell_values = []
    for x in range(game_map.width):
        for y in range(game_map.height):
            cell = game_map[hlt.entity.Position(x, y)]

            if not cell.position == me.shipyard.position:
                if not cell.position in ship_targets.values():
                    cell_values.append((
                        cell.position,
                        cell.halite_amount / game_map.calculate_distance(cell.position, me.shipyard.position)))

    cell_values.sort(key=itemgetter(1))

    for ship in me.get_ships():
        if ship.id not in ship_states:
            ship_states[ship.id] = "NEW"
            logging.info("Turtle: {} Created".format(ship.id))

        move_direction = Direction.Still

        if ship_states[ship.id] == "NEW":
            ship_targets[ship.id] = cell_values.pop()[0]
            ship_states[ship.id] = "TRANSIT"
            logging.info("Turtle: {} TARGET set to {}".format(ship.id, ship_targets[ship.id]))

        if ship_states[ship.id] == "TRANSIT":
            if ship_targets[ship.id] == ship.position:
                ship_states[ship.id] = "COLLECT"
            else:
                move_direction = move_towards_target(ship, ship_targets[ship.id])

        if ship_states[ship.id] == "COLLECT":
            if ship.is_full:
                ship_states[ship.id] = "RETURN"
            else:
                if game_map[ship.position].halite_amount > 100:
                    move_direction = Direction.Still
                else:
                    move_direction = move_towards_higher_halite(ship, game_map)

        if ship_states[ship.id] == "RETURN":
            if ship.position == me.shipyard.position:
                ship_states[ship.id] = "NEW"
            else:
                move_direction = move_towards_target(ship, me.shipyard.position)

        # Avoid ships
        for pos in next_turn_positions:
            if ship.position.directional_offset(move_direction) == pos:
                move_direction = move_towards_lower_halite(ship, game_map)
        for pos in next_turn_positions:
            if ship.position.directional_offset(move_direction) == pos:
                move_direction = Direction.invert(move_direction)

        next_turn_positions.append(ship.position.directional_offset(move_direction))
        command_queue.append(ship.move(move_direction))

    if me.shipyard.position not in next_turn_positions:
        if len(me.get_ships()) < 2 and me.halite_amount >= constants.SHIP_COST and game.turn_number < 200:
            command_queue.append(me.shipyard.spawn())

    game.end_turn(command_queue)