import math, pywt, numpy as np
import csv
import sys
import os
import xml.etree.ElementTree

from datetime import datetime

import zmq
from msgpack import loads

import time
from threading import Thread
from queue import Queue

import keyboard
import datetime

from socket import *
import json

"""
To use this established data processing file, simply plug the pupil core onto a laptop/PC and run the "pupil capture.exe" on it.
"""


host = '255.255.255.255'
port = 50000    # Randomly choose a portal.

confidenceThreshold = .2
windowLengthSeconds = 60
maxSamplingRate = 60    # Changed to 60Hz due to our hardware limitations.
minSamplesPerWindow = maxSamplingRate * windowLengthSeconds
# wavelet = 'sym8'
wavelet = 'sym16'

MODE_2D = '2d c++'
MODE_3D = 'pye3d 0.3.0 real-time'
INDEX_EYE_0 = 0
INDEX_EYE_1 = 1

global threadRunning, currentI0PupilData, currentI1PupilData


class ProcessingThread(Thread):
    def __init__(self, I0pupilData, I1pupilData, targetSocket):
        Thread.__init__(self)
        self.I0data = I0pupilData
        self.I1data = I1pupilData
        self.targetSocket = targetSocket

    def run(self):
        global threadRunning
        processData(self.I0data, self.I1data, self.targetSocket)
        threadRunning = False


class PupilData(float):
    def __init__(self, dia):
        self.X = dia
        self.timestamp = 0
        self.confidence = 0


def createSendSocket():
    backlog = 5
    size = 1024
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    return sock


def createPupilConnection():
    context = zmq.Context()
    # open a req port to talk to pupil
    addr = '127.0.0.1'  # remote ip or localhost
    req_port = "50020"  # same as in the pupil remote gui
    req = context.socket(zmq.REQ)
    req.connect("tcp://{}:{}".format(addr, req_port))
    # ask for the sub port
    req.send_string('SUB_PORT')
    sub_port = req.recv_string()

    # open a sub port to listen to pupil
    sub = context.socket(zmq.SUB)
    sub.connect("tcp://{}:{}".format(addr, sub_port))

    sub.setsockopt_string(zmq.SUBSCRIBE, 'pupil.')  # See Pupil Lab website, don't need to change here. "Pupil Datum Format": https://docs.pupil-labs.com/developer/core/overview/.

    return sub


def cleanup(old_data):
    stddev = np.std(old_data)
    mean = np.mean(old_data)

    filtered = []
    runner = 0.0

    for i in range(len(old_data)):
        currentData = PupilData(old_data[i].X)
        currentData.timestamp = old_data[i].timestamp
        distanceToMean = abs(currentData.X - mean)

        if distanceToMean < stddev * 2:
            filtered.append(currentData)
            runner += 1

    # print(str(stddev) + " / " + str(mean) + ' / ' + str(len(filtered)))

    return filtered


def cleanBlinks(data):
    blinks = []

    minNumForBlinks = 2
    numSamples = len(data)
    i = 0
    minConfidence = .25

    while i < numSamples:
        if data[i].confidence < minConfidence and i < numSamples - 1:
            runner = 1
            nextData = data[i + runner]
            while nextData.confidence < minConfidence:
                runner = runner + 1

                if i + runner >= numSamples:
                    break

                nextData = data[i + runner]

            if runner >= minNumForBlinks:
                blinks.append((i, runner))

            i = i + runner
        else:
            i = i + 1

    durationsSampleRemoveMS = 200
    numSamplesRemove = int(math.ceil(120 / (1000 / durationsSampleRemoveMS)))

    blinkMarkers = np.ones(numSamples)
    for i in range(len(blinks)):
        blinkIndex = blinks[i][0]
        blinkLength = blinks[i][1]

        for j in range(0, blinkLength):
            blinkMarkers[blinkIndex + j] = 0

        for j in range(0, numSamplesRemove):
            decrementIndex = blinkIndex - j
            incrementIndex = blinkIndex + blinkLength + j

            if decrementIndex >= 0:
                blinkMarkers[decrementIndex] = 0

            if incrementIndex < numSamples:
                blinkMarkers[incrementIndex] = 0

    newSamplesList = []

    for i in range(0, numSamples):
        if blinkMarkers[i] == 1:
            newSamplesList.append(data[i])

    return newSamplesList


def fixTimestamp(data):
    runner = 0.0
    for i in range(len(data)):
        data[i].timestamp = runner / 60.0   # Changed this from 120 to 60
        runner += 1


