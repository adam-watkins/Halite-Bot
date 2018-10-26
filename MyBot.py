#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt
from hlt import constants
from hlt.positionals import Direction
from hlt.entity import ShipStates
from operator import itemgetter
import logging

MIN_HALITE = 100
MAX_SHIPS = 15

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


def log_move(ship, move_d, special=""):
    s = "\n{}\n\tState: {}\n\tTarget: {}\n\tMove: {}".format(
        ship, ship_states[ship.id], ship_targets[ship.id], move_d)
    if special != "":
        s += "\n\tNote: {}".format(special)
    logging.info(s)


while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map
    ships = me.get_ships()

    next_targets = game_map.get_cell_values(me.shipyard.position, MIN_HALITE)  # [(position, value)]
    next_targets.sort(key=itemgetter(1))  # Prioritizing targets

    for t in next_targets:
        if t[0] in ship_targets.values():
            next_targets.remove(t)

    # Setting Ship States
    for ship in ships:
        if ship.id not in ship_states:
            ship_targets[ship.id] = next_targets.pop()[0]
            ship_states[ship.id] = ShipStates.Outbound
        elif ship.position == me.shipyard.position:
            ship_targets[ship.id] = next_targets.pop()[0]
            ship_states[ship.id] = ShipStates.Outbound

        if ship_states[ship.id] == ShipStates.Outbound and ship_targets[ship.id] == ship.position:
            ship_states[ship.id] = ShipStates.Collect

        if ship_states[ship.id] == ShipStates.Collect and ship.is_full:
            ship_targets[ship.id] = me.shipyard.position
            ship_states[ship.id] = ShipStates.Inbound

        if ship_states[ship.id] == ShipStates.Collect and not game_map.is_near_min_halite(ship.position, MIN_HALITE):
            ship_targets[ship.id] = me.shipyard.position
            ship_states[ship.id] = ShipStates.Inbound

        if ship_states[ship.id] == ShipStates.Inbound and ship_targets[ship.id] == ship.position:
            ship_targets[ship.id] = next_targets.pop()[0]
            ship_states[ship.id] = ShipStates.Outbound

        if constants.MAX_TURNS - game.turn_number == game_map.height / 2:
            ship_targets[ship.id] = me.shipyard.position
            ship_states[ship.id] = ShipStates.Inbound

    logging.info("SHIPS: {}".format(len(ships)))
    logging.info("SHIPS States: {}".format(ship_states))
    logging.info("SHIPS Targets: {}".format(ship_targets))

    # Commands
    ship_moves = {}  # Ship : Position
    command_queue = []  # Command list

    # Stuck Ships
    for ship in ships:
        if ship.halite_amount < game_map[ship.position].halite_amount / 10:  # TODO: MOVE COST RATIO
            ship_moves[ship.id] = ship.position
            command_queue.append(ship.move(Direction.Still))
            log_move(ship, Direction.Still, "STUCK")

    # Moving Ships
    for ship in ships:
        if ship.id not in ship_moves:
            safe_directions = {}  # {direction : halite}
            priority_list = []  # (direction, halite)
            log_reason = "NONE"

            # Get safe moves:
            for d in Direction.get_all():
                if game_map.normalize(ship.position.directional_offset(d)) not in ship_moves.values():
                    safe_directions[d] = game_map[game_map.normalize(ship.position.directional_offset(d))].halite_amount

            # Transit order
            if ship_states[ship.id] == ShipStates.Inbound or ship_states[ship.id] == ShipStates.Outbound:
                for d in game_map.get_unsafe_moves(ship.position, ship_targets[ship.id]):
                    if d in safe_directions:
                        priority_list.append((d, safe_directions[d]))
                        log_reason = "NAV"
                    next_targets.sort(key=itemgetter(1))  # Lowest first
                for d in safe_directions:
                    if d not in priority_list:
                        priority_list.append((d, safe_directions[d]))

            # Collect order
            elif ship_states[ship.id] == ShipStates.Collect:
                if Direction.Still in safe_directions and game_map[ship.position].halite_amount > MIN_HALITE:
                    priority_list.append((Direction.Still, safe_directions[Direction.Still]))
                    log_reason = "COLLECT"
                else:
                    for d in Direction.get_all_cardinals():
                        if d in safe_directions:
                            priority_list.append((d, safe_directions[d]))
                            log_reason = "COL MOV"
                    next_targets.sort(key=itemgetter(1), reverse=True)  # Highest first

            # NO MOVES
            if len(priority_list) == 0:
                priority_list.append((Direction.Still, 0))
                log_reason = "NO MOVE"

            # Make move
            final_direction = (priority_list[0])[0]
            ship_moves[ship.id] = game_map.normalize(ship.position.directional_offset(final_direction))
            command_queue.append(ship.move(final_direction))
            log_move(ship, final_direction, log_reason)

    # Spawning
    if me.halite_amount >= constants.SHIP_COST and game.turn_number < 200:
        shipyard_is_empty = True
        for p in ship_moves.values():
            if p == me.shipyard.position:
                shipyard_is_empty = False
                break

        if shipyard_is_empty:
            command_queue.append(me.shipyard.spawn())
            logging.info("___SPAWNED SHIP___")

    logging.info("ALL MOVES: {}".format(ship_moves))
    game.end_turn(command_queue)
