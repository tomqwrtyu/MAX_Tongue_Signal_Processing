# [common]
NUM_IMF = 3
CHANNEL_NUMBER = 3
WINDOW_SIZE = 100
SAMPLE_RATE = 500 #Hz
KEY_CLASS = {0:'undefined action', 1:'up', 2:'down', 3:'left', 4:'right', 5:'quick touch'}
SERVER_URL = 'http://maxtongue.ddns.net:3000'

# [inference]
REQ_RECEIVE_CHANNEL = 'inference'
RESULT_CHANNEL = 'inferenceResult'
CLASS_NUMBER = 5
ID_LEN = 6
BELIEF_THRESHOLD = 0.9

# [signal]
BAUD_RATE = 115200
REQUEST_CHANNEL = "inferenceRequest"
REQUEST_COOLDOWN = 0.04 #second