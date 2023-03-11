import argparse
import config
import serial
import socketio
import socket
import numpy as np
from collections import deque
from emd.sift import sift
from time import sleep, time

record_path = './data/230220_l5m6r7_record_X.npy'

def args():
    desc = (':3')
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        '-p', '--port', type=str, default='COM3',
        help=('Port to arduino usb connection.'))
    parser.add_argument(
        '-f', '--fakeSignal', action='store_true',
        help=('Raise this flag to use fake signal.') 
    )
    parser.add_argument(
        '-r', '--remoteMode', action='store_true',
        help=('Raise this flag to wait for signal through Wi-Fi.') 
    )
    return parser.parse_args()

class receiver():
    def __init__(self, url, port, baud_rate, record = None) -> None: 
        if isinstance(record, loader):
            self.__serial = record
        else:
            self.__serial = serial.Serial(port, baud_rate)
            
        self.__clientID = ''
        self.__serverUrl = url
        self.__sio = None
        self.__initializeSocketIOClient()

        self.__container = deque([], maxlen=config.WINDOW_SIZE)
        
    def __initializeSocketIOClient(self):
        self.__sio = socketio.Client(reconnection=False)
        self.__sio.connect(self.__serverUrl)
        self.__sio.on('registerInfo', self.__getID)
        self.__sio.emit('signalHandlerRegister', {'time': "{:.3f}".format(time()), 'remote': True, 'localIP': socket.gethostbyname(socket.gethostname())})
        sleep(0.1)
        try:
            assert isinstance(self.__sio, socketio.Client)
            print("Connected to Socket server with ID: {}.".format(self.__clientID))
        except:
            raise Exception("Maybe server is not online.")
        
    def __getID(self, id):
        self.__clientID = id

    def run(self):
        try:
            escape = False
            stamp = time()
            count = 0
            while not escape:
                while self.__serial.in_waiting:
                    data_raw = self.__serial.readline() 
                    rcv = data_raw.decode(errors='surrogateescape').rstrip()
                    try:
                        if len(rcv.split(',')) < config.CHANNEL_NUMBER:
                            continue
                        self.__container.append(rcv.split(',')) # a0,b0,c0, a1,b1,c1 .... an,bn,cn, <-- tackle this with rstrip() and 
                                                     # reshape with (WINDOW_SIZE, CHANNEL_SIZE) and then transpose -> (CHANNEL_SIZE, WINDOW_SIZE)
                        
                        if len(self.__container) == config.WINDOW_SIZE and time() > (stamp + config.REQUEST_COOLDOWN):
                            stamp = time()
                            count += 1
                            self.__sio.emit(config.REQUEST_CHANNEL, {'uid': self.__clientID, 'data': self.__emdSignal(self.__container), 'serial_num': count})
                            print("ID: {} send {}.".format(self.__clientID, count))
                            config.clear_line()
                            
                    except KeyboardInterrupt:
                        escape = True
                        break
                    except:
                        pass
                            
            raise KeyboardInterrupt

        except KeyboardInterrupt:
            self.__serial.close() 
            self.__sio.disconnect()
            print('Serial disconnected.'.ljust((len(self.__clientID) + int(np.log10(count)) + 12)))
            
    def __emdSignal(self, sig):
        sig = np.array(sig).astype(np.float32).reshape(config.CHANNEL_NUMBER, config.WINDOW_SIZE).T
        ret = None
    
        for c in range(config.CHANNEL_NUMBER):
            raw = sig[:, c]
            imf = sift(raw, max_imfs=config.NUM_IMF, imf_opts={'sd_thresh': 0.1})
            
            if imf.shape[-1] < config.NUM_IMF:
                compensate = np.zeros((config.WINDOW_SIZE, config.NUM_IMF - imf.shape[-1]))
                imf = np.concatenate([imf, compensate], axis = 1)
            
            if not type(ret) == np.ndarray: 
                ret = imf
            else: 
                ret = np.concatenate([ret, imf], axis = 1)
              
        return ",".join(ret[np.newaxis, :].astype(np.str_).flatten().tolist())
    
