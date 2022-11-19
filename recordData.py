import serial  # 引用pySerial模組
import numpy as np
from time import sleep

COM_PORT = 'COM3'    # 指定通訊埠名稱
NO_ARDUINO = True
RECORDTYPE = 'coswave'
SAMPLE_TIME = 1 / 500
RECORDTIME = 15 #seconds
BAUD_RATE = 115200    # 設定傳輸速率

class generator():
    def __init__(self) -> None:
        self.v = {'x': 0, 'y': 5, 'z': 10}
        self.in_waiting = True
        
    def readline(self):
        temp = np.cos([(self.v['x'] / 180 * np.pi), (self.v['y'] / 180 * np.pi), (self.v['z'] / 180 * np.pi)]).tolist()
        for key in self.v:
            self.v[key] += 1
        ret = ''
        for x in temp:
          ret = ret + str(x) + ','
          
        return ret.rstrip(',').encode(encoding='UTF-8')
    
    def close(self):
        pass

def main():
    filepath = './data/' + RECORDTYPE
    if NO_ARDUINO:
        ser = generator()
    else:
        ser = serial.Serial(COM_PORT, BAUD_RATE)
    print("Recording start.")
    maxTime = int(RECORDTIME / SAMPLE_TIME)
    record = None
    firstTime = True
    try:
        i = 0
        while ser.in_waiting and i < maxTime:  # 若收到序列資料…
            data_raw = ser.readline()  # 讀取一行
            rcv = data_raw.decode(errors='surrogateescape').rstrip().split(",") # 用預設的UTF-8解碼
            try:
                new = np.array(list(map(float, rcv)))
                if firstTime:
                    firstTime = False
                    record = new[:, np.newaxis]
                else:
                    record = np.concatenate([record, new[:, np.newaxis]], axis=1)
            except KeyboardInterrupt:
                break
            except:
                pass
            finally:
                i += 1
            
        print("Data collection finished.")

    except KeyboardInterrupt:
        np.save(filepath, record)
        ser.close()    # 清除序列通訊物件
        print('再見！')
        
    np.save(filepath, record)
        
if __name__ == '__main__':
    main()