from nyct_gtfs import NYCTFeed
import datetime
import sys
import csv
with open('stops.csv', newline='') as csvfile:
    stops = []
    name_counter = {}
    stopreader = csv.reader(csvfile, quotechar='|')
    for row in stopreader:
        if len(row[0]) < 4:
            stop = {
                'stop_id': row[0],
                'stop_name': row[1],
                'stop_service': row[2],
                'borough': row[3],
            }
            stops.append(stop)

stop_ids_url = 'https://openmobilitydata-data.s3-us-west-1.amazonaws.com/public/feeds/mta/79/20220615/original/stops.txt'

API_KEY = ''

def get_feed(line):
    feed = NYCTFeed(line, api_key=API_KEY)
    return feed

def get_stop_id_from_name(line, stop_name):
    for stop in stops:
        if stop['stop_name'] == stop_name and line in [*stop['stop_service']]:
            return stop['stop_id']
        
def get_stop_name_from_id(stop_id):
    # Checks if ID has N or S attached
    if len(stop_id) > 3:
        stop_id = stop_id[0:3]
    for stop in stops:
        if stop_id == stop["stop_id"]:
            return stop['stop_name']

def get_group(line):
    if line == "A" or line == "C" or line == "E":
       return("ACE")
    if line == "B" or line == "D" or line == "F" or line == "M":
       return("BDFM")
    if line == "G":
       return("G")
    if line == "J" or line == "Z":
       return("JZ")
    if line == "N" or line == "Q" or line == "R" or line == "W":
       return("NQRW")
    if line == "L":
       return("L")
    if line == "1" or line == "2" or line == "3" or line == "4" or line == "5" or line == "6" or line == "7" or line == "S":  
       return("1234567S") 

def get_line_stops(line):
    line_stops = []
    for stop in stops:
        if line in [*stop['stop_service']]:
            line_stop = {
                'stop_name': stop['stop_name'],
                'stop_id': stop['stop_id'],
                'borough': stop['borough'],
                'service': stop['stop_service']
            }
            line_stops.append(line_stop)
                
    return line_stops     
  
def get_trains_at_stop(lines, stop_name):    
    stop_id = get_stop_id_from_name(lines[0], stop_name)
    if stop_id == None:
        return print('Couldn\'t find a stop with name', stop_name, "on the", lines, "line")
    group = get_group(lines[0])
    
    groups = []
    line_ids = []
    feeds = []
    trains = []
    for line in lines:
        line_ids.append(line)
        line_ids.append(line+"X")
        group = get_group(line)
        if group in groups:
            continue
        groups.append(group)    
    print(groups)
    for group in groups:
        feeds.append(get_feed(group[0]))
    print(feeds)
    for feed in feeds:
        trains.append(feed.filter_trips(line_id=line_ids, headed_for_stop_id=[stop_id+"N", stop_id+"S"], underway=True))
    now = datetime.datetime.now()
    
    trains_to_stop = []
    for trainSet in trains:
        for train in trainSet:
            if(train.has_delay_alert):
                print('Delayed train:')
                print(train.route_id)
                print(train)
            for update in train.stop_time_updates:
                if update.arrival == None:
                    print('exiting early')
                    continue
                if ((update.stop_id == stop_id+"N" or update.stop_id == stop_id+"S")) and ((((update.arrival - now).seconds // 30) < 30) and (((update.arrival - now).seconds // 30) > 0)):
                    # print("Train:", line)
                    # print(train.headsign_text + "-bound", "(" + train.direction + ")")
                    trains_to_stop.append({
                        'line': train.route_id,
                        'direction': train.direction,
                        'arrival': update.arrival,
                        'time_to_stop': str((update.arrival - now).seconds // 30),
                        'requested_stop': update.stop_name,
                        'last_stop': get_stop_name_from_id(train.location),
                        'location_status': train.location_status,
                        'headsign': train.headsign_text,
                        'delay': train.has_delay_alert,
                        'train_id': train.trip_id
                    })
                    # print('Arriving at', update.stop_name, 'in', ((update.arrival) - now).seconds // 30, 'minutes at', update.arrival.time())
                    # print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    return trains_to_stop

# if len(sys.argv) <= 1:
#     sys.exit(1)
# if sys.argv[1] == 'f': 
#     get_F_trains()
    
# if sys.argv[1] == 'g':
#     get_G_trains()
# else:
#     pass

# print('-------------------------')
# feed = get_feed("L")
# trains = feed.filter_trips(line_id="L", headed_for_stop_id=["L29N", "L29S"], underway=True)

# for train in trains:
#     if(train.has_delay_alert):
#         print('Delayed train:')
#         print(train.route_id)
#         print(train)
#     for update in train.stop_time_updates:
#         print(update)

