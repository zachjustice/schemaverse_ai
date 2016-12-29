Helpful tables and views

Views

my_player
    id
    username
    created
    balance
    fuel_reserve
    password
    error_channel
    starting_fleet
    symbol
    rgb

my_ships
    id
    fleet_id
    player_id
    name
    last action_tic
    last move_tic
    last living_tic
    current_health
    max health
    current_fuel
    max fuel
    max speed
    range
    attack
    defense
    engineering
    prospecting
    location_x
    location_y
    direction
    speed
    destination_x
    destination_y
    repair_priority
    action
    action_target_id
    location
    destination
    target_speed
    target_direction

planets_in_range
    ship
    planet
    ship_location
    planet_location
    distance

main.py
    Plays schemaverse using an AI
    In the future specific configurations of the AI will be determined here
schemaverse_ai.py
    An implementation of an ai to play schemaverse
db.py
    A class holding helpful queries for playing schemaverse
    I've used a class here so I don't need to use globals
