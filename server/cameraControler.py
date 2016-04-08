#!/usr/bin/env python
"""
Usage:
	cameraControler.py [options]
	cameraControler.py --version
	cameraControler.py (--help | -h)
Options:
	-init-camera	first camera
	--port=<port>	change default port [default: 9000]
	--host=<host>	change default default multicast address [default: 244.1.1.1]
	-h --help       shows this help message and exits
	--version    	shows the version number
	-a --min-area   minimum area size
"""

import sys
import socket
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from docopt import docopt #for arguments


class Multicast:
	def __init__(self, host, port):
		self._host = host
		self._port = port
		joinMultiCastGroup()
		threading.Thread(target=ReadMultiCastGroupRequest(arguments['<host>'], arguments['<port>'],)

	def joinMultiCastGroup():
		sock = socket.socket(socket.AF_INET, socket.SOCJ_DGRAM, socket.IPPROTO_UDP)
		sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL,32)
		sock.sendto('new', (self._host, self._port))

	def ReadMultiCastGroupRequest():
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		try:
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		except AttributeError:
			pass

		sock.bind((self._host, self._port))
		host = socket.gethostbyname(socket.gethostname())
		sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host))
		sock.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP,
				socket.inet_aton(self._host) + socket.inet_aton(host))
		while 1:
			try:
				data, addr = sock.recvfrom(1024)
			except socket.error, e:
				print 'Expection'
			hexdata = binascii.hexlify(data)
			if hexdata == 'new'


class Camera:
	addressList = []
	recording = False

	def  __init__():
		server = simpleXMLRPCServer(("localhost", 8000))
		server.register_function(appendToAddressList)
		server.register_function(heartBeatReturn)
		server.register_function(StartRecordeing)
		server.register_function(StopRecording)
		threading.Thread(target=server.serve_forever())

	def appendToAddressList(self, address):
		newAddress = {'address':address, 'heartbeat':0}
		self.addressList.appand(newAddress)

	def heartBeatReturn():
		return True;

	#we need to change this to a int latter in the future
	def StartRecordeing(self):
		self._recording = True

	def StopRecording(self):
		self._recording = False

def main():
	arguments = docopt(__doc__, __version="Alpha 1")
	if !arguments['-init-camera']:
		Multicast(arguments['<host>'], arguments['<port>'])
	Camera()


if __name__ == '__main__':
	main()
