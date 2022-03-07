# load the packages
import cv2
import datetime
import time
import imutils
from matplotlib import image
import yolov5model
import numpy as np
from centroidtracker import CentroidTracker
import pandas as pd


# load the model (weights)
detector = yolov5model.YOLOv5Model('Weights/best_yolov5s.pt')

# http://www.cbsr.ia.ac.cn/users/sfzhang/WiderPerson/

# load the tracker from CentroidTracker
# maxDisappeared - is number of frame that tracker will wait for object
# maxDistance - is distance between center and box
tracker = CentroidTracker(maxDisappeared = 0, maxDistance = 50)


def main():
    # read the video file
    # cap = cv2.VideoCapture('Videos/Video9.mp4')
    cap = cv2.VideoCapture(0)
    
    # FPS values
    fps_start_time = datetime.datetime.now()
    fps = 0
    total_frames = 0
    
    # Values for counting LPC - live person counter, OPC - overall person counter
    lpc_count = 0
    opc_count = 0
    object_id_list = []
    
    # CURRENT TIME
    current_time = datetime.datetime.now()
    
    # DATA to store the : [date, time, number of person]
    main.data = []
        
    while True:
        # get the image from video
        ret, image = cap.read()
        image = imutils.resize(image, width = 640, height = 640)
        
        # apply .detect() function from yolov5model.py and get results
        modelOutput = detector.detect(image)
        
        # empty list of coordinates
        lst = []
        
        # start X,Y -> center X,Y    |    end X,Y -> width, height
        coordinates = detector.getBoxData(modelOutput, image)
        for i in coordinates:
            startX = i[0]
            startY = i[1]
            endX = i[2]
            endY = i[3]
            label = detector.classToString(i[4])
            
            # coordinate of list
            coor_list = [startX, startY, endX, endY]
            
            # append list coordinates to list
            lst.append(coor_list)
                       
        # update all coordinates to tracker           
        # the object value contain a tuple of two values (objectId, coordinates of box (or just boundingbox))
        # ⭕⭕⭕⭕⭕⭕⭕machine⭕⭕⭕⭕⭕⭕⭕ OBJECTS ARE HERE ⭕⭕⭕⭕⭕⭕⭕⭕⭕⭕⭕⭕⭕⭕
        objects = tracker.update(lst)
        for (objectId, bbox) in objects.items():
            x1, y1, x2, y2 = bbox
            x1 = int(x1)
            y1 = int(y1)
            x2 = int(x2)
            y2 = int(y2)
            
            # draw the rectangle
            cv2.rectangle(image, (x1, y1), (x2, y2), (0,255,0), 2)
            
            # show the text i.e., ID of object
            text = "ID: {}".format(objectId)
            cv2.putText(image, text, (x1, y1 - 5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1 , (0, 0, 255), 1)
            
            # ❌❌❌❌❌❌❌❌❌❌❌❌ list of objectId ❌❌❌❌❌❌❌❌❌❌❌❌
            if objectId not in object_id_list:
                object_id_list.append(objectId)
        
        # count the LPC and OPC
        lpc_count = len(objects)
        opc_count = len(object_id_list)
        
        # show the LPC and OPC
        lpc_txt = "LPC: {}".format(lpc_count)
        opc_txt = "OPC: {}".format(opc_count)

        cv2.putText(image, lpc_txt, (5,60), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)
        cv2.putText(image, opc_txt, (5,90), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)
        
        # FPS counter
        total_frames = total_frames + 1
        fps_end_time = datetime.datetime.now()
        time_diff = fps_end_time - fps_start_time
        if time_diff.seconds == 0:
            fps = 0.0
        else:
            fps = (total_frames/time_diff.seconds)  
        
        # showing the FPS on video
        fps_text = "FPS: {:.2f}".format(fps)
        cv2.putText(image, fps_text, (5,30), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)
        
        # the time that goes by
        now = datetime.datetime.now()
        
        # collect the data into list
        if current_time.hour < now.hour:
            timedata = current_time.time().replace(second=0, microsecond=0, minute=0, hour=current_time.hour) # WAS CHANGED
            main.data.append([current_time.date().strftime('%d/%m/%Y'), timedata.strftime('%H:%M:%S') , opc_count])
            current_time = now
        
        # show the time on image/video    
        show_time = fps_end_time.strftime("%H:%M:%S")
        cv2.putText(image, show_time, (5,120), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)
            
        # show the video with results 
        cv2.imshow('Application', image)        
        
        key = cv2.waitKey(1)
        if key == ord('q'):
        	break  
    
cv2.destroyAllWindows()
main()

# Some manipulation with DataFrame
df = pd.DataFrame()
date_lst = []
time_lst = []
human_lst = []
for i in main.data:
    date_lst.append(i[0])
    time_lst.append(i[1])
    human_lst.append(i[2])
df['Date'] = date_lst
df['At the time'] = time_lst
df['Cumulative'] = human_lst
df["Difference"] = [np.nan] + df.iloc[:-1]["Cumulative"].tolist()
df["There was // person"] = df['Cumulative'] - df["Difference"] 
df["There was // person"][0] = df["Cumulative"][0]
del df['Cumulative']
del df['Difference']

# Save the Dataframe
df.to_excel('Results for ' + datetime.datetime.now().date().strftime('%d.%m.%Y') + '.xlsx')