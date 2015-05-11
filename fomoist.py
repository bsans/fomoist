#!python

import json
import itertools
import logging
from datetime import datetime, timedelta
from multiprocessing import Pool
import sqlite3

import requests
import facebook
from flask import Flask, g
from flask import render_template

app = Flask(__name__)

# The Stupid Shit No One Needs & Terrible Ideas Hackathon
# EVENT_ID = 1567576990198712

# Everyhere Logistics Junior Ranger Program at Sunday Streets
EVENT_ID = 1423979991242356

# has lat/lon: 37.7623836,-122.4191881

AUTH_TOKEN = 'DO_THE_MACARENA'

TIMEZONE = 'America/Los_Angeles'

PLACE_LAT_LON = '37.7623836,-122.4191881'

graph = facebook.GraphAPI(access_token=AUTH_TOKEN)


### Flask stuff

@app.route("/")
def shame_fomoists():
  db = get_db()
  db.row_factory = sqlite3.Row
  row = query_db("select * from cache order by id DESC LIMIT 1", one=True)
  all_events = json.loads(row['all_events'])
  fomoists = json.loads(row['fomoists'])  # {'id': [event indices]}
  people = json.loads(row['people'])  # is a dict {'id': {'name': name_val}}
  return render_template('fomoists.html', user_ids=fomoists.keys(), people=people)


@app.route("/write_to_cache")
def write_cache():
  backend()
  return "Done!"

@app.route("/read_from_cache")
def read_cache():
  db = get_db()
  db.row_factory = sqlite3.Row
  row = query_db("select * from cache order by id DESC LIMIT 1", one=True)
  return "%s\n%s" % (row['all_events'], row['fomoists'])


@app.route("/test_db")
def test_db():
  db = get_db()
  db.row_factory = sqlite3.Row
  result = []
  for bla in query_db('select * from test'):
    logging.warning("%s, %s", bla['id'], bla['name'])
    result.append(bla)

  return "result: %s" % result

@app.route("/write_to_db")
def write_to_db():
  db = get_db()
  insert_to_db('insert into test(name) values("bla bla");')
  return ""


### Backend

def query_for_event(event_id):
  return graph.get_object(str(event_id))


def query_for_places(lat_lon=PLACE_LAT_LON):
   # /search?
   #  q=coffee&
   #  type=place&
   #  center=37.76,-122.427&
   #  distance=1000

   # This is probably never going to be useful for us...too specific
   # 'q': event['location'],

  query_args = {'type': 'place',
                'center': lat_lon,
                'distance': '1000'}
  result = graph.request('search', query_args)
  return result


def query_for_events_by_location_name(name):
  query_args = {'q': name.encode('ascii', 'ignore'),
                'type': 'event'}
  result = graph.request('search', query_args)
  # do more filtering here, e.g. no events in Lima Peru

  return result


def datetime_from_iso(iso_time):
  """Parse datetime from a ISO8601 time string

  Must be able to accommodate time strings with no UTC offset
  """
  # "start_time": "2015-05-23T10:00:00-0700",
  # "end_time": "2015-05-23T20:00:00-0700",
  if iso_time is None:
    return iso_time

  try:
    return datetime.strptime(iso_time.rsplit("-", 1)[0], "%Y-%m-%dT%H:%M:%S")
  except ValueError:
    try:
      return datetime.strptime(iso_time, "%Y-%m-%dT%H:%M:%S")  # no UTC offset
    except ValueError:
      try:
        return datetime.strptime(iso_time, "%Y-%m-%d")  # assume no UTC offset
      except ValueError:
        try:
          return datetime.strptime(iso_time, "%Y-%m")  # assume no UTC offset
        except ValueError:
          try:
            return datetime.strptime(iso_time, "%Y")  # assume no UTC offset
          except:
            logging.warning("what! iso_time: %s", iso_time)


def time_overlaps(start_time,
                  end_time,
                  event_start,
                  event_end,
                  SLOP_FACTOR=timedelta(0)):
  # end_time can be None
  # CASE 1: edge overlaps
  if (event_start > start_time - SLOP_FACTOR and event_start < end_time + SLOP_FACTOR) or \
     (event_end and event_end > start_time - SLOP_FACTOR and event_end < end_time + SLOP_FACTOR):
    return True
  # CASE 2: end equalities
  elif event_start == start_time or event_end == end_time:
    return True
  # CASE 3: completely within and vice versa
  elif event_end and (event_start < end_time + SLOP_FACTOR and event_end > start_time - SLOP_FACTOR):
    return True


def check_time_overlaps(e, end_time, start_time):
  return time_overlaps(start_time,
                       end_time,
                       datetime_from_iso(e['start_time']),
                       datetime_from_iso(e.get('end_time')))


def filter_events(events, start_time, end_time, timezone=TIMEZONE):
  """
  :param list events:
  :param start_time: ISO8601 time
  :param end_time: ISO8601 time
  """
  global events_without_timezone_counter
  start_time = datetime_from_iso(start_time)
  end_time = datetime_from_iso(end_time)
  filtered_events = []
  for e in events:
    if not e.get('timezone'):
      events_without_timezone_counter.next()
      # include and time filter events without timezone for now because they may be relevant
      if check_time_overlaps(e, end_time, start_time):
        filtered_events += [e]
    elif e['timezone'] == timezone and \
        check_time_overlaps(e, end_time, start_time):
      filtered_events += [e]

  return filtered_events

