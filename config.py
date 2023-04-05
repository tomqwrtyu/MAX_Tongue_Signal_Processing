# [common]
def clear_line(n=1):
    LINE_UP = '\033[1A'
    LINE_CLEAR = '\x1b[2K'
    for _ in range(n):
        print(LINE_UP, end=LINE_CLEAR)

NUM_IMF = 3
CHANNEL_NUMBER = 3
WINDOW_SIZE = 200
SAMPLE_RATE = 500 #Hz
KEY_CLASS = {0:'undefined action', 1:'up', 2:'down', 3:'left', 4:'right', 5:'quick touch'}
SERVER_URL = 'http://maxtongue.ddns.net:3000'

# [inference]
REQ_RECEIVE_CHANNEL = 'inference'
RESULT_CHANNEL = 'inferenceResult'
CLASS_NUMBER = 5
ACCEPT_CLASS = [3, 4]
UNKNOWN_CLASS = 0

# [signal]
BAUD_RATE = 115200
REQUEST_CHANNEL = "inferenceRequest"
REQUEST_COOLDOWN = 0.04 #second

