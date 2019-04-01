import os
import sys

import numpy as np
import cv2
import easygui

import imgphon

dir_name = "output_imgs"

try:
    os.mkdir(dir_name)
except:
    pass

m_tp_list = [5.000, 10.110, 15.001, 20.001, 25.010]

unsorted_4_coords_dict = {}  # key: output_image_name => value: [four coords]
output_img_name_list = []  # a list of all output files id, e.g. SUZHOU_18.MOV_2_10.11
temp_4_coords_list = []  # temp list of four coords
# key: output_img_name => value: {key: position => value: x-val/y-val}
final_result_dict = {}


def paint_dot(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        # param's are passed in by 3rd arg of setMouseCallback, param[0] is the image/canvas curr_frame
        cv2.circle(param[0], (x, y), 3, (60, 20, 220), -1)
        # param[1] is the timepoint value tp, param[2] is the file_name
        temp_4_coords_list.append((x, y))


def interface(windowName, canvas, tp, frame_index, file_name):
    global temp_4_coords_list
    global output_img_name_list
    global unsorted_4_coords_dict
    reloadTrigger = False
    output_img_name = str(file_name) + "_" + str(frame_index) + "_" + str(tp)
    while True:
        cv2.imshow(windowName, canvas)
        key = cv2.waitKey(1) & 0xFF  # ASCII code of pressed key
        if key == 110:  # [N] to next
            if len(temp_4_coords_list) != 4:
                reloadTrigger = True
                temp_4_coords_list = []
                break
            cv2.imwrite(os.path.join(dir_name, output_img_name + ".bmp"), canvas)
            unsorted_4_coords_dict[output_img_name] = temp_4_coords_list
            if not (output_img_name in output_img_name_list): 
                output_img_name_list.append(output_img_name)
            temp_4_coords_list = []
            break
        elif key == 114:  # [R] to reload
            reloadTrigger = True
            temp_4_coords_list = []
            break
        elif key == 113:  # [Q] to quit
            if len(temp_4_coords_list) == 4:
                cv2.imwrite(output_img_name + ".bmp", canvas)
                unsorted_4_coords_dict[output_img_name] = temp_4_coords_list
            temp_4_coords_list = []
            open("checkpoint.txt", "w+").close()
            f = open("checkpoint.txt", "a+")
            f.write(frame_index)
            f.close()
            if not (output_img_name in output_img_name_list): 
                output_img_name_list.append(output_img_name)
            
            cv2.destroyAllWindows()
            sys.exit(0)
    cv2.destroyAllWindows()
    return reloadTrigger

def open_vid_file():
    global final_result_dict
    global unsorted_4_coords_dict
    global output_img_name_list

    all_mode = "Start a new annotation"
    cont_mode = "Resume an unfinished work"
    sg_mode = "Modify a single frame"
    welcome_msg = "Please select an option to proceed. \nNOTICE: You may only select the 2nd or the 3rd option on annotations that you already started or finished."
    choice = easygui.buttonbox(
        msg=welcome_msg, title="LipLabeler", choices=(all_mode, cont_mode, sg_mode))
    vid_path = easygui.fileopenbox(title="Select a video file (*.MOV)...")
    if choice == all_mode:
        loop_timepts(0, m_tp_list, vid_path)
    elif choice == sg_mode:
        final_result_dict = np.load("final_result_dict.npy").item()
        unsorted_4_coords_dict = np.load("unsorted_4_coords_dict.npy").item()
        output_img_name_list = list(np.load("output_img_name_list.npy"))

        frame_index = easygui.integerbox(
            msg="Please enter the frame index you would like to modify", title='Frame Timepoint', lowerbound=1)
        modify_single(frame_index, (final_result_dict,unsorted_4_coords_dict,output_img_name_list), vid_path)
        return
    elif choice == cont_mode:
        final_result_dict = np.load("final_result_dict.npy").item()
        unsorted_4_coords_dict = np.load("unsorted_4_coords_dict.npy").item()
        output_img_name_list = list(np.load("output_img_name_list.npy"))
        f = open("checkpoint.txt","r")
        start_tp = int(f.read()) - 1
        loop_timepts(start_tp,m_tp_list, vid_path)
        return

def modify_single(frame_index, imported_dicts, vid_path):
    
    reloadTrigger = True
    global unsorted_4_coords_dict
    global temp_4_coords_list
    global output_img_name_list

    #unsorted_4_coords_dict = imported_dicts[1]
    #output_img_name_list = imported_dicts[2]
    tp = m_tp_list[frame_index - 1]
    file_name = os.path.basename(vid_path)
    #output_img_name = str(file_name) + "_" + str(frame_index) + "_" + str(tp)
    imgphon.get_video_frame(vid_path, tp)

    while reloadTrigger == True:
        curr_frame = cv2.imread("temp.bmp")
        windowName = str(file_name) + " (Frame " + str(frame_index) + ": " + str(tp) + \
        ") | [R] Reload | [N] Save & Next | [Q] Save & Quit"
        cv2.namedWindow(windowName)
        cv2.moveWindow(windowName, 320, 180)
        cv2.setMouseCallback(windowName, paint_dot, (curr_frame, tp, file_name))

        reloadTrigger = interface(windowName, curr_frame,
                                tp, frame_index, file_name)

        if reloadTrigger == False:
            #unsorted_4_coords_dict[output_img_name] = temp_4_coords_list
            #temp_4_coords_list = []
            break
        else:
            temp_4_coords_list = []

    os.remove("temp.bmp")  # TODO: how to avoid busy


def loop_timepts(start_pt, tp_list, vid_path):
    global temp_4_coords_list
    file_name = str(os.path.basename(vid_path))
    total_frames_count = str(len(tp_list))

    tp_index = start_pt
    while tp_index < len(tp_list):
        tp = tp_list[tp_index]
        imgphon.get_video_frame(vid_path, tp)

        curr_frame = cv2.imread("temp.bmp")
        frame_index = str(tp_index + 1)
        windowName = file_name + " (" + frame_index + "/" + total_frames_count + \
            ") | [R] Reload | [N] Save & Next | [Q] Save & Quit"
        cv2.namedWindow(windowName)
        cv2.moveWindow(windowName, 320, 180)
        cv2.setMouseCallback(windowName, paint_dot,
                             (curr_frame, tp, file_name))

        reloadTrigger = interface(
            windowName, curr_frame, tp, frame_index, file_name)

        if reloadTrigger == False:
            tp_index += 1  # Advance to the next timepoint
        else:
            temp_4_coords_list = []

    os.remove("temp.bmp")  # TODO: how to avoid busy


def take_x(elem):
    return elem[0]


def output_file():
    tmp_dict = {}
    open("result.txt", "w+").close()
    f = open("result.txt", "a+")
    f.write("tp\tleftcx\tleftcy\trightcx\trightcy\tupperx\tuppery\tlowerx\tlowery\n")
    for output_img_name in output_img_name_list:
        f.write(output_img_name + '\t')
        tmp_l = unsorted_4_coords_dict[output_img_name]
        tmp_l.sort(key=take_x)

        tmp_dict["leftx"] = tmp_l[0][0]
        tmp_dict["lefty"] = tmp_l[0][1]
        tmp_dict["rightx"] = tmp_l[3][0]
        tmp_dict["righty"] = tmp_l[3][1]

        f.write(str(tmp_l[0][0]) + '\t' + str(tmp_l[0][1]) +
                '\t' + str(tmp_l[3][0]) + '\t' + str(tmp_l[3][1]) + '\t')
        if tmp_l[1][1] < tmp_l[2][1]:
            tmp_dict["upperx"] = tmp_l[1][0]
            tmp_dict["uppery"] = tmp_l[1][1]
            tmp_dict["lowerx"] = tmp_l[2][0]
            tmp_dict["lowery"] = tmp_l[2][1]
            f.write(str(tmp_l[1][0]) + '\t' + str(tmp_l[1][1]) +
                    '\t' + str(tmp_l[2][0]) + '\t' + str(tmp_l[2][1]))
        else:
            tmp_dict["upperx"] = tmp_l[2][0]
            tmp_dict["uppery"] = tmp_l[2][1]
            tmp_dict["lowerx"] = tmp_l[1][0]
            tmp_dict["lowery"] = tmp_l[1][1]
            f.write(str(tmp_l[2][0]) + '\t' + str(tmp_l[2][1]) +
                    '\t' + str(tmp_l[1][0]) + '\t' + str(tmp_l[1][1]))
        f.write('\n')
        final_result_dict[output_img_name] = tmp_dict
        tmp_dict = {}
    f.close()
    np.save("final_result_dict.npy", final_result_dict)
    np.save("unsorted_4_coords_dict.npy", unsorted_4_coords_dict)
    np.save("output_img_name_list.npy", output_img_name_list)


if __name__ == "__main__":
    open_vid_file()
    output_file()

# interface has problem, (output_img.._dict,), index out of range
