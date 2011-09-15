import struct, socket

COMMAND_REQUEST = 1
COMMAND_RESPONSE = 2

RIP_VERSION = 2

class UpdatePacket:
    
    
    
    def __init__(self, first, second = None):
	self.routes = []
	self.routerId = None
	if (second == None):
	    self.fromString(first)
	else:
	    self.fromRoutes(first, second)
	
	
    def fromString(self, dataString):
	#print dataString
	(command, version, sender) = struct.unpack_from("!BBH", dataString);
	self.routerId = sender
	#print "Command: {}, Version: {}, Sender: {}".format(command, version, sender)
	offset = 4;
	while len(dataString)-offset >= 20:
	    (afi, zero, address, zero, zero, metric) = struct.unpack_from("!HHIIII", dataString, offset);
	    self.routes.append((address, sender, -1, metric))
	    #print "AFI: {}, Address: {}, Metric: {}".format(afi, address, metric)
	    offset += 20
	#print len(dataString)-offset

    def fromRoutes(self, routerId, routes):
	self.routerId = routerId
	self.routes = routes
	
    def getRouterId(self):
	return self.routerId
	
    def getRoutes(self):
	return self.routes

    def __str__(self):
	#print "AF_INET = " + str(socket.AF_INET)
	#RIP Header
	# |command(1) | version(1) |   zeros (2)	|
	ret = struct.pack("!BBH",COMMAND_RESPONSE, RIP_VERSION, self.routerId)
	
	for (dest, sender, outport, metric) in self.routes:
	    ret += struct.pack("!HHIIII",socket.AF_INET, 0, dest, 0, 0, metric)
	
	
	return ret
    