
import _thread as thread
from tf_detector import TfDetector
from tracker import Tracker
from database import ClassMySQL
from setting import *
from datetime import datetime
import func
import time
import cv2
import sys
import os


class WorkCamera:

    def __init__(self, camera_list):
        self.class_model = TfDetector()
        self.class_db = ClassMySQL()

        self.camera_list = camera_list
        self.cap_list = []
        self.frame_list = []
        self.update_frame = []
        self.ret_image = []
        self.detect_rects_list = []
        self.detect_scores_list = []
        self.frame_ind_list = []
        self.tracker_list = []
        self.count_list = []
        self.camera_list = camera_list
        self.camera_enable = []
        self.sql_table = ''
        self.query_list = []
        self.enable_send_query = True

        for i in range(len(camera_list)):
            if camera_list[i] == '' or camera_list[i] is None:
                self.cap_list.append(None)
            else:
                self.cap_list.append(cv2.VideoCapture(camera_list[i]))

            self.tracker_list.append(Tracker())
            self.frame_list.append(None)
            self.update_frame.append(False)
            self.ret_image.append(None)
            self.detect_rects_list.append([])
            self.detect_scores_list.append([])
            self.frame_ind_list.append(0)
            self.count_list.append(0)
            self.camera_enable.append(True)

        # create counting data save folder
        self.cur_path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        self.save_folder = os.path.join(self.cur_path, SAVE_PATH)
        if not os.path.isdir(self.save_folder):
            os.mkdir(self.save_folder)

    def send_query(self):
        while True:
            if self.enable_send_query:
                if len(self.query_list) > 0:
                    query = self.query_list[0]
                    self.class_db.commit(self.sql_table, query[0], query[1], query[2])
                    self.query_list.pop(0)

            time.sleep(0.05)

    def read_frame(self, camera_ind, scale_factor=1.0):
        while True:
            if self.cap_list[camera_ind] is None:
                self.frame_list[camera_ind] = None

            elif self.camera_enable[camera_ind]:
                ret, frame = self.cap_list[camera_ind].read()

                if ret:
                    if scale_factor != 1.0:
                        frame = cv2.resize(frame, None, fx=scale_factor, fy=scale_factor)
                    self.frame_list[camera_ind] = frame
                    self.update_frame[camera_ind] = True
                else:
                    cam_url = self.camera_list[camera_ind]
                    print("Fail to read camera!", cam_url)
                    self.cap_list[camera_ind].release()
                    time.sleep(0.5)
                    self.cap_list[camera_ind] = cv2.VideoCapture(cam_url)

            time.sleep(0.02)

    def check_valid_detection(self, rect_list, score_list, cam_ind):
        check_rect_list = []
        check_score_list = []

        for i in range(len(score_list)):
            if score_list[i] < DETECTION_THRESHOLD:
                continue

            # check ROI
            frame_height, frame_width = self.frame_list[cam_ind].shape[:2]
            roi_x1 = int(CAMERA_ROI[cam_ind][0] * frame_width)
            roi_x2 = int(CAMERA_ROI[cam_ind][2] * frame_width)
            roi_y1 = int(CAMERA_ROI[cam_ind][1] * frame_height)
            roi_y2 = int(CAMERA_ROI[cam_ind][3] * frame_height)
            if rect_list[i][0] < roi_x1 or rect_list[i][2] > roi_x2:
                continue
            elif rect_list[i][1] < roi_y1 or rect_list[i][3] > roi_y2:
                continue

            # check overlap with other rects
            f_overlap = False
            for j in range(len(check_rect_list)):
                if func.check_overlap_rect(check_rect_list[j], rect_list[i]):
                    if check_score_list[j] < score_list[i]:
                        check_score_list[j] = score_list[i]
                        check_rect_list[j] = rect_list[i]
                    f_overlap = True
                    break

            if f_overlap:
                continue

            # check width/height rate
            w = rect_list[i][2] - rect_list[i][0]
            h = rect_list[i][3] - rect_list[i][1]
            if max(w, h) / min(w, h) > 2:
                continue

            # register data
            check_rect_list.append(rect_list[i])
            check_score_list.append(score_list[i])

            # print(class_list[i], rect_list[i])

        return check_rect_list, check_score_list

    def draw_image(self, img, count, rects, scores, cam_ind):
        # draw ROI region
        frame_height, frame_width = self.frame_list[cam_ind].shape[:2]
        roi_x1 = int(CAMERA_ROI[cam_ind][0] * frame_width)
        roi_x2 = int(CAMERA_ROI[cam_ind][2] * frame_width)
        roi_y1 = int(CAMERA_ROI[cam_ind][1] * frame_height)
        roi_y2 = int(CAMERA_ROI[cam_ind][3] * frame_height)
        cv2.rectangle(img, (roi_x1, roi_y1), (roi_x2, roi_y2), (100, 100, 100), 1)

        # draw objects with rectangle
        for i in range(len(rects)):
            rect = rects[i]
            cv2.rectangle(img, (rect[0], rect[1]), (rect[2], rect[3]), (255, 0, 0), 2)
            # cv2.putText(img, str(scores[i]), (rect[0], rect[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            # cv2.putText(img, '{},{}'.format(rect[0], rect[2]), (rect[0], rect[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            #             (255, 0, 0), 2)

        # write counting result
        cv2.rectangle(img, (0, 0), (220, 40), (255, 255, 255), -1)
        cv2.putText(img, "Count: " + str(count), (50 - 10 * len(str(count)), 28), cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 0, 0), 2)

        return img

    def process_frame(self, cam_ind):
        while True:
            if self.update_frame[cam_ind]:
                if self.frame_list[cam_ind] is not None:
                    self.frame_ind_list[cam_ind] += 1

                    img_color = self.frame_list[cam_ind].copy()

                    if DETECT_ENABLE:
                        det_rect_list, det_score_list, det_class_list = self.class_model.detect_from_images(img_color)
                        valid_rects, valid_scores = self.check_valid_detection(det_rect_list, det_score_list, cam_ind)
                    else:
                        valid_rects = []
                        valid_scores = []

                    self.detect_rects_list[cam_ind] = valid_rects
                    self.detect_scores_list[cam_ind] = valid_scores

                    # tracker
                    if self.frame_ind_list[cam_ind] > 2:
                        self.tracker_list[cam_ind].update(self.frame_ind_list[cam_ind], valid_rects)

                        # write to csv file
                        # csv_file = os.path.join(self.save_folder, 'out' + str(cam_ind) + '.csv')
                        if COUNTING_INTEGRATE:
                            count = self.tracker_list[cam_ind].total
                        else:
                            count = len(valid_rects)
                        cur_time = datetime.now()
                        timestamp = cur_time.strftime("%Y-%m-%d %H:%M:%S")

                        # csv_data = '{},{},{}'.format(timestamp, count, count - self.count_list[cam_ind]) + '\n'
                        # func.append_text(csv_file, csv_data)

                        if SEND_SQL and self.count_list[cam_ind] != count:
                            self.query_list.append([cam_ind, count, timestamp])

                        self.count_list[cam_ind] = count

                    if DISPLAY_DETECT_FRAME_ONLY:
                        self.ret_image[cam_ind] = self.draw_image(img_color,
                                                                  count=self.count_list[cam_ind],
                                                                  rects=valid_rects,
                                                                  scores=valid_scores,
                                                                  cam_ind=cam_ind)

                # initialize the variable
                self.update_frame[cam_ind] = False

            time.sleep(0.1)

    def run_thread(self):
        self.class_db.connect(host='78.188.225.187', database='camera', user='root', password='Aa3846sasa*-')
        self.sql_table = 'camera'

        thread.start_new_thread(self.send_query, ())
        for i in range(len(self.cap_list)):
            thread.start_new_thread(self.read_frame, (i, RESIZE_FACTOR))
            thread.start_new_thread(self.process_frame, (i, ))

        while True:
            for i in range(len(self.cap_list)):
                if DISPLAY_DETECT_FRAME_ONLY:
                    if self.ret_image[i] is not None:
                        cv2.imshow('org' + str(i), self.ret_image[i])
                else:
                    if self.frame_list[i] is not None:
                        img_org = self.draw_image(self.frame_list[i].copy(),
                                                  count=self.tracker_list[i].total,
                                                  rects=self.detect_rects_list[i],
                                                  scores=self.detect_scores_list[i],
                                                  cam_ind=i)
                        cv2.imshow('org' + str(i), img_org)

            key = cv2.waitKey(10)
            if key == ord('q'):
                break
            elif key == ord('s'):
                img_gray = cv2.cvtColor(self.frame_list[0], cv2.COLOR_BGR2GRAY)
                img_color = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
                # img_color = img_color[20:-70, 180:-180]
                cv2.imwrite(str(time.time()) + '.jpg', img_color)

    def run(self):
        frame_ind = 0
        while True:
            frame_ind += 1
            ret, frame = self.cap_list[0].read()
            if not ret:
                break

            # resize image
            if RESIZE_FACTOR != 1.0:
                frame = cv2.resize(frame, None, fx=RESIZE_FACTOR, fy=RESIZE_FACTOR)

            # detect
            self.frame_list[0] = frame
            if DETECT_ENABLE:
                det_rect_list, det_score_list, det_class_list = self.class_model.detect_from_images(frame)
                valid_rects, valid_scores = self.check_valid_detection(det_rect_list, det_score_list, 0)
            else:
                valid_rects = []
                valid_scores = []

            self.tracker_list[0].update(frame_ind, valid_rects)

            img_ret = self.draw_image(frame, self.tracker_list[0].total, valid_rects, valid_scores, 0)

            cv2.imshow('ret', img_ret)
            if cv2.waitKey(10) == ord('q'):
                break


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cam_list = [sys.argv[1]]
    else:
        cam_list = CAMERA_URL

    class_work = WorkCamera(cam_list)

    if RUN_MODE_THREAD:
        class_work.run_thread()
    else:
        class_work.run()
