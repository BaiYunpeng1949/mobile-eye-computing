import Config
import ReadRawPupilData

if __name__ == '__main__':
    threadPupilDataReader = ReadRawPupilData.DataReadThread(setting='-' + Config.LOWLUX + '-' + Config.ONEBACK + '-09')
    threadPupilDataReader.start()

