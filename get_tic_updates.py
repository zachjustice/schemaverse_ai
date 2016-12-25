from schemaverse_ai import FleetController
import time
import sys
# read from password file 
try:
    lines = [line.rstrip('\n') for line in open('.password')]
    user, password = lines
except Exception, e:
    traceback.print_exc("COULDN'T GET PASSWORD OR USERNAME", e)
    exit(0)

conn_str = "host=db.schemaverse.com dbname=schemaverse user=" + user + " password=" + password

wilhelm = FleetController(conn_str)

prev_tic = 0
sleep_time = 60
while( True ):
    cur_tic = wilhelm.get_current_tic()

    if prev_tic != cur_tic:
        prev_tic = cur_tic
        sleep_time = 60
        sys.stdout.write( "\nCurrent tic is " + str(cur_tic) )
    else:
        sys.stdout.write('.')
    sys.stdout.flush()
    time.sleep( sleep_time )
