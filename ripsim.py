#!/usr/bin/python



#THINGS THAT AREN'T YET WORKING/IMPLEMENTED:
#Replacing a route with a shorter one doesn't actually get rid of the old one. This should be easy to fix.
#Route timeouts aren't implemented, so if a router goes offline the routes don't adapt...
#None of the split horizon with route poisoning stuff is in here.
#Probably a lot of other stuff is missing. I dunno.

import ConfigParser, sys, socket, time, select, packets

updatePeriod = 3
timeout = 6

def getMetricTo(dest):
      #for myRoute in routes:
      #      myDest, myFirstRouter1, myInterface, myMetric = myRoute
      #      if (int(dest) == int(myDest)):
      #            return myMetric
      
      for (port, routerId, metric) in outputports:
            if (dest == routerId):
                  return metric
      
      return 16

def getOutputPortTo(router):
      for (portNum, routerId, metric) in outputports:
            if int(routerId) == int(router):
                  return portNum
      return 1111

def printRoutingTable(routes):
    print "Dest\t| Sender\t| OutPort\t| Metric"
    print "-------------------------------------------"
    for (dest, sender, outport, metric) in routes:
	if not (metric == 16): formattedMetric = str(metric)
	else: formattedMetric = "inf"
	print "{}\t| {}\t\t|  {}\t\t|  {}".format(dest, sender, outport, formattedMetric)
	
def updateRoute(newRoute):
    for route in routes:
	if route[0] == newRoute[0]:
	    routes.remove(route)
	    routes.append(newRoute)
	    #route = newRoute
	  
def updateNeighbour(neighbour):
    timeNow = time.time()
    isNew = True
    for n in neighbours:
	if n[0] == neighbour[0]:
	    if (deadneighbours.count(dest) > 0):
		deadneighbours.remove(n[0])
	    neighbours.remove(n)
	    neighbours.append((neighbour[0], timeNow))
	    #print "Neighbour " + str(n[0]) + " updated" 
	    isNew = False
    if isNew:
	neighbours.append((neighbour[0], timeNow))
	
    #print "I HAVE {} NEIGHBOURS".format(len(neighbours))
    
def checkNeighbours():
    timeNow = time.time()
    #print "Time is {}".format(timeNow)
    for n in neighbours:
	if n[1]+timeout < timeNow:
	    print "DEAD NEIGHBOUR: " + str(n[0]) + " WITH TIME {}".format(n[1])
	    deadneighbours.append(n[0])
	    #routes.remove(n[0])
	    for route in routes:
		(dest, sender, outport, metric) = route
		if dest == n[0] or sender == n[0]:
		    routes.remove(route)
		    routes.append((dest, sender, outport, 16))
		    sendUpdate(myId, routes)
	    #(dest, sender, outport, metric) = n[0]
	    #triggeredUpdateRoutes = []
	    #triggeredUpdateRoutes.append(dest, sender, outport, 16)
	    
	    neighbours.remove(n)
	    
def sendUpdate(myId, routes):
    
    #print "RIP Packet has length: " + str(len(str(updatePacket)))
    print outputports
    for (outPort, outRouterId, outMetric) in outputports:
	    outroutes = []
	    print "I am " + str(myId)
	    #Poisoned reverse
	    for (dest, sender, outport, metric) in routes:
		if not (sender == outRouterId or dest == outRouterId):
		    outroutes.append((dest, myId, outport, metric))
		    print "Sending to " + str(outRouterId) + ": " + str((dest, myId, outport, metric))
		    
	    
	    print "Poisoned Reverse: Routes={}, Culled={}".format(len(routes), len(outroutes))
	    
	    updatePacket = packets.UpdatePacket(myId, outroutes)
	    message = str(updatePacket)
	    outsocket.sendto(message, ('127.0.0.1', int(outPort)))
	    #print "sending " + routeString

if len(sys.argv) < 2: 
      #if there are no arguments
      print "ARJHGKLW"
      
