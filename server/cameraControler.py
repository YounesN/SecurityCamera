#!/usr/bin/env python
"""
Usage:
	cameraControler.py [options]
	cameraControler.py --version
	cameraControler.py (--help | -h)
Options:
	--init-camera	first camera
	--port=<port>	change default port [default: 9003]
	--host=<host>	change default default multicast address [default: 244.1.1.1]
	-h --help       shows this help message and exits
	--version    	shows the version number
	-a --min-area   minimum area size
"""

import sys
import threading
from socket import *
import cv2
import imutils
import select
import datetime
import time
import fcntl
import struct
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import xmlrpclib
from docopt import docopt #for arguments

def get_ip_address(ifname):
    s = socket(AF_INET, SOCK_DGRAM)
    return inet_ntoa(fcntl.ioctl(s.fileno(),0x8915, struct.pack('256s', ifname[:15]))[20:24])

class Multicast:
    def __init__(self, host, port, init_camera):
        self._host = host
        self._port = port
        self._bufferSize = 1024
        if not init_camera:
            self.joinMultiCastGroup()
        t = threading.Thread(target=self.ReadMultiCastGroupRequest)
        t.daemon = True
        t.start()

    def joinMultiCastGroup(self):
        cs = socket(AF_INET, SOCK_DGRAM)
        cs.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        cs.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        cs.sendto('JOIN:' + get_ip_address('eth0'), ('255.255.255.255', self._port))

    def ReadMultiCastGroupRequest(self):
        cs = socket(AF_INET, SOCK_DGRAM)
        cs.bind(('255.255.255.255', self._port))
        cs.setblocking(0)
        while True:
            result = select.select([cs],[],[])
            msg = result[0][0].recv(self._bufferSize)
            elem = msg.split(":")
            print("received broadcast")
            if elem[0] == "JOIN":
                print(elem[1] + " joined!")
                client = xmlrpclib.ServerProxy('http://' + str(elem[1]) + ":8000")
                client.appendToAddressList(get_ip_address('eth0'))

class Camera:
    addressList = []
    recording = False
    motion = False

    def  __init__(self, host, port):
        self._host = host
        self._port = port
        server = SimpleXMLRPCServer(("localhost", 8000))
        server.register_function(self.appendToAddressList)
        server.register_function(self.heartBeatReturn)
        server.register_function(self.StartRecording)
        server.register_function(self.StopRecording)
        t = threading.Thread(target=server.serve_forever)
        t.daemon = True
        t.start()
        self.CameraDetection()

    def appendToAddressList(self, address):
        print(address)
        client = xmlrpclib.ServerProxy('http://' + str(address) + ":8000")
        newAddress = {'address':client, 'heartbeat':0}
        self.addressList.appand(newAddress)

    def heartBeatReturn():
        return True;

    #we need to change this to a int latter in the future
    def StartRecording(self):
        cv2.putText(frame, "Starting",
           (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        print("Start Recording")
        self._recording = True

    def StopRecording(self):
        cv2.putText(frame, "Stopping",
            (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        print("Stop Recording")
        self._recording = False

    def CameraDetection(self):
        camera = cv2.VideoCapture(0)
        time.sleep(0.25)
        firstFrame = None

        text = "Unoccupied"

        # loop over the frames of the video
        while True:
            # grab the current frame and initialize the occupied/unoccupied
            # text
            (grabbed, frame) = camera.read()

            # if the frame could not be grabbed, then we have reached the end
            # of the video
            if not grabbed:
                break

            # resize the frame, convert it to grayscale, and blur it
            frame = imutils.resize(frame, width=500)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            # if the first frame is None, initialize it
            if firstFrame is None:
                firstFrame = gray
                continue

            # compute the absolute difference between the current frame and
            # first frame
            frameDelta = cv2.absdiff(firstFrame, gray)
            thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

            # dilate the thresholded image to fill in holes, then find contours
            # on thresholded image
            thresh = cv2.dilate(thresh, None, iterations=2)
            (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)

            # loop over the contours
            for c in cnts:
                # compute the bounding box for the contour, draw it on the frame,
                # and update the text
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            if ((len(cnts) != 0) & (not self.motion)):
                self.motion = True
                text = "Occupied"
                for item in self.addressList:
                    item.address.StartRecording()
            elif ((len(cnts) == 0) & self.motion):
                self.motion = False
                text = "Unoccupied"
                for item in self.addressList:
                    item.address.StopRecording()

            # draw the text and timestamp on the frame
            cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            #cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"),
            #    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

            # show the frame and record if the user presses a key
            cv2.imshow("Security Feed", frame)
            #cv2.imshow("Thresh", thresh)
            #cv2.imshow("Frame Delta", frameDelta)
            key = cv2.waitKey(1) & 0xFF

            # if the `q` key is pressed, break from the lop
            if key == ord("q"):
                break

            firstFrame = gray

        camera.release()
        cv2.destroyAllWindows()

def main():
    arguments = docopt(__doc__, version="Alpha 1")
    if arguments['--host'] == None:
        arguments['--host'] = '244.1.1.1'
    if arguments['--port'] == None:
        arguments['--port'] = 9003
    multi = Multicast(arguments['--host'], arguments['--port'], arguments['--init-camera'])
    camera = Camera(arguments['--host'], arguments['--port'])

if __name__ == '__main__':
    main()
