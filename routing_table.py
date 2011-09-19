import time
from route import Route

class RoutingTable:

    def __init__(self, thisRouter):
	self.thisRouter = thisRouter
	self.routes = []
	self.neighbours = []
	self.deadneighbours = []
	
	#add a route to myself with port number 0 and metric 0
	self.routes.append(Route(dest=self.thisRouter,sender=self.thisRouter, outport=0, metric=0)) 
	
    def getRoutes(self):
	return self.routes
	
    def processRoute(self, route):
	
	receivedDestDown = False
	
	if (route.dest == route.sender):
	    self.processNeighbour(route)
	    
	#if route.dest in self.deadneighbours:
	#    return
	
	
	haveRoute = False
	for r in self.routes:
	     if (r.dest == route.dest): 
		haveRoute = True
		if route.metric < r.metric or route.sender == r.sender:
		    self.routes.remove(r)
		    self.routes.append(route)
		    
		    if route.sender == r.sender and route.metric == Route.inf and r.metric != Route.inf:
			receivedDestDown = True
	    
	if not haveRoute:
	    self.routes.append(route)
	    
	return receivedDestDown
	    
    def processNeighbour(self, neighbour):
	timeNow = time.time()
	isNew = True
	for n in self.neighbours:
	    if n[0] == neighbour.dest:
		if (self.deadneighbours.count(neighbour.dest) > 0):
		    self.deadneighbours.remove(neighbour.dest)
		self.neighbours.remove(n)
		self.neighbours.append((neighbour.dest, timeNow))
		isNew = False
	if isNew:
	    self.neighbours.append((int(neighbour[0]), timeNow))
    
    def checkNeighbours(self, timeout):
	newDeadNeighbours = False
	for n in self.neighbours:
	    if n[1]+timeout < time.time():
		self.deadneighbours.append(n[0])

		routes = []
		for route in self.routes:
		    if ((int(route.dest) == int(n[0])) or (int(route.sender) == int(n[0]))):
			routes.append(Route(route.dest, route.sender, route.outport, 16))
			newDeadNeighbours = True
		    else:
			routes.append(route)
		self.routes = routes
		self.printTable()
		self.neighbours.remove(n)

	return newDeadNeighbours
    
    def getNeighbours(self):
	self.neighbours.sort()
	return [n[0] for n in self.neighbours]
	
    def getDeadNeighbours(self):
	return self.deadneighbours
	

    
    def printTable(self):
	self.routes.sort()
	print "Dest\t| Sender\t| OutPort\t| Metric"
	print "-------------------------------------------"
	for route in self.routes:
	    if not (route.metric == 16): formattedMetric = str(route.metric)
	    else: formattedMetric = "inf"
	    print "{}\t| {}\t\t|  {}\t\t|  {}".format(route.dest, route.sender, route.outport, formattedMetric)
