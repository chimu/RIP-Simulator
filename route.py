from collections import namedtuple

Route = namedtuple('Route', 'dest sender outport metric')
Route.inf = 16