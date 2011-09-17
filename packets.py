import struct, socket
from route import Route
COMMAND_REQUEST = 1
COMMAND_RESPONSE = 2

RIP_VERSION = 2

class RIPPacket:

    def __init__(self, first, second = None, third = None):
	self.routes = []
	self.routerId = None
	self.command = COMMAND_RESPONSE
	if (second == None):
	    self.fromString(first)
	elif third != None:
	    self.fromRoutes(first, second, third)
	
	
    def fromString(self, dataString):
	#print dataString
	(command, version, sender) = struct.unpack_from("!BBH", dataString);
	self.routerId = sender
	self.command = command
	#print "Command: {}, Version: {}, Sender: {}".format(command, version, sender)
	offset = 4;
	while len(dataString)-offset >= 20:
	    (afi, zero, address, zero, zero, metric) = struct.unpack_from("!HHIIII", dataString, offset);
	    
	    self.routes.append(Route(dest=address, sender=sender, outport=-1, metric=metric))
	    
	    offset += 20
	#print len(dataString)-offset

    def fromRoutes(self, routerId, routes, command):
	self.routerId = routerId
	self.routes = routes
	self.command = command
	
    def getRouterId(self):
	return self.routerId
	
    def getRoutes(self):
	return self.routes

    def __str__(self):
	#print "AF_INET = " + str(socket.AF_INET)
	#RIP Header
	# |command(1) | version(1) |   zeros (2)	|
	ret = struct.pack("!BBH",self.command, RIP_VERSION, self.routerId)
	
	for route in self.routes:
	    ret += struct.pack("!HHIIII",socket.AF_INET, 0, route.dest, 0, 0, route.metric)
	
	
	return ret
