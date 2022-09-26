import Config
import ReadRawPupilData

if __name__ == '__main__':
    threadPupilDataReader = ReadRawPupilData.DataReadThread(setting='-' + Config.HIGHLUX + '-' + Config.ONEBACK)
    threadPupilDataReader.start()

