import psycopg2 #import postgresql connection library
from psycopg2.extras import DictCursor
conn = psycopg2.connect("host=db.schemaverse.com dbname=schemaverse user=username password=PASSWORD") #establish DB connection
conn.autocommit = True #disable transactions (transactions left uncommitted will hang the game)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) #create database cursor. parameter grabs result as dict (which is not default)

cur.execute("SELECT username, balance, fuel_reserve FROM my_player;") #run command
results = cur.fetchone() #grab 1 row from results
#do stuff
print results

conn.commit() #commit any database changes
cur.close() #close cursor
conn.close() #close connection