def processData(data, socket):
    blinkedRemoved = cleanBlinks(data)
    cleanedData = cleanup(blinkedRemoved)
    fixTimestamp(cleanedData)
    currentIPA = None   # TODO: fix this

    valueString = ' ipa ' + str(currentIPA)
    print(str(datetime.datetime.now()) + '  ' + valueString + '; ' + str(len(cleanedData)) + ' / ' + str(len(data)) + ' samples')
    socket.sendto(str.encode(str(round(currentIPA, 3))), (host, port))    # Send to their equipment.


def processData(I0data, I1data, socket):
    blinkedRemovedI0 = cleanBlinks(I0data)
    cleanedI0Data = cleanup(blinkedRemovedI0)
    fixTimestamp(cleanedI0Data)

    blinkedRemovedI1 = cleanBlinks(I1data)
    cleanedI1Data = cleanup(blinkedRemovedI1)
    fixTimestamp(cleanedI1Data)

    print('Eye 0: ' + str(datetime.datetime.now()) + ' ' + str(len(cleanedI0Data)) + ' / ' + str(
        len(I0data)) + ' samples')
    print(str(cleanedI0Data))
    print('Eye 1: ' + str(datetime.datetime.now()) + ' ' + str(len(cleanedI1Data)) + ' / ' + str(
        len(I1data)) + ' samples')
    print(str(cleanedI1Data))
    # socket.sendto(str.encode(str(round(averagedCurrentIPA, 3))), (host, port))    # TODO: resume this part later.


def receivePupilData(udp, pupilSocket):     # The "udp" is for "user datagram protocol".
    while True:
        try:
            topic = pupilSocket.recv_string()
            msg = pupilSocket.recv()
            msg = loads(msg, encoding='utf-8')
            # print("\n{}: {}".format(topic, msg))

            global threadRunning
            method = msg['method']
            idEye = msg['id']

            # if idEye == INDEX_EYE_0:
            #     I0data = PupilData(msg['diameter'])  # Collect the 2-D pixel data.
            #     I0data.timestamp = msg['timestamp']
            #     I0data.confidence = msg['confidence']
            #
            #     currentI0PupilData.append(I0data)
            # elif idEye == INDEX_EYE_1:
            #     I1data = PupilData(msg['diameter'])  # Collect the 2-D pixel data.
            #     I1data.timestamp = msg['timestamp']
            #     I1data.confidence = msg['confidence']
            #
            #     currentI1PupilData.append(I1data)
            #
            if method == MODE_3D and idEye == INDEX_EYE_0:
                I0data = PupilData(msg['diameter_3d'])    # Calculate the 3-D mm model data.  Sometimes lacks this data.
                I0data.timestamp = msg['timestamp']
                I0data.confidence = msg['confidence']

                currentI0PupilData.append(I0data)
            elif method == MODE_3D and idEye == INDEX_EYE_1:
                I1data = PupilData(
                    msg['diameter_3d'])  # Calculate the 3-D mm model data.  Sometimes lacks this data.
                I1data.timestamp = msg['timestamp']
                I1data.confidence = msg['confidence']

                currentI1PupilData.append(I1data)

            # Calculate and send out the ipa data.
            while len(currentI0PupilData) > minSamplesPerWindow:
                currentI0PupilData.pop(0)     # Remove the first element in the list.
            while len(currentI1PupilData) > minSamplesPerWindow:
                currentI1PupilData.pop(0)  # Remove the first element in the list.

            if len(currentI0PupilData) == minSamplesPerWindow and len(currentI1PupilData) == minSamplesPerWindow and threadRunning is False:     # Wait for reaching 1-minute's windows length; enough data points.
                threadRunning = True
                processingThread = ProcessingThread(list(currentI0PupilData), list(currentI1PupilData), udp)    # Iteratively apply and start threads. TODO: make a new thread cope 2 pupils.
                processingThread.start()

        except KeyboardInterrupt:
            break


def runPupilReader():
    global threadRunning, currentI0PupilData, currentI1PupilData
    threadRunning = False
    currentI0PupilData = list()
    currentI1PupilData = list()     # Added to apply 2 pupil analysis.

    print(datetime.datetime.now())
    socket = createSendSocket()
    pupilSocket = createPupilConnection()  # Subscribe pupil data "Pupil Datum Format".

    receivePupilData(socket, pupilSocket)


class DataReadThread(Thread):
    def __int__(self):
        Thread.__init__(self)

    def run(self):
        runPupilReader()
