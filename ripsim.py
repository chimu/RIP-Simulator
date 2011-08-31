#!/usr/bin/python

import ConfigParser, sys, socket, time, select

if len(sys.argv) < 2:
      print "ARJHGKLW"
else:
      configfile = sys.argv[1]



      config = ConfigParser.ConfigParser()
      config.read(configfile)

      routerid = config.getint('RIP', 'router-id')
      boganname = config.get('RIP', 'bogan-name')
      
      outputports = []
      inputports = []
      insockets = []
      
      outsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

      for inport in config.get('RIP', 'input-ports').split(','):
            inputports.append(int(inport.strip()))

      for outport in config.get('RIP', 'output-ports').split(','):
            (port, metric) = outport.strip().split('-')
            outputports.append((int(port), metric))

      print "I am", boganname, "and my Id is", routerid
      print "I listen on:", inputports
      print "I connect to:", outputports
	 
      for port in inputports:
	  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	  sock.bind(('127.0.0.1', int(port)))
	  
	  insockets.append(sock)
	  
       
      message = "I am " + boganname
      while True:
	   for (port, metric) in outputports:
	       outsocket.sendto(message, ('127.0.0.1', int(port)))
	   
	   starttime = time.time()
	   readyInputs, [], [] = select.select(insockets, [], [], 10)
	   blockduration = time.time() - starttime
	   
	   for insock in readyInputs:
	       inmessage = insock.recv(1024)
	       print inmessage
	   
	   if (blockduration < 10):
	       time.sleep(10-blockduration)
	       

       
	 
      