import os
import sys
import re
import contextlib

import numpy as np
import cv2
import easygui

import imgphon

m_tp_list = [5.000, 10.110, 15.001, 20.001, 25.010]

result_dict = {}
clicks_list = []
working_directory = ""


def paint_dot(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        cv2.circle(param, (x, y), 3, (60, 20, 220), -1)
        clicks_list.append((x, y))


def interface(windowName, canvas, tp, frame_index, file_name):
    dir_name = "output_imgs"

    with contextlib.suppress(FileExistsError):
        os.mkdir(os.path.join(working_directory, dir_name))

    global clicks_list
    global result_dict
    shouldReload = False
    output_img_name = str(file_name) + "-" + str(frame_index) + "-" + str(tp)
    while True:
        cv2.imshow(windowName, canvas)
        key = cv2.waitKey(1) & 0xFF  # ASCII code of pressed key
        if key == 110:  # [N] to next
            if len(clicks_list) != 4:
                shouldReload = True
                clicks_list = []
                break
            cv2.imwrite(os.path.join(working_directory, dir_name,
                                     output_img_name + ".bmp"), canvas)
            result_dict[tp] = sort_coords(clicks_list)
            clicks_list = []
            break
        elif key == 114:  # [R] to reload
            shouldReload = True
            clicks_list = []
            break
        elif key == 113:  # [Q] to quit
            if len(clicks_list) == 4:
                cv2.imwrite(os.path.join(working_directory,
                                         dir_name, output_img_name + ".bmp"), canvas)
                result_dict[tp] = sort_coords(clicks_list)
            clicks_list = []
            cv2.destroyAllWindows()
            np.save(os.path.join(working_directory,
                                 "result_dict.npy"), result_dict)
            sys.exit(0)
    cv2.destroyAllWindows()
    return shouldReload


def open_vid_file():
    global result_dict
    global working_directory

    all_mode = "Start a new annotation"
    cont_mode = "Resume an unfinished work"
    sg_mode = "Modify a single frame"
    welcome_msg = """Please select an option to proceed. \n
                     NOTICE: You may only select the 2nd or the 3rd option on annotations 
                     that you already started or finished."""
    choice = easygui.buttonbox(
        msg=welcome_msg, title="LipLabeler", choices=(all_mode, cont_mode, sg_mode))
    if choice == None:
        sys.exit(0)
    vid_path = easygui.fileopenbox(title="Select a video file (*.MOV)...")
    if vid_path == None:
        sys.exit(0)
    working_directory = re.sub(r'\..*', '', vid_path)
    with contextlib.suppress(FileExistsError):
        os.mkdir(working_directory)

    if choice == all_mode:
        label_mutiple(0, m_tp_list, vid_path)
    elif choice == sg_mode:
        try:
            with open(os.path.join(working_directory, "result.txt")):
                result_dict = np.load(os.path.join(
                    working_directory, "result_dict.npy")).item()
        except FileNotFoundError:
            if easygui.msgbox(msg="""single mode is only for modifying existing project. 
                                     You need to start one first""") == "OK":
                sys.exit(0)
        frame_index = easygui.integerbox(
            msg="Please enter the frame index you would like to modify", title='Frame Timepoint', 
            lowerbound=1, upperbound=(len(m_tp_list)))
        if frame_index == None:
            sys.exit(0)
        label_single(frame_index, vid_path)
        return
    elif choice == cont_mode:
        with contextlib.suppress(FileNotFoundError):
            result_dict = np.load(os.path.join(
                working_directory, "result_dict.npy")).item()
        start_tp = 0
        tp_index = 0
        while tp_index < len(m_tp_list):
            tp = m_tp_list[tp_index]
            if not tp in result_dict:
                start_tp = tp_index
                break
            tp_index += 1

        label_mutiple(start_tp, m_tp_list, vid_path)
        return


def label_single(frame_index, vid_path):
    shouldReload = True
    tp = m_tp_list[frame_index - 1]
    file_name = os.path.basename(vid_path)
    imgphon.get_video_frame(vid_path, tp)

    while shouldReload:
        curr_frame = cv2.imread("temp.bmp")
        windowName = str(file_name) + " (Frame " + str(frame_index) + ": " + str(tp) + \
            ") | [R] Reload | [N] Save & Next | [Q] Save & Quit"
        cv2.namedWindow(windowName)
        cv2.moveWindow(windowName, 320, 180)
        cv2.setMouseCallback(windowName, paint_dot, curr_frame)

        shouldReload = interface(windowName, curr_frame,
                                 tp, frame_index, file_name)

    os.remove("temp.bmp")


def label_mutiple(start_pt, tp_list, vid_path):
    file_name = str(os.path.basename(vid_path))
    total_frames_count = str(len(tp_list))
    tp_index = start_pt
    while tp_index < len(tp_list):
        shouldReload = True
        tp = tp_list[tp_index]
        imgphon.get_video_frame(vid_path, tp)

        while shouldReload:
            curr_frame = cv2.imread("temp.bmp")
            frame_index = str(tp_index + 1)
            windowName = file_name + " (" + frame_index + "/" + total_frames_count + \
                ") | [R] Reload | [N] Save & Next | [Q] Save & Quit"
            cv2.namedWindow(windowName)
            cv2.moveWindow(windowName, 320, 180)
            cv2.setMouseCallback(windowName, paint_dot,
                                 curr_frame)

            shouldReload = interface(
                windowName, curr_frame, tp, frame_index, file_name)

            if not shouldReload:
                tp_index += 1

    os.remove("temp.bmp")


def sort_coords(tmp_l):
    tmp_dict = {}

    def take_x(elem):
        return elem[0]
    tmp_l.sort(key=take_x)

    tmp_dict["leftx"] = tmp_l[0][0]
    tmp_dict["lefty"] = tmp_l[0][1]
    tmp_dict["rightx"] = tmp_l[3][0]
    tmp_dict["righty"] = tmp_l[3][1]

    if tmp_l[1][1] < tmp_l[2][1]:
        tmp_dict["upperx"] = tmp_l[1][0]
        tmp_dict["uppery"] = tmp_l[1][1]
        tmp_dict["lowerx"] = tmp_l[2][0]
        tmp_dict["lowery"] = tmp_l[2][1]
    else:
        tmp_dict["upperx"] = tmp_l[2][0]
        tmp_dict["uppery"] = tmp_l[2][1]
        tmp_dict["lowerx"] = tmp_l[1][0]
        tmp_dict["lowery"] = tmp_l[1][1]
    return tmp_dict


def output_file():
    open(os.path.join(working_directory, "result.txt"), "w+").close()
    f = open(os.path.join(working_directory, "result.txt"), "a+")
    f.write("index\ttimestamp\tleftcx\tleftcy\trightcx\trightcy\tupperx\tuppery\tlowerx\tlowery\n")
    tp_index = 0
    while tp_index < len(m_tp_list):
        tp = m_tp_list[tp_index]
        f.write(str(tp_index + 1) + "\t")
        f.write(str(tp))
        for keys in result_dict[tp]:
            f.write("\t")
            f.write(str(result_dict[tp][keys]))
        f.write("\n")
        tp_index += 1
    f.close()


if __name__ == "__main__":
    open_vid_file()
    output_file()
    np.save(os.path.join(working_directory,
                         "result_dict.npy"), result_dict)
