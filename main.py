import Socket2PupilLabs

if __name__ == '__main__':
    threadPupilDataReader = Socket2PupilLabs.DataReadThread()
    threadPupilDataReader.start()

