import psycopg2 #import postgresql connection library
from psycopg2.extras import NamedTupleConnection

class db:
    
    def __init__(self, conn_str):
        self.conn = psycopg2.connect( conn_str ) #establish DB connection
        self.conn.autocommit = True #disable transactions (transactions left uncommitted will hang the game)

    def fetchall(self, query, data=None):
        cur = self.execute(query, data)
        results = cur.fetchall()
        cur.close()
        return results

    def fetchone(self, query, data=None):
        cur = self.execute(query, data)
        results = cur.fetchone()
        cur.close()
        return results

    def execute(self, query, data=None):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
        try:
            if data == None:
                cur.execute(query)
            else:
                cur.execute(query, data)
        except Exception, e:
            print "Query failed:", e
        return cur

    def convert_fuel_to_money(self, amount=None):
        if amount == None:
            query ="SELECT convert_resource('FUEL', my_player.fuel_reserve) FROM my_player;"
        else:
            query ="SELECT convert_resource('FUEL', %s) FROM my_player;"
        
        converted_fuel = self.fetchone(query, [amount])
        return converted_fuel

    def get_player_balance(self):
        query ="SELECT balance FROM my_player;"
        results = self.fetchone(query)
        return results.balance

    def create_ships(self, ships_to_create):
        query = """
            INSERT INTO my_ships(
                attack, defense, engineering, prospecting, location
            ) VALUES
        """
        ship_str = """ (
            5,5,5,5,
            (
                SELECT
                    location
                FROM
                    planets
                WHERE
                    conqueror_id=GET_PLAYER_ID(SESSION_USER)
            )
        ),"""

        for i in range( ships_to_create ):
            query = query + ship_str

        query = query[:-1] # remove last comma
        created_ships = self.execute( query )

        query = """
        UPDATE my_ships s
        SET action='MINE', action_target_id=pir.planet
        FROM planets_in_range pir WHERE s.id = pir.planet and pir.distance = 0;
        """
        self.execute(query)
        return created_ships

    def get_my_ships(self):
        query = """
            SELECT 
                id,
                name,
                current_health,
                max_health,
                current_fuel,
                max_fuel,
                max_speed,
                range,
                attack,
                defense,
                engineering,
                prospecting,
                location_x,
                location_y,
                direction,
                speed,
                destination_x,
                destination_y,
                action,
                action_target_id,
                location,
                destination,
                target_speed,
                target_direction
            FROM
                my_ships;"""
        ships = self.fetchall(query)
        return ships

    def get_planets(self):
        query = """
            SELECT 
                id,
                name,
                mine_limit,
                location_x,
                location_y,
                conqueror_id,
                location
            FROM
                planets;"""
        planets = self.fetchall(query)
        return planets

    def get_planets_in_range(self):
        query = """
            SELECT 
                ship,
                planet,
                ship_location,
                planet_location,
                distance
            FROM
                planets_in_range;"""
        planets_in_range = self.fetchall(query)
        return planets_in_range

    def get_ships_in_range(self):
        query = """
            SELECT 
                id,
                ship_in_range_of,
                player_id,
                name,
                health,
                enemy_location
            FROM
                ships_in_range;"""
        ships_in_range = self.fetchall(query)
        return ships_in_range