def find_people(events_attendees):
  people = {}
  for attendees in events_attendees:
    for attendee in attendees:
      people[attendee['id']] = { 'name': attendee['name'] }
  return people

def find_fomoists(events_attendees, rsvp_statuses=['attending']):
  """
    "events" is a list of lists of attendees:

    [
        [
          {
            "name": "Brittany Miller",
            "rsvp_status": "attending",
            "id": "1442173849420454"
          },
          ...
        ]
      ...
    ]

    "rsvp_statuses" is a list of event attendance statuses to consider

    Returns a dict of of fomoists where the key is a person ID and the value is
    a list of events the person is attending. Events are represented by their
    index in the "events" parameter.

  """
  fomoists = {}
  for i, e in enumerate(events_attendees):
    for p in e:
      if p['rsvp_status'] in rsvp_statuses:
        pid = p['id']
        if pid not in fomoists:
          fomoists[pid] = []
        fomoists[pid] += [i]
  for pid in fomoists.keys():
    if len(fomoists[pid]) < 2:
      del fomoists[pid]
  return fomoists


def find_all_events_attendees(all_events):
  all_events_attendees = []
  for e in all_events:
    attendees = get_all_attendees(e['id'])
    all_events_attendees += [attendees]
  return all_events_attendees


def get_all_attendees(event_id=EVENT_ID):
  all_attendees = []
  first_call = graph.get_connections(id=str(event_id), connection_name='attending')
  all_attendees += first_call['data']
  if not first_call.get('paging'):
    return all_attendees

  next_url = first_call.get('paging').get('next')
  while next_url:
    attendees_response = requests.get(next_url).json()
    all_attendees += attendees_response['data']
    next_url = attendees_response.get('paging').get('next')

  return all_attendees


# Globals!

event = None
all_events_counter = itertools.count()
events_without_timezone_counter = itertools.count()


def get_and_filter_events(place):
  global all_events_counter
  unfiltered_events = query_for_events_by_location_name(place['name'])
  logging.warning("unfiltered events found: %s", len(unfiltered_events['data']))
  for e in unfiltered_events['data']:
    all_events_counter.next()

  return filter_events(unfiltered_events['data'], event['start_time'], event['end_time'])


def backend():
  global event

  # event_id is the starting point for querying with location and times to fan out
  # into who is "attending" to events

  event = query_for_event(EVENT_ID)
  logging.warning("event fetched: %s", event)
  places = query_for_places()
  num_places = len(places['data'])
  logging.warning("%s places found", num_places)

  pool = Pool(1)
  all_events_mess = pool.map(get_and_filter_events, places['data'][:1000])

  all_events = []
  for sublist in all_events_mess:
    all_events += sublist

  num_events = len(all_events)
  logging.warning('all events found: %s', num_events)
  all_events_attendees = find_all_events_attendees(all_events)
  total_attendees = 0
  assert isinstance(all_events_attendees, list)
  for i in all_events_attendees:
    assert isinstance(i, list)
    total_attendees += len(i)

  logging.warning("total attendees found: %s", total_attendees)

  fomoists = find_fomoists(all_events_attendees)
  people = find_people(all_events_attendees)
  # is a dict, keyed by uid

  num_fomoists = len(fomoists)
  logging.warning('total fomoists double-booked or worse: %s', num_fomoists)
  scoped_all_events_counter = all_events_counter.next()
  scoped_events_without_timezone_counter = events_without_timezone_counter.next()

  serialized_all_events = json.dumps(all_events)
  serialized_fomoists = json.dumps(fomoists)
  serialized_people = json.dumps(people)
  insert_to_db('insert into cache(all_events, fomoists, people) values(?,?, ?)',
               (serialized_all_events, serialized_fomoists, serialized_people))


### DB


DATABASE = '/Users/Bodhi/projects/fomoist/database.db'


def connect_to_database():
  return sqlite3.connect(DATABASE)


def get_db():
  logging.warning("connecting to db")
  db = getattr(g, '_database', None)
  if db is None:
      db = g._database = connect_to_database()
  return db


def query_db(query, args=(), one=False):
  logging.warning("querying db for: %s" % query)
  cur = get_db().execute(query, args)
  rv = cur.fetchall()
  cur.close()
  return (rv[0] if rv else None) if one else rv


def insert_to_db(query, args=()):
  cur = get_db().execute(query, args)
  logging.warn(cur)
  get_db().commit()
  cur.close()


@app.teardown_appcontext
def close_connection(exception):
  logging.warning("closing db connection")
  db = getattr(g, '_database', None)
  if db is not None:
      db.close()


def init_db():
  """Special function only needed during initial setup
  """
  with app.app_context():
      db = get_db()
      with app.open_resource('schema.sql', mode='r') as f:
          db.cursor().executescript(f.read())
      db.commit()


### Magic

if __name__ == "__main__":
  app.run(debug=True)
