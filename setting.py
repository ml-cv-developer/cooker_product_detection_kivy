# config file
CONFIG_FILE = 'config/ui_config.json'

# camera
# CAMERA_URL = ['rtsp://admin:sys123456@185.123.3.152:554/cam/realmonitor?channel=1&subtype=0']
CAMERA_URL = ['../video/1.mov']
# CAMERA_URL = ['../image/0479.jpg']
# CAMERA_URL = ['../car1.mp4', '../1.mp4']

# roi
CAMERA_ROI = [
    [0.14, 0.07, 0.875, 0.89],
    [0.01, 0.05, 0.96, 0.95],
    [0.01, 0.05, 0.96, 0.95],
    [0.01, 0.05, 0.96, 0.95],
    [0.01, 0.05, 0.96, 0.95],
    [0.01, 0.05, 0.96, 0.95],
    [0.01, 0.05, 0.96, 0.95],
    [0.01, 0.05, 0.96, 0.95],
]

# engine
RUN_MODE_THREAD = False
RESIZE_FACTOR = 1.0
DISPLAY_DETECT_FRAME_ONLY = True
COUNTING_INTEGRATE = True
SEND_SQL = False
SAVE_PATH = 'save'

# detector
DETECT_ENABLE = True
DETECTION_THRESHOLD = 0.1

# tracker
TRACKER_THRESHOLD_DISTANCE = 90  # 90
TRACKER_BUFFER_LENGTH = 100
TRACKER_KEEP_LENGTH = 30

# UI
PIECE_WIDTH = 510
PIECE_HEIGHT = 300
