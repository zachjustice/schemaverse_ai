import psycopg2 #import postgresql connection library
from psycopg2.extras import DictCursor

# read from password file 
lines = [line.rstrip('\n') for line in open('.password')]
user, password = lines

conn_str = "host=db.schemaverse.com dbname=schemaverse user=" + user + " password=" + password

conn = psycopg2.connect( conn_str ) #establish DB connection
conn.autocommit = True #disable transactions (transactions left uncommitted will hang the game)
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
new_ships = []
for i in range( balance / SHIP_COST ):
    query = """
        INSERT INTO my_ships(
            attack,
            defense,
            engineering,
            prospecting,
            location
        ) 
        VALUES(
            5,5,5,5,
            (
                SELECT
                    location
                FROM
                    planets
                WHERE
                    conqueror_id=GET_PLAYER_ID(SESSION_USER)
            )
        )
        RETURNING id;
    """
    cur.execute( query )
    new_ship = cur.fetchone()
    new_ships.append( new_ship )
    print "New Ship", new_ship

    query = "UPDATE my_ships s SET action='MINE', action_target_id=p.planet FROM planets_in_range p WHERE %s=p.ship;"
    cur.execute(query, new_ship) 

conn.commit() #commit any database changes
cur.close() #close cursor
conn.close() #close connection
