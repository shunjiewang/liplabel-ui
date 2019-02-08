import numpy as np
import cv2
import easygui
import imgphon
import os

def paint_dot(event,x,y,flags,param):
	if event == cv2.EVENT_LBUTTONDOWN:
		cv2.circle(param[0],(x,y),3,(60,20,220),-1)
		f = open(str(param[2]) + "_" + str(param[1]) + ".txt", "a+")
		#f = open(str(param[1]) + ".txt", "a+")
		f.write(str((x,y))+'\n')
		f.close()

def interface(windowName, frame):
	while (1):
		cv2.imshow(windowName, frame)
		key = cv2.waitKey(20) & 0xFF
		if key == 32 or key == 110: #Space,n
			#reply = easygui.ynbox(msg="Is the annotation satisfying?", choices=["Yes","No"])
			#if reply == False:
			#	continue
			#else:
			break
			cv2.destroyWindow(windowName)

	cv2.destroyAllWindows()

m_tp_list = [5.000,10.111]

def open_vid_file():
	vid_path = easygui.fileopenbox(title="Select a video file (*.MOV)...")
	return vid_path

def paint_tp_list(tp_list):

	## easygui.msgbox(msg="Please select a video file (*.MOV) to start...", title = "LipLabeler")
	# This thing is causing error
	
	vid_path = open_vid_file()
	##vid_path = "../Videos/SUZHOU_18.MOV"
	file_name = os.path.basename(vid_path)

	for tp in tp_list:
		imgphon.get_video_frame(vid_path, tp)
		
		curr_frame = cv2.imread("temp.bmp")
		cv2.namedWindow('LipLabeler')
		cv2.setMouseCallback('LipLabeler',paint_dot,(curr_frame,tp,file_name)) #3rd param: file_name

		interface('LipLabeler', curr_frame)

	#easygui.msgbox('You have finished labeling all frames.','Good Job!')

paint_tp_list(m_tp_list)
