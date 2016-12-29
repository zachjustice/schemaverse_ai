import psycopg2 #import postgresql connection library
from psycopg2.extras import NamedTupleConnection

class FleetController:

    def __init__(self, conn_str):
        from db import db
        self.db = db(conn_str)
        self.ship_cost = 1000

    def run(self):
        db = self.db
        # assume all ships are completely fueled
        # want max money to make most ships possible
        db.convert_fuel_to_money()
        # update data to make correct amount of ships
        self.update_data()
        created_ship_ids = self.create_ships()
        # update after we've created our the ships so data is up to date
        self.update_data()

        # sanity checks
        print "-----"
        print "TIC", db.get_current_tic()
        print "Current Balance:", self.balance
        print "ships:", len(self.ships)
        print "planets:", len(self.planets)
        print "conquered planets:", len(self.conquered_planets)
        print "planets_in_range:", len(self.planets_in_range)
        print "ships_in_range:", len(self.ships_in_range)

        # if a planet is above mining capacity move ships to new planets
        moving_ships = self.move_ships()
        # ships which are not moving should be mining the planets they are on
        mining_ship_ids = [s for s in self.ships if s not in moving_ships]
        self.mine(mining_ship_ids)

        db.refuel_ships()
        print "-----"

    def get_current_tic(self):
        return self.db.get_current_tic()

    def update_data(self):
        db = self.db
        self.get_my_player_info()
        self.ships = db.get_my_ships()
        self.planets = db.get_planets()
        self.planets_in_range = db.get_planets_in_range()
        self.ships_in_range = db.get_ships_in_range()

        self.conquered_planets = [p for p in self.planets if p.conqueror_id == self.player_id]

        self.planets_by_id = {}
        for p in self.planets:
            self.planets_by_id[p.id] = p

        self.ships_by_id = {}
        for s in self.ships:
            self.ships_by_id[s.id] = s

        # dict{ planet id => [ list of ships on the planet ] } useful
        # for when we move ships above a planet's mine limit
        # in the future this may need to be updated to include ships
        # that are not exactly 0 distnance from the planet but we're
        # not there yet
        self.ships_per_planet = {}
        for p in self.planets_in_range:
            if p.planet not in self.ships_per_planet:
                self.ships_per_planet[p.planet] = []
            elif p.planet_location == p.ship_location:
                self.ships_per_planet[p.planet].append(p.ship)

    def get_my_player_info(self):
        my_player_info = self.db.get_my_player_info()
        self.player_id = my_player_info.id
        self.balance = my_player_info.balance
        self.fuel_reserve = my_player_info.fuel_reserve

    # TODO should probably actually use the ship_ids.
    def mine(self, ship_ids):
        if len(self.ships_per_planet.values()) < 1:
            return None

        db = self.db
        ship_actions = []

        for planet_id, ship_ids in self.ships_per_planet.iteritems():
            ship_action = ['MINE', planet_id, ship_ids]
            ship_actions.append(ship_action)
        db.bulk_set_ship_actions(ship_actions)

    def create_ships(self):
        # can't create ships if we don't own any planets to create them on
        if len(self.conquered_planets) < 1:
            return []

        db = self.db
        created_ship_ids = []
        num_ships_to_create = int(self.balance / self.ship_cost)
        if num_ships_to_create > 0:
            created_ship_ids = db.create_ships(num_ships_to_create)
            print "Created Ship ids:",len(created_ship_ids)
        return created_ship_ids

    def move_ships(self):
        moved_ships = []
        for planet_id, ship_ids in self.ships_per_planet.iteritems():
            planet = self.planets_by_id[planet_id]
            mine_limit = planet.mine_limit
            if len(ship_ids) > mine_limit:
                planet_location = (planet.location_x, planet.location_y)
                sorted_planets = self.planets_sorted_by_distance(planet_location)
                i = 0
                print "Moving", len(ship_ids), "ships"
                while(len(ship_ids) > mine_limit):
                    destination_planet = sorted_planets[i]
                    destination = (destination_planet.location_x,
                                   destination_planet.location_y)
                    num_ships_to_move = destination_planet.mine_limit
                    if len(ship_ids) - num_ships_to_move < mine_limit:
                        # prevents edge case where mine limit is 30
                        # and we have 50 ships on the planet.
                        # if we move all 50 ships, that's too much so
                        # move 50 - 30 = 20 ships instead which is desired behaviour
                        num_ships_to_move = len(ship_ids) - mine_limit
                    print "moving", num_ships_to_move, "ships with", len(ship_ids) - num_ships_to_move, "left"
                    ships_to_move = ship_ids[-num_ships_to_move:]
                    self.db.move_ships(destination, ships_to_move)
                    ship_ids = ship_ids[:-num_ships_to_move]
                    moved_ships.append(ships_to_move)
                    i = i + 1
                    print "Planet", planet_id, "has", num_ships_to_move, "ships."
        return moved_ships

    def planets_sorted_by_distance(self, source_location):
        # array of (<planet record>, <distance to planet>) tuples
        planet_locations = []
        for planet in self.planets:
            destination_location = (planet.location_x, planet.location_y)
            distance = self.distance(source_location, destination_location)
            planet_locations.append((planet, distance))
        compare_planets = lambda planet1, planet2: int(planet1[1] - planet2[1])
        sorted_planets = sorted(planet_locations,cmp=compare_planets)
        sorted_planets = [planet for planet, distance in sorted_planets]
        return sorted_planets[1:] # first element will be the source location

    def distance(self, a, b):
        import math
        ax, ay = a
        bx, by = b

        delta_x = math.pow( ax-bx, 2 )
        delta_y = math.pow( ay-by, 2 )

        return math.pow( delta_x + delta_y, 0.5 )

