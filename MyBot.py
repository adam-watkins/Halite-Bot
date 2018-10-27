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


def main():
    """" <<<Game Begin>>> """
    game = hlt.Game()
    game.ready("MyPythonBot")
    logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

    """ <<<Game Loop>>> """
    ship_targets = {}  # Ship : Position
    ship_states = {}  # Ship : ShipState
    while True:
        game.update_frame()
        me = game.me
        game_map = game.game_map
        ships = me.get_ships()

        # Removing Dead ships
        dead_ships = []
        for ship_id in ship_states:
            if not me.has_ship(ship_id):
                dead_ships.append(ship_id)
        for ds in dead_ships:
            del ship_states[ds]

        position_value_list = game_map.get_cell_values(me.shipyard.position, MIN_HALITE)  # (position, value)

        # Targets already assigned
        for p in position_value_list:
            if p[0] in ship_targets.values():
                position_value_list.remove(p)

        # # Targets near other targets
        # for pos in values_dict:
        #     for st_pos in ship_targets.values():
        #         if game_map.calculate_distance(pos, st_pos) <= 2:
        #             values_dict[pos] *= .75

        next_targets = position_value_list
        next_targets.sort(key=itemgetter(1))  # Prioritizing targets

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

            if ship_states[ship.id] == ShipStates.Inbound and ship_targets[ship.id] == ship.position:
                ship_targets[ship.id] = next_targets.pop()[0]
                ship_states[ship.id] = ShipStates.Outbound

            if constants.MAX_TURNS - game.turn_number == game_map.height / 2:  # TODO improve
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
            if ship.halite_amount < game_map[ship.position].halite_amount / constants.MOVE_COST_RATIO:
                ship_moves[ship.id] = ship.position
                command_queue.append(ship.move(Direction.Still))
                log_move(ship, ship_states[ship.id], ship_targets[ship.id], Direction.Still, "STUCK")

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
                        priority_list.sort(key=itemgetter(1))  # Lowest first
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
                        priority_list.sort(key=itemgetter(1), reverse=True)  # Highest first

                # NO MOVES
                if len(priority_list) == 0:
                    priority_list.append((Direction.Still, 0))
                    log_reason = "NO MOVE"

                # Make move
                final_direction = (priority_list[0])[0]
                ship_moves[ship.id] = game_map.normalize(ship.position.directional_offset(final_direction))
                command_queue.append(ship.move(final_direction))
                log_move(ship, ship_states[ship.id], ship_targets[ship.id], final_direction, log_reason)

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


def log_move(ship, state, target, move_d, special=""):
    s = "\n{}\n\tState: {}\n\tTarget: {}\n\tMove: {}".format(
        ship, state, target, move_d)
    if special != "":
        s += "\n\tNote: {}".format(special)
    logging.info(s)


main()
