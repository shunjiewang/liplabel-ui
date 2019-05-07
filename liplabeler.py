import os
import sys
import re
import contextlib

import numpy as np
import cv2
import easygui

import imgphon


def interface(windowName, canvas, tp, frame_index, file_name, result_dict, clicks_list, working_dir, sort_fn, label_num_constr: int, ext):
    output_imgs_dir = "output_imgs"

    with contextlib.suppress(FileExistsError):
        os.mkdir(os.path.join(working_dir, output_imgs_dir))

    shouldReload = False
    output_img_name = str(file_name) + "-" + str(frame_index) + "-" + str(tp)
    while True:
        cv2.imshow(windowName, canvas)
        key = cv2.waitKey(1) & 0xFF  # ASCII code of pressed key
        if key == 110:  # [N] to next
            if label_num_constr and (len(clicks_list) != label_num_constr):
                shouldReload = True
                break
            cv2.imwrite(os.path.join(working_dir, output_imgs_dir,
                                     output_img_name + ext), canvas)
            # When using for other purposes, customize sort_coords()
            result_dict[tp] = sort_fn(clicks_list)
            break
        elif key == 114:  # [R] to reload
            shouldReload = True
            break
        elif key == 113:  # [Q] to quit
            if label_num_constr and (len(clicks_list) == label_num_constr):
                cv2.imwrite(os.path.join(working_dir,
                                         output_imgs_dir, output_img_name + ext), canvas)
                result_dict[tp] = sort_fn(clicks_list)
            cv2.destroyAllWindows()
            np.save(os.path.join(working_dir,
                                 "result_dict.npy"), result_dict, allow_pickle=True)
            os.remove("temp.bmp")
            sys.exit(0)
    cv2.destroyAllWindows()
    return (shouldReload, result_dict)


