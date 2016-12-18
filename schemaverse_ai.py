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

        print "START OF TIC"
        print "Current Balance:", self.balance
        print "ships:", len(self.ships)
        print "planets:", len(self.planets)
        print "planets_in_range:", len(self.planets_in_range)
        print "ships_in_range:", len(self.ships_in_range)
        print "-----"

        self.create_ships()
        self.move_ships()

    def move_ships(self):
        ships_per_planet = {}
        for p in self.planets_in_range:
            if p.planet not in ships_per_planet:
                ships_per_planet[p.planet] = []
            else:
                print ships_per_planet[p.planet]
                ships_per_planet[p.planet] = ships_per_planet[p.planet].append(p.ship)

        print ships_per_planet
        for planet, ships in ships_per_planet:
            print planet, ships

    def create_ships(self):
        db = self.db
        if self.balance / self.ship_cost > 0:
            db.create_ships(int(self.balance / self.ship_cost))
        self.ships = db.get_my_ships()
        # ships are created now update them to mining

    def update_data(self):
        db = self.db
        self.ships = db.get_my_ships()
        self.planets = db.get_planets()
        self.planets_in_range = db.get_planets_in_range()
        self.ships_in_range = db.get_ships_in_range()
