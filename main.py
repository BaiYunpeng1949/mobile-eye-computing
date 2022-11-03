import Config
import ReadRawPupilData

if __name__ == '__main__':
    threadPupilDataReader = ReadRawPupilData.DataReadThread(setting='-ParticipantName-' + Config.HIGHLUX + '-' + Config.THREEBACK)
    threadPupilDataReader.start()

