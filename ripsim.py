#!/usr/bin/python

import ConfigParser, sys, socket, time, select, packets, routing_table
from route import Route

updatePeriod = 30
timeout = 180

'''Get the Metric to a Neighbour'''
def getMetricTo(dest):
      for (port, routerId, metric) in outputports:
            if (dest == routerId):
                  return metric
      return 16

'''Get the output port to a neighbour'''
def getOutputPortTo(router):
      for (portNum, routerId, metric) in outputports:
            if int(routerId) == int(router):
                  return portNum
      return 1111
      
'''Send an update to all neighbours (if target is None) or a single neighbour (if target != None)'''
def sendUpdate(myId, routes, target = None):

      for (outPort, outRouterId, outMetric) in outputports:
	    if (target == None or target == outRouterId):
		  outroutes = []
      
		  for route in routes:		
		  
			# Poisoned reverse
			if route.sender == outRouterId:
			      route = Route(route.dest, route.sender, route.outport, 16)
			
			if not route.dest == outRouterId:
			      outroutes.append(route)
			
			updatePacket = packets.RIPPacket(myId, outroutes, packets.COMMAND_RESPONSE)
			message = str(updatePacket)
			outsocket.sendto(message, ('127.0.0.1', int(outPort)))
			
			
'''Send a broadcasted request packet'''
def sendRequest(myId, routes):
    print "Sending request packet"
    requestPacket = packets.RIPPacket(myId, routes, packets.COMMAND_REQUEST)
    message = str(requestPacket)
    for (outPort, outRouterId, outMetric) in outputports:
	outsocket.sendto(message, ('127.0.0.1', int(outPort)))


if len(sys.argv) < 2: 
      print "Usage:", sys.argv[0], "<config file>"
      
else:
      
      #Read config file
      
      configfile = sys.argv[1]
      config = ConfigParser.ConfigParser()
      config.read(configfile)

      myId = config.getint('RIP', 'router-id')
      #boganname = config.get('RIP', 'bogan-name')
      
      updatePeriod = 30;
      
      if config.has_option('RIP', 'update-interval'):
	    updatePeriod = config.getint('RIP', 'update-interval')
	    
      if config.has_option('RIP', 'neighbour-timeout'):
	    timeout = config.getint('RIP', 'neighbour-timeout')
      else:
	    timeout = 6 * updatePeriod
	    
      
      
      outputports = []
      inputports = []
      insockets = []


      
      routingTable = routing_table.RoutingTable(myId)
      
      #Create the output socket
      outsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

      #Read port information from config file

      for inport in config.get('RIP', 'input-ports').split(','):
            inputports.append(int(inport.strip()))

      for outport in config.get('RIP', 'output-ports').split(','):
            (port, routerId, metric) = outport.strip().split('-')
            outputports.append((int(port), int(routerId), int(metric)))
            

      print "I am", myId
      print "I listen on:", inputports
      print "I connect to:", outputports
             
      for port in inputports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('127.0.0.1', int(port)))
        
        insockets.append(sock)
        
      routingTable.printTable()
      
      sendRequest(myId, routingTable.routes)
            
      while True:
 
	    sendUpdate(myId, routingTable.getRoutes())

            starttime = time.time()
            blockduration = 0
            
            while blockduration < updatePeriod:
		readyInputs, [], [] = select.select(insockets, [], [], updatePeriod)
		
		triggeredUpdateRequired = False
		
		for insock in readyInputs:
		    inmessage = insock.recv(1024)
		    
		    inPacket = packets.RIPPacket(inmessage)
		    
		    #print "COMMAND:", inPacket.command
		    
		    if inPacket.command == packets.COMMAND_REQUEST:
			print "REQUEST RECEIVED FROM", inPacket.routerId
			sendUpdate(myId, routingTable.getRoutes(), inPacket.routerId)
		    else:
		    
			#inPacket = packets.UpdatePacket(inmessage)
			#print inmessage
			#get routes from received data
			for route in inPacket.getRoutes():
				newOutport = getOutputPortTo(route.sender)
				#figure out the metric of the new route
				newMetric = min(int(route.metric) + int(getMetricTo(route.sender)), 16) 
				route = Route(route.dest, route.sender, newOutport, newMetric)
				triggeredUpdateRequired |= routingTable.processRoute(route)

		newDeadNeighbours = routingTable.checkNeighbours(timeout)
		if newDeadNeighbours:
		    print "DEAD NEIGHBOURS"
		    triggeredUpdateRequired = True
		
		if triggeredUpdateRequired:
		    print "TRIGGERED UPDATE"
		    sendUpdate(myId, routingTable.getRoutes())
		
		print
		print "I am", myId
		print "My neighbours are", routingTable.getNeighbours(), ", my ex-neighbours are", routingTable.getDeadNeighbours()
		print "So here's my routing table at the moment:"
		routingTable.printTable()
		print "\n"
		
		blockduration = time.time() - starttime
