import flaskr.api.nyct_api as nyct_api

def get_all_line_stops():
    lines = ["1", "2", "3", "4", "5", "6", "A", "C", "E", "G", "7", "B", "D", "F", "M", "J", "Z",
                "N", "Q", "R", "W", "L", "S"]

    line_stops = []

    for line in lines:
        stops = nyct_api.get_line_stops(line)
        line_stops.append({
            'line': line,
            'stops': stops
        })
        

    return line_stops

get_all_line_stops()

