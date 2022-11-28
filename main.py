import Config
import ReadRawPupilData

if __name__ == '__main__':
    threadPupilDataReader = ReadRawPupilData.DataReadThread(setting='-' + Config.LOWLUX + '-' + Config.ONEBACK + '-P09')
    threadPupilDataReader.start()

