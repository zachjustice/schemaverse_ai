import psycopg2 #import postgresql connection library
from psycopg2.extras import NamedTupleConnection

class FleetController:

    def __init__(self, conn_str):
        from db import db
        self.db = db(conn_str)
        self.ship_cost = 1000

    def run(self):
        db = self.db
        self.update_data()
        db.convert_fuel_to_money()
        self.balance = db.get_player_balance()

        print "-----"
        print "TIC", db.get_current_tic()
        print "Current Balance:", self.balance
        print "ships:", len(self.ships)
        print "planets:", len(self.planets)
        print "planets_in_range:", len(self.planets_in_range)
        print "ships_in_range:", len(self.ships_in_range)
        print "-----"

        created_ship_ids = self.create_ships()
        self.mine(created_ship_ids)
        self.move_ships()

    def get_current_tic(self):
        return self.db.get_current_tic()

    def update_data(self):
        db = self.db
        self.ships = db.get_my_ships()
        self.planets = db.get_planets()
        self.planets_in_range = db.get_planets_in_range()
        self.ships_in_range = db.get_ships_in_range()

        self.planets_by_id = {}
        self.ships_by_id = {}
        
        for p in self.planets:
            self.planets_by_id[p.id] = p

        for s in self.ships:
            self.ships_by_id[s.id] = s

    def mine(self, ship_ids):
        db = self.db
        ship_actions = []
        for ship_id in ship_ids:
            planet_id = 0 # TODO fix
            ship_action = ('MINE', planet_id, [ship_id])

    def create_ships(self):
        db = self.db
        if self.balance / self.ship_cost > 0:
            db.create_ships(int(self.balance / self.ship_cost))
        self.ships = db.get_my_ships()
        # ships are created now update them to mining

    def move_ships(self):
        ships_per_planet = {}
        # dict{ planet id => [ list of ships on the planet ] }
        # this is so that we can move extra ships above the 
        # planet's mine limit somewhere else
        for p in self.planets_in_range:
            if p.planet not in ships_per_planet:
                ships_per_planet[p.planet] = []
            elif p.planet_location == p.ship_location:
                # only move ships to a different planet if the ship is *on* the planet
                ships_per_planet[p.planet].append(p.ship)

        for planet_id, ship_ids in ships_per_planet.iteritems():
            planet = self.planets_by_id[planet_id]
            mine_limit = planet.mine_limit
            if len(ship_ids) > mine_limit:
                planet_location = (planet.location_x, planet.location_y)
                sorted_planets = self.planets_sorted_by_distance(planet_location)
                i = 0
                print "Moving", len(ship_ids), "ships"
                while(len(ship_ids) > mine_limit):
                    destination_planet = sorted_planets[i][0]
                    destination = (destination_planet.location_x,
                                   destination_planet.location_y)
                    num_ships_to_move = destination_planet.mine_limit
                    if len(ship_ids) - num_ships_to_move < mine_limit:
                        # prevents edge case where mine limit is 30
                        # and we have 50 ships on the planet.
                        # if we move all 50 ships, that's too much so
                        # move 50 - 30 = 20 ships instead which is desired behaviour
                        num_ships_to_move = len(ship_ids) - mine_limit
                    print "moving %s with %s left", num_ships_to_move, len(ship_ids) - num_ships_to_move
                    self.db.move_ships(destination, ship_ids[-num_ships_to_move:])
                    ship_ids = ship_ids[:-num_ships_to_move]
                    i = i + 1
                    print "Planet", planet_id, "has", num_ships_to_move, "ships."

    def planets_sorted_by_distance(self, source_location):
        # array of (<planet record>, <distance to planet>) tuples
        planet_locations = []
        for planet in self.planets:
            destination_location = (planet.location_x, planet.location_y)
            distance = self.distance(source_location, destination_location)
            planet_locations.append((planet, distance))
        compare_planets = lambda planet1, planet2: int(planet1[1] - planet2[1])
        sorted_planets = sorted(planet_locations,cmp=compare_planets)
        sorted_planets = [planet for planet, distance in sorted_planet]
        return sorted_planets[1:] # first element will be the source location

    def distance(self, a, b):
        import math
        ax, ay = a
        bx, by = b

        delta_x = math.pow( ax-bx, 2 )
        delta_y = math.pow( ay-by, 2 )

        return math.pow( delta_x + delta_y, 0.5 )

