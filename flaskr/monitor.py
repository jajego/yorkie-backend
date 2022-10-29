from flask import Blueprint
from flask import flash
from flask import g
from flask import request
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import send_from_directory
from flask import current_app
from flask import session


from . import stationgetter

from werkzeug.exceptions import abort

# from . import api

import flaskr.api.nyct_api as nyct_api

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint("monitor", __name__)

@bp.route("/")
def index():
    lines = stationgetter.get_all_line_stops()
    # Checks headers of requests from frontend. Vulnerable because people can spoof headers, but CORS is a hurdle right now for session data between the frontend and backend
    requester_user_id = None
    headers = request.headers
    for header in headers:
        if header[0] == "User-Id":
            requester_user_id = header[1]
    print("Requester's user id is:", requester_user_id)
    db = get_db()
    # Gets all monitors
    monitors = db.execute(
        "SELECT m.id, user_id, created, line, other_service, station_name"
        " FROM monitor m JOIN user u ON m.user_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    
    monitors_json = []
    
    # Occurs if accessing self from backend
    if requester_user_id is None:
        for monitor in monitors:
            # Checks logged in user's id against pulled monitors, but would it be better to have only pulled the user's monitors in the first place?
            user_id = monitor['user_id']
            session_id = session.get("user_id")
            if user_id == session_id:
                monitors_json.append(
                    {
                        'line': monitor['line'], 
                        'stationName': monitor['station_name'],
                    }
                )
                
    # Requests from frontend
    elif requester_user_id is not None:
        print('Request to "/" from frontend')
        for monitor in monitors:
            # Checks logged in user's id against pulled monitors, but would it be better to have only pulled the user's monitors in the first place?
            user_id = monitor['user_id']
            if user_id == int(requester_user_id):
                line = monitor['line']
                stationName = monitor['station_name']
                monitorId = monitor['id']
                stopId = nyct_api.get_stop_id_from_name(line, stationName)
                service = ''
                otherService = monitor['other_service']
                # extract stop service
                for line in lines:
                    for stop in line['stops']:
                        if stopId == stop['stop_id']:
                            service = stop['service']
                
                
                monitors_json.append(
                    {
                        'line': line, 
                        'stationName': stationName,
                        'monitorId': monitorId,
                        'service': service,
                        'other_service': otherService 
                    }
                )
    return monitors_json

def get_username_from_id(db, user_id):
    user = db.execute(
        "SELECT username"
        " FROM user u WHERE u.id = %s" % user_id
    ).fetchone()
    return user['username']

def dict_from_row(row):
    return dict(zip(row.keys(), row))       


@bp.route("/trains")
def trains():
    """Show all the posts, most recent first."""
    requester_user_id = None
    headers = request.headers
    for header in headers:
            if header[0] == "User-Id":
                    requester_user_id = header[1]
   
    db = get_db()
    monitors = db.execute(
        "SELECT m.id, user_id, created, line, other_service, station_name"
        " FROM monitor m JOIN user u ON m.user_id = u.id WHERE m.user_id = %s" % requester_user_id 
    ).fetchall()
    trains_json = []
    for monitor in monitors:
        # Checks logged in user's id against pulled monitors, but would it be better to have only pulled the user's monitors in the first place?
        user_id = monitor['user_id']
        if user_id == int(requester_user_id):
            lines = []
            lines.append(monitor['line'])
            for line in list(monitor['other_service']):
                lines.append(line)
            trains_json.append({
                'line': monitor['line'],
                'station_name': monitor['station_name'],
                'trains': nyct_api.get_trains_at_stop(lines, monitor['station_name']),
                'monitorId': monitor['id'],
                'otherService': monitor['other_service']
            })
            
    return trains_json

@bp.route("/all-stops")
def all_stops():
    return stationgetter.get_all_line_stops()

def get_monitor(id):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    monitor = (
        get_db()
        .execute(
            "SELECT m.id, user_id, created, line, station_name"
            " FROM monitor m JOIN user u ON m.user_id = u.id"
            " WHERE m.id = ?",
            (id,),
        )
        .fetchone()
    )

    if monitor is None:
        abort(404, f"Monitor id {id} doesn't exist.")

    return monitor

@bp.route("/create", methods=("GET", "POST"))
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        requester_user_id = None
        headers = request.headers
        for header in headers:
            print(header)
            if header[0] == "User-Id":
                requester_user_id = header[1]
        json = request.get_json()
        
        line = json["line"]
        station_name = json["station_name"]
        other_service = json["other_service"]
        
        db = get_db()
        db.execute(
            "INSERT INTO monitor (line, station_name, other_service, user_id) VALUES (?, ?, ?, ?)",
            (line, station_name, other_service, requester_user_id),
        )
        db.commit()

    return json


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    monitor = get_monitor(id)

    if request.method == "POST":
        line = request.form["line"]
        station_name = request.form["station-name"]
        error = None

        if not line:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE monitor SET line = ?, station_name = ? WHERE id = ?", (line, station_name, id)
            )
            db.commit()
            return redirect(url_for("monitor.trains"))

    return render_template("monitor/update.html", monitor=monitor)


@bp.route("/<int:id>/delete", methods=("POST",))
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """

    requester_user_id = None
    headers = request.headers
    for header in headers:
        if header[0] == "User-Id":
            requester_user_id = header[1]
    if requester_user_id == None:
        return 'no user id given'
    
    monitor = get_monitor(id)
    db = get_db()
    db.execute("DELETE FROM monitor WHERE id = ?", (id,))
    db.commit()
    return 'Succesfull deletion'
