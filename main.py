import Config
import ReadRawPupilData

if __name__ == '__main__':
    threadPupilDataReader = ReadRawPupilData.DataReadThread(setting='-' + Config.STAND + '-' + Config.NOREAD)
    threadPupilDataReader.start()

