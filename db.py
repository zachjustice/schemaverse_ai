import psycopg2 #import postgresql connection library
from psycopg2.extras import NamedTupleConnection
import traceback

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

    def execute_blind(self, query, data=None):
        cur = self.execute(query, data)
        cur.close()

    def execute(self, query, data=None):
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
        try:
            if data == None:
                cur.execute(query)
            else:
                cur.execute(query, data)
        except Exception, e:
            traceback.print_stack()
            print "ERROR WITH QUERY: '" + query + "'"
        return cur

    def get_current_tic(self):
        query = "SELECT last_value FROM tic_seq;"
        return self.fetchone(query).last_value

    def convert_fuel_to_money(self, amount=None):
        if amount == None:
            query ="SELECT convert_resource('FUEL', my_player.fuel_reserve)\
                    FROM my_player;"
        else:
            query ="SELECT convert_resource('FUEL', %s) FROM my_player;"
        
        converted_fuel = self.fetchone(query, [amount])
        return converted_fuel

    def get_my_player_info(self):
        query ="""\
            SELECT
                id,
                balance,
                fuel_reserve
            FROM my_player;"""
        player_info = self.fetchone(query)
        return player_info

    def move_ships(self, planet_destination, ship_ids):
        query = """\
        SELECT 
        SHIP_COURSE_CONTROL(id, current_fuel / 2, null, POINT%s) 
        FROM my_ships 
        WHERE id = ANY(%s)"""
        data = [planet_destination,ship_ids]
        self.execute_blind(query, data)

    def create_ships(self, ships_to_create):
        query = "INSERT INTO my_ships( attack, defense, engineering, prospecting, location) VALUES"
        ship_str = " ( 0,10,0,10, ( SELECT location FROM planets WHERE conqueror_id=GET_PLAYER_ID(SESSION_USER) ) ),"

        for i in range( ships_to_create ):
            query = query + ship_str

        query = query[:-1] # remove last comma
        query = query + " RETURNING id;"
        created_ship_ids = self.fetchall( query )
        return created_ship_ids

    # ship_actions is an array of arrays such that
    # [ 
    #   [ <action string>, action_target_id, <array of applicable ship ids>]
    #   ...
    # ]
    # bulk set ship actions will then string together a list of update queries
    # to update the ships to act on the corresponding action target
    def bulk_set_ship_actions(self, ship_actions):
        data = []
        bulk_query = ""
        simple_query = """
        UPDATE my_ships s
        SET action=%s, action_target_id=%s
        WHERE s.id = ANY(%s);
        """
        for ship_action in ship_actions:
            bulk_query = bulk_query + simple_query
            data = data + ship_action

        self.execute_blind(bulk_query, data)

    def set_ship_action(self, action, action_target_id, ship_ids):
        query = """
        UPDATE my_ships s
        SET action=%s, action_target_id=%s
        WHERE s.id = ANY(%s);
        """
        data = (action, action_target_id, ship_ids)
        self.execute_blind(query, data)

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
    
    def refuel_ships(self):
        query = "SELECT refuel_ship(id) FROM my_ships WHERE current_fuel < max_fuel"
        self.execute_blind(query)