class remoteReceiver():
    def __init__(self, url) -> None: 
        self.__clientID = ''
        self.__serverUrl = url
        self.__sio = None
        self.__initializeSocketIOClient()

        self.__container = deque([], maxlen=config.WINDOW_SIZE)
        
    def __initializeSocketIOClient(self):
        self.__sio = socketio.Client()
        self.__sio.connect(self.__serverUrl)
        self.__sio.on('registerInfo', self.__getID)
        self.__sio.emit('signalHandlerRegister', {'time': "{:.3f}".format(time()), 'remote': True, 'localIP': socket.gethostbyname(socket.gethostname())})
        sleep(0.1)
        try:
            assert isinstance(self.__sio, socketio.Client)
            print("Connected to Socket server with ID: {}.".format(self.__clientID))
        except:
            raise Exception("Maybe server is not online.")
        
    def __getID(self, id):
        self.__clientID = id
        self.__sio.on('r' + id, self.__getData)
    
    def __getData(self, rcv):
        try:
            rcv_split = rcv.split(',')
            if len(rcv_split) == config.CHANNEL_NUMBER:
                self.__container.append(rcv_split)
        except:
            pass
        
    def __emdSignal(self, sig):
        sig = np.array(sig).astype(np.float32).reshape(config.CHANNEL_NUMBER, config.WINDOW_SIZE).T
        ret = None
    
        for c in range(config.CHANNEL_NUMBER):
            raw = sig[:, c]
            imf = sift(raw, max_imfs=config.NUM_IMF, imf_opts={'sd_thresh': 0.1})
            
            if imf.shape[-1] < config.NUM_IMF:
                compensate = np.zeros((config.WINDOW_SIZE, config.NUM_IMF - imf.shape[-1]))
                imf = np.concatenate([imf, compensate], axis = 1)
            
            if not type(ret) == np.ndarray: 
                ret = imf
            else: 
                ret = np.concatenate([ret, imf], axis = 1)
              
        return ",".join(ret[np.newaxis, :].astype(np.str_).flatten().tolist())
        
    def run(self):
        try:
            escape = False
            stamp = time()
            count = 0
            while not escape:
                try:
                    if len(self.__container) == config.WINDOW_SIZE and time() > (stamp + config.REQUEST_COOLDOWN):
                        stamp = time()
                        count += 1
                        self.__sio.emit(config.REQUEST_CHANNEL, {'uid': self.__clientID, 'data': self.__emdSignal(self.__container), 'serial_num': count})
                        print("ID: {} send {}.".format(self.__clientID, count).ljust((len(self.__clientID) + int(np.log10(count)) + 11)), end='\r')
                        self.__container.popleft()
                        
                except KeyboardInterrupt:
                    escape = True
                    break
                except:
                    pass
        
        except KeyboardInterrupt:
            self.__sio.disconnect()
            print('Serial disconnected.'.ljust((len(self.__clientID) + int(np.log10(count)) + 12)))
    
class loader():
    def __init__(self, path) -> None:
        self.data = np.load(path)
        self.in_waiting = True
        self.__i = 0
        
    def readline(self):
        try:
            ret = ["%.2f" %x for x in self.data[self.__i, :].tolist()]
            return ",".join(ret).encode(encoding='UTF-8')
        except KeyboardInterrupt:
            self.in_waiting = False
        except:
            self.__i = 0
            ret = ["%.2f" %x for x in self.data[self.__i, :].tolist()]
            return ",".join(ret).encode(encoding='UTF-8')
        finally:
            self.__i += 1
    
    def close(self):
        pass

def main():
    arg = args()
    if arg.fakeSignal:
        signal = receiver(config.SERVER_URL, arg.port, config.BAUD_RATE, loader(record_path))
    elif arg.remoteMode:
        signal = remoteReceiver(config.SERVER_URL)
    else:
        signal = receiver(config.SERVER_URL, arg.port, config.BAUD_RATE)
    signal.run()

if __name__ == '__main__':
    main()
