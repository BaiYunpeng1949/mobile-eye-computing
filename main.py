import Config
import ReadRawPupilData

if __name__ == '__main__':
    threadPupilDataReader = ReadRawPupilData.DataReadThread(setting='-' + Config.HIGHLUX + '-' + Config.THREEBACK + '-11')
    threadPupilDataReader.start()

