import serial  # 引用pySerial模組
import numpy as np
from time import sleep, time
from threading import Thread, Lock

COM_PORT = 'COM3'    # 指定通訊埠名稱
NO_ARDUINO = False
RECORDTYPE = 'tongue_out_discrete_2'
SAMPLE_TIME = 1 / 500
RECORDTIME = 10 #seconds
BAUD_RATE = 115200    # 設定傳輸速率


class recorder(Thread):
    def __init__(self, container, source, filepath) -> None:
        super().__init__()
        self._source = source
        self._container = container
        self._overallData = np.array([])
        self._filepath = filepath
    
    def run(self):
        while self._source.is_alive():
            data = self._container.extractData()
            try:
                assert type(data[0]) == np.ndarray
                dataA, dataB, dataC = data
                canonicalData = np.concatenate([dataA[np.newaxis, :], dataB[np.newaxis, :], dataC[np.newaxis, :]], axis=0)
                if self._overallData.any():
                    self._overallData = np.concatenate([self._overallData, canonicalData[np.newaxis, :]], axis=0)
                else:
                    self._overallData = canonicalData[np.newaxis, :]
            except:
                continue #it's a None
            finally:
                sleep(SAMPLE_TIME) #wait for new data
        
        print("{} data recorded.".format(self._overallData.shape[0]))
        np.save(self._filepath, self._overallData)
        print("Recording finished.")
        
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
    def __init__(self, container, port, baud_rate, maxTime) -> None:
        super().__init__()
        self._maxTime = maxTime
        self._serial = serial.Serial(port, baud_rate) # 初始化序列通訊埠
        self._container = container
    
    def run(self):
        try:
            i = 0
            while i < self._maxTime:
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
            
class generator():
    def __init__(self) -> None:
        self.v = {'x': 0, 'y': 60, 'z': 120}
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
    temp_container = container(int(WINDOWSIZE))
    if NO_ARDUINO:
        arduino = generator(temp_container)
    else:
        arduino = reciever(temp_container, COM_PORT, BAUD_RATE, int(RECORDTIME / SAMPLE_TIME))
    record = recorder(temp_container, arduino, filepath)
    arduino.start()
    record.start()
    print("Recording start.")
    arduino.join()
    record.join()
        
if __name__ == '__main__':
    main()