import serial  # 引用pySerial模組
import numpy as np
#import unreal as ue
from time import sleep
from threading import Thread, Lock
from collections import deque
import tensorflow as tf

COM_PORT = 'COM3'    # 指定通訊埠名稱
NO_ARDUINO = False
BAUD_RATE = 115200    # 設定傳輸速率
SAMPLE_TIME = 1 / 500
WINDOW_SIZE = 600
model_path = 'LickenPark'
class inference(Thread):
    def __init__(self, container, source, modelPath) -> None:
        super().__init__()
        self._model = tf.keras.models.load_model(modelPath)
        self._source = source
        self._container = container
    
    def run(self):
        while self._source.is_alive():
            data = self._container.extractData()
            try:
                assert type(data[0]) == np.ndarray
                inputData = np.asarray(data)
                res = self._model.predict(inputData,
                                          verbose = False)
                if res[0] == 1:
                    print("Licking.")
                else:
                    print("Not licking.")
                #self._container.peek()
            except:
                continue #it's a None
            finally:
                sleep(SAMPLE_TIME) #wait for new data
                   
        print("Inference finished.")
        
class container():
    def __init__(self, size) -> None:
        self._lock = Lock()
        self._size = size
        self._dataA = deque([], maxlen = size)
        self._dataB = deque([], maxlen = size)
        self._dataC = deque([], maxlen = size)
    
    def newData(self, newA, newB, newC):
        self._lock.acquire()
        self._dataA.append(newA)
        self._dataB.append(newB)
        self._dataC.append(newC)
        self._lock.release()
        
    def extractData(self):
        if ((len(self._dataA) < self._size) or (len(self._dataB) < self._size) or (len(self._dataB) < self._size)):
            return np.array([None, None, None])
            
        self._lock.acquire()
        try:
            ret = np.asarray(self._dataA)[:, np.newaxis]
            ret = np.concatenate([ret, np.asarray(self._dataB)[:, np.newaxis]], axis=1)
            ret = np.concatenate([ret, np.asarray(self._dataC)[:, np.newaxis]], axis=1)
            return ret[np.newaxis, :]
        finally:
            self._lock.release()
            
        
class reciever(Thread):
    def __init__(self, container, port, baud_rate) -> None:
        super().__init__()
        self._serial = serial.Serial(port, baud_rate) # 初始化序列通訊埠
        self._container = container
    
    def run(self):
        try:
            while True:
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

        except KeyboardInterrupt:
            self._serial.close()    # 清除序列通訊物件
            print('Serial disconnected.')
            
class generator():
    def __init__(self) -> None:
        self.v = {'x': 0, 'y': 10, 'z': 20}
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
    temp_container = container(WINDOW_SIZE)
    if NO_ARDUINO:
        arduino = generator(temp_container)
    else:
        arduino = reciever(temp_container, COM_PORT, BAUD_RATE)
    #test = ue.Actor()
    deepNN = inference(temp_container, arduino, model_path)
    arduino.start()
    deepNN.start()
    arduino.join()
    deepNN.join()
        
if __name__ == '__main__':
    main()