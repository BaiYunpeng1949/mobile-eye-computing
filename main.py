import Config
import ReadRawPupilData

if __name__ == '__main__':
    threadPupilDataReader = ReadRawPupilData.DataReadThread(setting='-' + Config.WALK_STAIRPATH + '-' + Config.HARD)
    threadPupilDataReader.start()

