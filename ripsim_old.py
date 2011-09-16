#!/usr/bin/python



#THINGS THAT AREN'T YET WORKING/IMPLEMENTED:
#Replacing a route with a shorter one doesn't actually get rid of the old one. This should be easy to fix.
#Route timeouts aren't implemented, so if a router goes offline the routes don't adapt...
#None of the split horizon with route poisoning stuff is in here.
#Probably a lot of other stuff is missing. I dunno.

import ConfigParser, sys, socket, time, select, packets

updatePeriod = 5
timeout = 10

def getMetricTo(dest):
      for myRoute in routes:
            myDest, myFirstRouter1, myInterface, myMetric = myRoute
            if (int(dest) == int(myDest)):
                  return myMetric
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
	print "{}\t| {}\t\t|  {}\t\t|  {}".format(dest, sender, outport, metric)
	
def updateRoute(newRoute):
    for route in routes:
	if route[0] == newRoute[0]:
	    route = newRoute
	  
def updateNeighbour(neighbour):
    timeNow = time.time()
    isNew = True
    for n in neighbours:
	if n[0] == neighbour[0]:
	    neighbours.remove(n)
	    neighbours.append((neighbour[0], timeNow))
	    print "Neighbour " + n[0] + " updated" 
	    isNew = False
    if isNew:
	neighbours.append((neighbour[0], timeNow))
	
    print "I HAVE {} NEIGHBOURS".format(len(neighbours))
    
def checkNeighbours():
    timeNow = time.time()
    print "Time is {}".format(timeNow)
    for n in neighbours:
	if n[1]+timeout < timeNow:
	    print "DEAD NEIGHBOUR: " + n[0] + " WITH TIME {}".format(n[1])
	    #routes.remove(n[0])
	    neighbours.remove(n)
	    

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
      
      outsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

      for inport in config.get('RIP', 'input-ports').split(','):
            inputports.append(int(inport.strip()))

      for outport in config.get('RIP', 'output-ports').split(','):
            (port, routerId, metric) = outport.strip().split('-')
            outputports.append((int(port), int(routerId), metric))
            routes.append((int(routerId), int(myId), int(port), int(metric)))
            
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
            routeString = ""
            for route in routes:
                  dest, firstRouter, interface, metric = route
                  routeString = routeString + str(dest) + '-' + str(myId) + '-' + str(metric) + '/'
            routeString = routeString.rstrip('/')
            updatePacket = packets.UpdatePacket(myId, routes)
            print "RIP Packet has length: " + str(len(str(updatePacket)))
            for (port, routerId, metric) in outputports:
                  message = routeString
                  outsocket.sendto(message, ('127.0.0.1', int(port)))
                  #print "sending " + routeString

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
                   #print inmessage
                   #get routes from received data
                  for route in inmessage.split('/'):
                        (dest, sender, metric) = route.strip().split('-')
                        if (int(metric) == 0):
			    print "NEIGHBOUR " + dest
			    updateNeighbour((dest, sender, getOutputPortTo(sender), int(metric)))
                        #print "Router "+sender+" can get to "+dest+" with metric "+metric
                        #check if this is should be the new route
                        haveRoute = False
                        for myRoute in routes:
                              myDest, myFirstRouter, myInterface, myMetric = myRoute
                              if (int(dest) == myDest): #if i have a route with this dest
                                     haveRoute = True
                                     #print "I also have a route to "+dest
                                     #metric = metric + distance from me to the sender of this update (firstRouter)
                                     newMetric = int(metric) + int(getMetricTo(sender)) #figure out the metric of the new route
                                     #print "If I use the new route it would have a metric of "+str(newMetric)
                                     if ((int(newMetric) < int(myMetric)) or (sender == myFirstRouter)):
                                           #print "My route has metric "+str(myMetric)+" but the new route I was sent has metric "+str(newMetric)+", \nso I'll use the new route."
                                           betterRoute = (dest, sender, getOutputPortTo(sender), newMetric)
                                           updateRoute(betterRoute)
                                           #routes.remove(myRoute) #This doesn't work. Is this even the right method call? I dunno, I just guessed.
                                           #routes.append(betterRoute)
                        if haveRoute == False:
                             # print "I don't have a route to "+dest+" so I'll add this new route:"
                              newRoute = (int(dest), int(sender), int(getOutputPortTo(sender)),int(metric) + int(getMetricTo(sender)))
                              #print newRoute
                              routes.append(newRoute)
            checkNeighbours()
            #print "\nSo here's my routing table at the moment:"
            #print routes
            printRoutingTable(routes)
            print "\n"
            if (blockduration < updatePeriod):
               #sleep for the rest of the 10 seconds
                   time.sleep(updatePeriod-blockduration)    

      