else:
      configfile = sys.argv[1]
      config = ConfigParser.ConfigParser()
      config.read(configfile)

      myId = config.getint('RIP', 'router-id')
      boganname = config.get('RIP', 'bogan-name')
      
      outputports = []
      inputports = []
      insockets = []
      routes = []
      neighbours = []
      deadneighbours = []
      
      outsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

      for inport in config.get('RIP', 'input-ports').split(','):
            inputports.append(int(inport.strip()))

      for outport in config.get('RIP', 'output-ports').split(','):
            (port, routerId, metric) = outport.strip().split('-')
            outputports.append((int(port), int(routerId), int(metric)))
            routes.append((int(routerId), int(myId), int(port), int(metric)))
      
      print outputports
      
      routes.append((myId, myId, 0, 0)) #add a route to myself with port number 0 and metric 0

      print "I am", boganname, "and my Id is", myId
      print "I listen on:", inputports
      print "I connect to:", outputports
      print "My routes are:", routes
             
      for port in inputports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('127.0.0.1', int(port)))
        
        insockets.append(sock)
            
      while True:
            #routeString = ""
            #for route in routes:
            #      dest, firstRouter, interface, metric = route
            #      routeString = routeString + str(dest) + '-' + str(myId) + '-' + str(metric) + '/'
            #routeString = routeString.rstrip('/')
            sendUpdate(myId, routes)

            starttime = time.time()
            readyInputs, [], [] = select.select(insockets, [], [], updatePeriod)
            blockduration = time.time() - starttime
                  

            #You can tell from the indenting here that this isn't exactly efficient...
            #Or readable...
            #Also at this point I have pretty much used strings and ints interchangeably
            #(due to slight laziness) hence the abundance of str() and int(). I'll fix
            #this later. Most of the locally-stored data should be ints though.
              
            for insock in readyInputs:
                  inmessage = insock.recv(1024)
                  inPacket = packets.UpdatePacket(inmessage)
                   #print inmessage
                   #get routes from received data
                  for route in inPacket.getRoutes():
                        (dest, sender, port, metric) = route
                        if (dest == sender):
			    print "NEIGHBOUR " + str(dest)
			    updateNeighbour((dest, sender, getOutputPortTo(sender), int(metric)))
			    
			if (deadneighbours.count(dest) > 0):
			    metric = 16;
                        #print "Router {} can get to {} with metric {}".format(sender, dest, metric)
                        #check if this is should be the new route
                        haveRoute = False
                        for myRoute in routes:
                              myDest, myFirstRouter, myInterface, myMetric = myRoute
                              if (int(dest) == myDest): #if i have a route with this dest
                                     haveRoute = True
                                     #print "I also have a route to "+dest
                                     #metric = metric + distance from me to the sender of this update (firstRouter)
                                     newMetric = min(int(metric) + int(getMetricTo(sender)), 16) #figure out the metric of the new route
                                     #print "If I use the new route it would have a metric of "+str(newMetric)
                                     if ((int(newMetric) < int(myMetric)) or (sender == myFirstRouter)):
					   #if sender == myFirstRouter:
					       #print "Sender wants me to have a metric of " + str(newMetric)
                                           #print "My route has metric "+str(myMetric)+" but the new route I was sent has metric "+str(newMetric)+", \nso I'll use the new route."
                                           betterRoute = (dest, sender, getOutputPortTo(sender), newMetric)
                                           updateRoute(betterRoute)
                                           #routes.remove(myRoute) #This doesn't work. Is this even the right method call? I dunno, I just guessed.
                                           #routes.append(betterRoute)
				     if metric == 16:
					 print "16 METRIC"
                        if haveRoute == False:
                             # print "I don't have a route to "+dest+" so I'll add this new route:"
                             newRoute = (int(dest), int(sender), int(getOutputPortTo(sender)),int(metric) + int(getMetricTo(sender)))
                             #print newRoute
                             routes.append(newRoute)
            checkNeighbours()
            print "So here's my routing table at the moment:"
            #print routes
            printRoutingTable(routes)
            print "\n"
            if (blockduration < updatePeriod):
               #sleep for the rest of the 10 seconds
                   time.sleep(updatePeriod-blockduration)    

      