def paint_dot(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        cv2.circle(param[0], (x, y), 3, (60, 20, 220), -1)
        param[1].append((x, y))


def label_single(frame_index: int, vid_path: str, total_frames_count: int, result_dict: dict, working_dir: str, sort_fn, label_num_constr: int, ext, tp_list):
    shouldReload = True
    tp = tp_list[frame_index - 1]
    file_name = os.path.basename(vid_path)
    imgphon.get_video_frame(vid_path, tp)
    m_clicks_list = []

    while shouldReload:
        curr_frame = cv2.imread("temp.bmp")
        windowName = "(Frame " + str(frame_index) + " of " + str(total_frames_count) + ") " + str(file_name) + " @ " + str(tp) +  \
            " Sec | [R] Reload | [N] Save & Next | [Q] Save & Quit"
        cv2.namedWindow(windowName)
        cv2.moveWindow(windowName, 320, 180)
        cv2.setMouseCallback(windowName, paint_dot,
                             (curr_frame, m_clicks_list))

        interface_return = interface(windowName, curr_frame,
                                     tp, frame_index, file_name, result_dict, m_clicks_list, working_dir, sort_fn, label_num_constr, ext)
        shouldReload = interface_return[0]
        if shouldReload:
            m_clicks_list = []

    os.remove("temp.bmp")
    return interface_return[1]


def label_multiple(start_pt: int, tp_list: list, vid_path: str, result_dict: dict, working_dir: str, sort_fn, label_num_constr: int, ext):
    total_frames_count = str(len(tp_list))
    tp_index = start_pt
    while tp_index < len(tp_list):
        m_tp_index = tp_index + 1
        new_result_dict = label_single(
            m_tp_index, vid_path, total_frames_count, result_dict, working_dir, sort_fn, label_num_constr, ext, tp_list)
        result_dict = new_result_dict
        tp_index += 1


def sort_coords(tmp_l):
    def take_x(elem):
        return elem[0]
    tmp_l.sort(key=take_x)

    left = tmp_l[0]
    right = tmp_l[3]
    if tmp_l[1][1] < tmp_l[2][1]:
        upper = tmp_l[1]
        lower = tmp_l[2]
    else:
        upper = tmp_l[2]
        lower = tmp_l[1]

    tmp_dict = {"leftx": left[0],
                "lefty": left[1],
                "rightx": right[0],
                "righty": right[1],
                "upperx": upper[0],
                "uppery": upper[1],
                "lowerx": lower[0],
                "lowery": lower[1]}

    return tmp_dict


if __name__ == "__main__":

    m_tp_list = [5.000, 10.110]

    result_dict = {}

    all_mode = "Start a new annotation"
    cont_mode = "Resume an unfinished work"
    single_mode = "Modify a single frame"

    welcome_msg = """Please select an option to proceed.\n
    NOTICE: You may only modify a single frame for annotations
    that you already started or finished."""

    choice = easygui.buttonbox(
        msg=welcome_msg, title="LipLabeler", choices=(all_mode, cont_mode, single_mode))
    if choice == None:
        sys.exit(0)

    vid_path = easygui.fileopenbox(title="Select a video file (*.MOV)...")
    if vid_path == None:
        sys.exit(0)

    working_dir = re.sub(r'\..*', '', vid_path)
    with contextlib.suppress(FileExistsError):
        os.mkdir(working_dir)

    def output_quality():
        ext = easygui.choicebox(msg='Select desired output image quality: \n .bmp: large file, high quality \n .png: smaller file, high quality \n .jpg: smallest file, low quality',
                                title="Select Quality", choices=[".bmp", ".png", ".jpg"], preselect=1)
        if ext == None:
            sys.exit(0)
        else:
            return ext

    # ALL MODE
    if choice == all_mode:
        ext = output_quality()
        label_multiple(0, m_tp_list, vid_path, result_dict,
                       working_dir, sort_coords, 4, ext)
    # RESUME MODE
    elif choice == cont_mode:
        with contextlib.suppress(FileNotFoundError):
            result_dict = np.load(os.path.join(
                working_dir, "result_dict.npy"), allow_pickle=True).item()
        start_tp = 0
        tp_index = 0
        while tp_index < len(m_tp_list):
            tp = m_tp_list[tp_index]
            if not tp in result_dict:
                start_tp = tp_index
                break
            tp_index += 1
        ext = output_quality()
        label_multiple(start_tp, m_tp_list, vid_path,
                       result_dict, working_dir, sort_coords, 4, ext)
    # SINGLE MODE
    elif choice == single_mode:
        try:
#           with open(os.path.join(working_dir, "result.txt")):
                result_dict = np.load(os.path.join(
                    working_dir, "result_dict.npy"), allow_pickle=True).item()
        except FileNotFoundError:
            if easygui.msgbox(msg="""Single mode is only for modifying existing project. \
                                     You need to start one first.""") == "OK":
                sys.exit(0)
        frame_index = easygui.integerbox(
            msg="Please enter the frame index you would like to modify", title='Frame Timepoint',
            lowerbound=1, upperbound=(len(m_tp_list)))
        if frame_index == None:
            sys.exit(0)
        ext = output_quality()
        label_single(frame_index, vid_path, 0, result_dict,
                     working_dir, sort_coords, 4, ext, m_tp_list)

    # WRITING TO OUTPUT
    keys = ["leftx", "lefty", "rightx", "righty",
            "upperx", "uppery", "lowerx", "lowery"]
    open(os.path.join(working_dir, "result.txt"), "w+").close()
    with open(os.path.join(working_dir, "result.txt"), "a+") as f:
        f.write("index\ttimestamp\t")
        for key in keys:
            f.write(key + "\t")
        f.write("\n")
        tp_index = 0
        while tp_index < len(m_tp_list):
            tp = m_tp_list[tp_index]
            f.write(str(tp_index + 1) + "\t")
            f.write(str(tp))
            for key in keys:
                f.write("\t")
                f.write(str(result_dict[tp][key]))
            f.write("\n")
            tp_index += 1

    np.save(os.path.join(working_dir,
                         "result_dict.npy"), result_dict, allow_pickle=True)