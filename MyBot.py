#!/usr/bin/env python3
# Python 3.6
import hlt
from hlt import constants
from hlt.positionals import Direction
import random
import logging

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


def highest_value_cell(ship, map):
    # TODO: Divisible by zero
    max_position = hlt.entity.Position(0, 0)
    max_position_distance = game_map.calculate_distance(max_position, ship.position)
    max_amount = map[max_position].halite_amount
    max_value = max_amount / max_position_distance

    for x in range(map.width):
        for y in range(map.height):
            map_cell = map[hlt.entity.Position(x, y)]
            if not map_cell.position == ship.position:
                map_cell_distance = game_map.calculate_distance(map_cell.position, ship.position)
                map_cell_value = map_cell.halite_amount / map_cell_distance

                if map_cell_value > max_value:
                    if map_cell_distance < max_position_distance:
                        max_position = map_cell.position
                        max_position_distance = game_map.calculate_distance(max_position, ship.position)
                        max_amount = map_cell.halite_amount
                        max_value = max_amount / max_position_distance

    return max_position


""" <<<Game Loop>>> """
ship_states = {}
ship_targets = {}
while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map
    command_queue = []
    next_turn_positions = []

    if len(me.get_ships()) == 0:
        command_queue.append(me.shipyard.spawn())

    for ship in me.get_ships():
        if ship.id not in ship_states:
            ship_states[ship.id] = "NEW"

        move_direction = Direction.Still
        logging.info("Ship ID: " + str(ship.id) + "State: " + ship_states[ship.id])

        if ship_states[ship.id] == "NEW":
            ship_targets[ship.id] = highest_value_cell(ship, game_map)
            ship_states[ship.id] = "TRANSIT"

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

        command_queue.append(ship.move(move_direction))

    game.end_turn(command_queue)