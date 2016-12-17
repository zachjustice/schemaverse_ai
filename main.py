import psycopg2 #import postgresql connection library
import time
from psycopg2.extras import DictCursor

# read from password file 
lines = [line.rstrip('\n') for line in open('.password')]
user, password = lines

conn_str = "host=db.schemaverse.com dbname=schemaverse user=" + user + " password=" + password

conn = psycopg2.connect( conn_str ) #establish DB connection
conn.autocommit = True #disable transactions (transactions left uncommitted will hang the game)

def play_schemaverse(conn):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) #create database cursor. parameter grabs result as dict (which is not default)

    # Game Constants
    SHIP_COST = 1000

    cur.execute("SELECT last_value FROM tic_seq;") #run command
    results = cur.fetchone() #grab 1 row from results
    tic_num = results[0]
    #do stuff
    print "SANITY CHECK. TIC NUM:", tic_num

    # TODO check if I need fuel and how much
    # refuel ships
    query ="""
    SELECT refuel_ship(id) FROM my_ships;
    """
    cur.execute(query)

    # convert remaining fuel to money
    query ="SELECT balance, convert_resource('FUEL', my_player.fuel_reserve) FROM my_player;"
    cur.execute(query)
    results = cur.fetchone()
    balance, converted_fuel = results
    balance = balance + converted_fuel
    print "Converted", converted_fuel, "fuel."
    print "Total money:", balance

    query = "SELECT planet_location FROM planets_in_range LIMIT 1;"
    cur.execute(query)
    results = cur.fetchone()
    print "Planet Location Results:",results
    if results != None:
        planet_location = results[0]

    # make as many ships as possible
    if balance / SHIP_COST > 0:
        query = """
            INSERT INTO my_ships(
                attack,
                defense,
                engineering,
                prospecting,
                location
            ) 
            VALUES
        """
        for i in range( balance / SHIP_COST ):
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
            query = query + ship_str
        query = query[:-1] # remove last comma
        cur.execute( query )

        # ships are created now update them to mining
        query = """
        UPDATE my_ships s
        SET action='MINE', action_target_id=pir.planet
        FROM planets_in_range pir WHERE s.id = pir.planet and pir.distance = 0;
        """
        cur.execute(query)

    # move ships to planets
    query = """
    WITH tt_count AS (
        SELECT
            COUNT(ship) AS "ships_on_planet",
            planet
        FROM planets_in_range
        WHERE distance = 0
        GROUP BY planet
    )
    SELECT
        p.mine_limit,
        COUNT(ship) as "num_ships_on_planet",
        ARRAY_AGG(ship) as "ships_on_planet"
    FROM planets_in_range pir
    JOIN planets p
    ON p.id = pir.planet
    WHERE 
        (SELECT ships_on_planet
        FROM tt_count
        WHERE tt_count.planet = pir.planet) > p.mine_limit
    GROUP BY pir.planet, p.location_x, p.location_y, p.mine_limit
    """
    cur.execute(query)
    ships_to_move_by_planet = cur.fetchall()

    query = """
    SELECT
        p.location_x, p.location_y
    FROM
        planets p
    WHERE p.id NOT IN (SELECT DISTINCT planet FROM planets_in_range)
    """
    cur.execute(query);
    unvisited_planets = cur.fetchall()
    curr_planet_index = 0

    for planet_record in ships_to_move_by_planet:
        mine_limit, num_ships, ships = planet_record
        for i in range(num_ships - mine_limit):
            ship = ships[i]
            query = "SELECT SHIP_COURSE_CONTROL( %s, current_fuel / 2, null, POINT(%s, %s) ) FROM my_ships WHERE id = %s;"
            x, y = unvisited_planets[curr_planet_index]
            curr_planet_index = curr_planet_index + 1 % len(unvisited_planets)
            data = [ship, x, y, ship]
            cur.execute(query, data)

    conn.commit() #commit any database changes
    cur.close() #close cursor

prev_tic = 0
sleep_time = 60
increment = 5
while( True ):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) #create database cursor. parameter grabs result as dict (which is not default)
    cur.execute("SELECT last_value FROM tic_seq;") #run command
    results = cur.fetchone() #grab 1 row from results
    cur_tic = results[0]
    conn.commit()
    cur.close

    if prev_tic != cur_tic:
        sleep_time = 60
        increment = 5
        play_schemaverse( conn )
    elif sleep_time < 60*5:
        sleep_time = sleep_time + increment
        increment = increment + 5
    time.sleep( sleep_time )

conn.close() #close connection
