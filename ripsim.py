#!/usr/bin/python

import ConfigParser, sys

if len(sys.argv) < 2:
      print "ARJHGKLW"
else:
      configfile = sys.argv[1]



      config = ConfigParser.ConfigParser()
      config.read(configfile)

      routerid = config.getint('RIP', 'router-id')
      outputports = []
      inputports = []

      for inport in config.get('RIP', 'input-ports').split(','):
            inputports.append(int(inport.strip()))

      for outport in config.get('RIP', 'output-ports').split(','):
            (port, metric) = outport.strip().split('-')
            outputports.append((port, metric))

      print "I am", routerid
      print "I listen on:", inputports
      print "I connect to:", outputports
