import time
import threading

from flask import request, url_for
from flask_api import FlaskAPI, status, exceptions


app = FlaskAPI(__name__)

client = None
streamer = None

def init_app(_client, _streamer):
    global client, streamer
    client = _client
    streamer = _streamer

def synchronized(lock):
    """ Synchronization decorator. """
    def wrap(f):
        def newFunction(*args, **kw):
            lock.acquire()
            try:
                return f(*args, **kw)
            finally:
                lock.release()
        return newFunction
    return wrap

glock = threading.Lock()

epics = {}

def epic_repr(epic):
    return request.host_url.rstrip('/') +url_for('epic_detail', epic=epic)

@synchronized(glock)
def list_epics():
    return [idx for idx in sorted(streamer.epic_details)]

@synchronized(glock)
def add_epic(epic):
    epics[epic] = 1
    streamer.subscribe_epic(epic)
    return epic

@synchronized(glock)
def update_epic(epic):
    epics[epic] = 1

@synchronized(glock)
def delete_epic(key):
    return epics.pop(key, None)

@app.route("/epics", methods=['GET', 'POST'])
def epics_list():
    """
    List or create epics
    """
    if request.method == 'POST':
        epic = str(request.data.get('epic', ''))
        add_epic(epic)
        return epic, status.HTTP_201_CREATED

    return list_epics()

@app.route("/epics/<epic>/", methods=['GET'])
def epic_detail(epic):
    """
    Retrieve, update or delete note instances.
    """
    epic_detail = streamer.epic_details.get(epic)
    if not epic or not epic_detail:
        raise exceptions.NotFound()
    return epic_detail

@app.route("/", methods=['GET'])
def heartbeat():
    local_t = time.localtime(streamer.last_heartbeat)
    utc_t = time.gmtime(streamer.last_heartbeat)
    return {"local": time.strftime('%Y-%m-%d %H:%M:%S', local_t),
            "utc": time.strftime('%Y-%m-%d %H:%M:%S', utc_t)
            }
