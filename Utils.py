import csv
import datetime
import os

import Config


def collectData(right2D, left2D, right3D, left3D):
    now = datetime.datetime.now()
    dateString = now.strftime("%d-%m-%H-%M")
    folderPath = Config.RAW_DATA_PATH + dateString + '/'

    # Check the existence of the folder. If not, create one.
    if os.path.exists(folderPath) is False:
        os.makedirs(folderPath)

    write2csv(pupilDataList=right2D, filePath=folderPath + 'right2D.csv')
    write2csv(pupilDataList=left2D, filePath=folderPath + 'left2D.csv')
    write2csv(pupilDataList=right3D, filePath=folderPath + 'right3D.csv')
    write2csv(pupilDataList=left3D, filePath=folderPath + 'left3D.csv')


def write2csv(pupilDataList, filePath):
    """
    This function writes 4 kinds of pupil diameter data into a csv file. Then being processed.
    :return:
    """

    # open the file in the write mode
    with open(filePath, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)

        # write the header
        writer.writerow(Config.RAW_DATA_CSV_HEADER)

        for pupilData in pupilDataList:
            # write the data
            data = [pupilData.timestamp, pupilData.confidence, pupilData.X, pupilData.event]
            writer.writerow(data)