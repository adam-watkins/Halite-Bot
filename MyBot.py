#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt
from hlt import constants
from hlt.positionals import Direction
from hlt.entity import ShipStates
from operator import itemgetter
import random
import logging

MIN_HALITE = 100

""" <<<Game Begin>>> """
game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.
game.ready("MyPythonBot")
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """

ship_targets = {}  # Ship : Position
ship_states = {}  # Ship : ShipState
while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map

    command_queue = []  # Direction list
    next_positions = []  # Position list
    next_targets = game_map.get_cell_values(me.shipyard.position, MIN_HALITE)  # [(position, value)]
    ships = me.get_ships()  # ships list

    next_targets.sort(key=itemgetter(1))  # Prioritizing targets
    next_targets = next_targets[-len(ships) - 1:]
    logging.info("Next Target(s): {}".format(next_targets))
    for t in next_targets:
        if t[0] in ship_targets.values():
            next_targets.remove(t)

    # Setting Ship States
    for ship in ships:
        if ship.id not in ship_states:
            ship_targets[ship.id] = next_targets.pop()[0]
            ship_states[ship.id] = ShipStates.Outbound
            logging.info("Created Ship: {}".format(ship.id, ship_states[ship.id]))
            logging.info("Ship: {} State Changed: {} Target: {}".format
                         (ship.id, ship_states[ship.id], ship_targets[ship.id]))

        if ship_states[ship.id] == ShipStates.Outbound and ship_targets[ship.id] == ship.position:
            ship_states[ship.id] = ShipStates.Collect
            logging.info("Ship: {} State Changed: {}".format(ship.id, ship_states[ship.id]))

        if ship_states[ship.id] == ShipStates.Collect and ship.is_full:
            ship_targets[ship.id] = me.shipyard.position
            ship_states[ship.id] = ShipStates.Inbound
            logging.info("Ship: {} FULL State Changed: {} Target: {}".format
                         (ship.id, ship_states[ship.id], ship_targets[ship.id]))

        if ship_states[ship.id] == ShipStates.Collect and not game_map.is_near_min_halite(ship.position, MIN_HALITE):
            ship_targets[ship.id] = me.shipyard.position
            ship_states[ship.id] = ShipStates.Inbound
            logging.info("Ship: {} LH State Changed: {} Target: {}".format
                         (ship.id, ship_states[ship.id], ship_targets[ship.id]))

        if ship_states[ship.id] == ShipStates.Inbound and ship_targets[ship.id] == ship.position:
            ship_targets[ship.id] = next_targets.pop()[0]
            ship_states[ship.id] = ShipStates.Outbound
            logging.info("Ship: {} State Changed: {} Target: {}".format
                         (ship.id, ship_states[ship.id], ship_targets[ship.id]))

    # Commanding Ships
    for ship in ships:
        move_direction = Direction.Still

        position_choices = []  # [(position, halite)]
        for pos in ship.position.get_surrounding_cardinals():
            if pos not in next_positions:
                position_choices.append(
                    (
                        pos, game_map[pos].halite_amount
                    )
                )
        position_choices.sort(key=itemgetter(1))

        if len(position_choices) > 0:
            if ship_states[ship.id] == ShipStates.Collect:
                move_direction = game_map.naive_navigate(ship, position_choices.pop())


        next_positions.append(ship.position.directional_offset(move_direction))
        command_queue.append(ship.move(move_direction))

    if len(ships) < 3:
        command_queue.append(me.shipyard.spawn())
    game.end_turn(command_queue)
