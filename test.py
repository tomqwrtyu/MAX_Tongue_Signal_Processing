import time

chars = 'ABCDEF'
loop = range(1, len(chars) + 1)

LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'

for idx in reversed(loop):
    print(chars[:idx])
    time.sleep(.5)
    print(LINE_UP, end=LINE_CLEAR)