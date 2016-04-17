#!/usr/bin/env python
"""
Usage:
    cameraControler.py [options]
    cameraControler.py --version
    cameraControler.py (--help | -h)
Options:
    --init-camera   first camera
    --port=<port>   change default port [default: 9003]
    --device=<devive>     device id [default: 0]
    --host=<host>   change default default multicast address [default: 244.1.1.1]
    -h --help       shows this help message and exits
    --version       shows the version number
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
import smtplib
from email.mime.text import MIMEText

__version__ = "Beta 1"

def get_ip_address():
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

class Multicast:
    def __init__(self, host, port, init_camera, addressList):
        print("initilizing multicast")
        self._host = host
        self._port = port
        self._bufferSize = 1024
        self._addressList = addressList;
        if not init_camera:
            self.joinMultiCastGroup()
        t = threading.Thread(target=self.ReadMultiCastGroupRequest)
        t.daemon = True
        t.start()

    def joinMultiCastGroup(self):
        cs = socket(AF_INET, SOCK_DGRAM)
        cs.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        cs.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        cs.sendto('JOIN:' + get_ip_address(), ('255.255.255.255', self._port))

    def ReadMultiCastGroupRequest(self):
        cs = socket(AF_INET, SOCK_DGRAM)
        cs.bind(('255.255.255.255', self._port))
        cs.setblocking(0)
        while True:
            result = select.select([cs],[],[])
            msg = result[0][0].recv(self._bufferSize)
            elem = msg.split(":")
            if elem[0] == "JOIN":
                print(elem[1] + " joined!")
                client = xmlrpclib.ServerProxy('http://' + str(elem[1]) +  ":12374",allow_none=True)
                client.appendToAddressList(get_ip_address())
                newAddress = {'address': client, 'heartbeat':0, 'recording':False, 'ip': str(elem[1])}
                self._addressList.append(newAddress)
                print("After cliect rpc call")

class Camera:
    def  __init__(self, host, port, device, init_camera):
        self.addressList = []
        self.recording = False
        self.motion = False
        self._host = host
        self._port = port
        self._device = device
        self._myIPaddress = get_ip_address();
        self.server = SimpleXMLRPCServer(("", 12374),allow_none=True)
        self.server.register_introspection_functions()
        self.server.register_function(self.appendToAddressList)
        self.server.register_function(self.heartBeatReturn)
        self.server.register_function(self.StartRecording)
        self.server.register_function(self.StopRecording)
        t = threading.Thread(target=self.server.serve_forever)
        t.daemon = True
        t.start()
        t = threading.Thread(target=self.networkChecker)
        t.daemon = True
        t.start()
        Multicast(host, port, init_camera, self.addressList)
        self.CameraDetection()

    def __exit__(self):
        camera.release()
        cv2.destroyAllWindows()
        self.server.quit = 1

    def networkChecker(self):
        while True:
            time.sleep(30)
            for item in self.addressList:
                try:
                    if item['address'].heartBeatReturn():
                        item['heartbeat'] = 0
                        print 'heartbeat =)'
                except EnvironmentError:
                    item['heartbeat'] =+ 1;
                    if item['heartbeat'] > 2:
                        addressList.remove(item)


    def appendToAddressList(self, address):
        client = xmlrpclib.ServerProxy('http://' + str(address) + ":12374", allow_none=True)
        newAddress = {'address':client, 'heartbeat':0, 'recording':False, 'ip':str(address)}
        self.addressList.append(newAddress)

    def heartBeatReturn(self):
        print 'recived heartbeat'
        return True;

    #we need to change this to a int latter in the future
    def StartRecording(self, address):
        #cv2.putText(frame, "Starting",
        #   (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        precount = 0
        print("Start Recording")
        for item in self.addressList:
            if item['recording'] == True:
                precount += 1
            if item['ip'] == address:
                item['recording'] = True

        count = 0
        for item in self.addressList:
            if item['recording'] == True:
                count += 1
        if count == 1 and precount == 0:
            msg = MIMEText("Alert! motion detected")
            msg['Subject'] = 'Alert!'
            msg['From'] = 'alert@security.com'
            msg['To'] = 'younes.nej2008@gmail.com'
            s = smtplib.SMTP('smtp.gmail.com:587')
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login("testdummyemailforproject@gmail.com", "test123!@#")
            s.sendmail('alert@security.com', ['younes.nej2008@gmail.com'], msg.as_string())
            s.quit()


    def StopRecording(self, address):
        #cv2.putText(frame, "Stopping",
        #    (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
        print("Stop Recording")
        for item in self.addressList:
            if item['ip'] == address:
                item['recording'] = False


    def CameraDetection(self):
        camera = cv2.VideoCapture(self._device)
        time.sleep(0.25)
        firstFrame = None
        counter = 0
        freezeFrame = 20
        frameList = {}
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
            frame = imutils.resize(frame, width=1000)
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
                    try:
                        print('Trying to send startRecording')
                        item['address'].StartRecording(self._myIPaddress)
                        print('After Trying to send startRecording')
                    except EnvironmentError:
                        print 'Couldnt send startRecording signal'
            elif ((len(cnts) == 0) & self.motion):
                self.motion = False
                text = "Unoccupied"
                for item in self.addressList:
                    try:
                        print('Trying to send stopRecording')
                        item['address'].StopRecording(self._myIPaddress)
                        print('Aster Trying to send stopRecording')
                    except EnvironmentError:
                        print 'Couldnt send stopRecording signal'

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
            # print counter % freezeFrame
            if counter >= freezeFrame:
                #print "in"
                firstFrame = frameList[counter % freezeFrame]

            frameList[counter % freezeFrame] = gray
            counter += 1

def main():
    arguments = docopt(__doc__, version=__version__)
    camera = Camera(arguments['--host'], int(arguments['--port']), int(arguments['--device']), arguments['--init-camera'])

if __name__ == '__main__':
    main()
