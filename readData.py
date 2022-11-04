import serial  # 引用pySerial模組
import numpy as np
from time import sleep
from threading import Thread, Lock
from collections import deque

COM_PORT = 'COM3'    # 指定通訊埠名稱
BAUD_RATE = 115200    # 設定傳輸速率
SAMPLE_TIME = 1 / 500
class inference(Thread):
    def __init__(self, container, source) -> None:
        super().__init__()
        self._model = None
        self._source = source
        self._container = container
    
    def run(self):
        while self._source.is_alive():
            data = self._container.extractData()
            sleep(SAMPLE_TIME) #wait for new data
            try:
                assert type(data[0]) == np.ndarray
                self._container.peek()
            except:
                continue #it's a None
            finally:
                dataA, dataB, dataC = data
                   
        print("Inference finished.")
        
class container():
    def __init__(self, size) -> None:
        self._lock = Lock()
        self._size = size
        self._dataA = deque([], maxlen = size)
        self._dataB = deque([], maxlen = size)
        self._dataC = deque([], maxlen = size)
        
    def peek(self):
        print(self._dataA[-1], self._dataB[-1], self._dataC[-1])
    
    def newData(self, newA, newB, newC):
        self._lock.acquire()
        self._dataA.append(newA)
        self._dataB.append(newB)
        self._dataC.append(newC)
        self._lock.release()
        
    def extractData(self):
        retA, retB, retC = None, None, None
        if ((len(self._dataA) < self._size) or (len(self._dataB) < self._size) or (len(self._dataB) < self._size)):
            return [retA, retB, retC]
            
        self._lock.acquire()
        try:
            retA, retB, retC = np.asarray(self._dataA), np.asarray(self._dataB), np.asarray(self._dataC)
        finally:
            self._lock.release()
            return [retA, retB, retC]
        
class reciever(Thread):
    def __init__(self, container, port, baud_rate) -> None:
        super().__init__()
        self._serial = serial.Serial(port, baud_rate) # 初始化序列通訊埠
        self._container = container
    
    def run(self):
        try:
            i = 0
            while i < 2000:
                while self._serial.in_waiting:          # 若收到序列資料…
                    data_raw = self._serial.readline()  # 讀取一行
                    rcv = data_raw.decode(errors='surrogateescape').rstrip().split(",") # 用預設的UTF-8解碼
                    try:
                        chA, chB, chC = map(float, rcv)
                        self._container.newData(chA, chB, chC)
                    except KeyboardInterrupt:
                        break
                    except:
                        pass
                    finally:
                        i += 1
                
            print("Data collection finished.")

        except KeyboardInterrupt:
            self._serial.close()    # 清除序列通訊物件
            print('再見！')

def main():
    temp_container = container(int(1200))
    arduino = reciever(temp_container, COM_PORT, BAUD_RATE)
    deepNN = inference(temp_container, arduino)
    arduino.start()
    deepNN.start()
    arduino.join()
    deepNN.join()
        
if __name__ == '__main__':
    main()