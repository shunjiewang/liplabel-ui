import numpy as np
import cv2
import easygui
import imgphon
import os

# Questions:
# 1. How are timepoints selected/inputted?
# 2. What to label when the mouth is shut?

m_tp_list = [5.000,10.111]

def paint_dot(event,x,y,flags,param):

	if event == cv2.EVENT_LBUTTONDOWN:
		#Paint a dot
		cv2.circle(param[0],(x,y),3,(60,20,220),-1)
		#Write the coordinate to f
		f = open(str(param[2]) + "_" + str(param[1]) + ".txt", "a+")
		f.write(str((x,y))+'\n')
		f.close()

def interface(windowName, canvas):	
	redo = False

	while True:
		cv2.imshow(windowName, canvas)
		key = cv2.waitKey(1) & 0xFF
		if key == 32 or key == 110: #Space,n
			break
		elif key == 114:
			redo = True
			break

	cv2.destroyAllWindows()
	return redo

def open_vid_file():
	vid_path = easygui.fileopenbox(title="Select a video file (*.MOV)...")
	return vid_path

def paint_tp_list(tp_list):
	easygui.msgbox(msg="Please select a video file (*.MOV) to start...", title = "LipLabeler GUI")
	
	vid_path = open_vid_file()
	file_name = os.path.basename(vid_path)

	m_index = 0

	while m_index < len(tp_list):
		tp = tp_list[m_index]
		imgphon.get_video_frame(vid_path, tp)
		
		curr_frame = cv2.imread("temp.bmp")
		cv2.namedWindow('LipLabeler')
		cv2.setMouseCallback('LipLabeler',paint_dot,(curr_frame,tp,file_name))
		
		redo = interface('LipLabeler', curr_frame)

		if redo == False:
			m_index += 1 #Advance to the next timepoint
		else:
			open(str(file_name) + "_" + str(tp) + ".txt", 'w').close() #Clear recorded coordinates in the txt file

if __name__=="__main__":
	paint_tp_list(m_tp_list)