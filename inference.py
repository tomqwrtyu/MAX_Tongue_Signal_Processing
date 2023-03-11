import argparse
import config
import socketio
import os
import gc
import numpy as np
import tensorflow as tf
from threading import Lock
from time import time, sleep
from copy import deepcopy
from multiprocessing import Process
from tensorflow.keras.backend import clear_session
tf.keras.mixed_precision.set_global_policy('mixed_float16')

MAXCHARLEN = max([len(config.KEY_CLASS[key]) for key in config.KEY_CLASS])
LINE_UP = '\033[1A'
LINE_CLEAR = '\x1b[2K'

def clear_line(n=1):
    LINE_UP = '\033[1A'
    LINE_CLEAR = '\x1b[2K'
    for _ in range(n):
        print(LINE_UP, end=LINE_CLEAR)

def args():
    desc = (':3')
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        '-m', '--model', type=str, default='LickingPark0309v3',
        help=('Model name in ./model .'))
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help=('Model name in ./model .'))
    return parser.parse_args()

class inference():
    def __init__(self, url, modelName, verbose) -> None:
        # connect to socketIO server
        self.__serverUrl = url
        self.__sio = None
        self.__initializeSocketIOClient()
        
        # load model
        self.__model = tf.keras.models.load_model('./model/' + modelName)
        # initialize predictor
        self.__model(np.zeros((1, config.WINDOW_SIZE, config.CHANNEL_NUMBER * config.NUM_IMF)))
        
        self.__lock = Lock()
        self.__white_list = {}
        self.__clientCount = 0
        self.__lastInferenceRecord = {}
        self.__req = {'uid': None, 'data': None}
        self.verbose = verbose
        
        
    def __initializeSocketIOClient(self):
        self.__sio = socketio.Client(reconnection=False)
        self.__sio.connect(self.__serverUrl)
        self.__sio.emit('inferenceRegister')
        self.__sio.on('whiteList', self.__newClient)
        self.__sio.on('rmWhiteList', self.__clientLeave)
        try:
            assert isinstance(self.__sio, socketio.Client)
            print("Connected to Socket server.")
        except:
            raise Exception("Maybe server is not online.")
        
    def __receiveSignal(self, req): # received clientID + CHANNEL_NUMBER * WINDOW_SIZE size of data
        self.__lock.acquire()
        self.__req = deepcopy(req)
        self.__lock.release()
        
    def  __newClient(self, info):
        self.__white_list[info['uid']] = info['stamp']
        self.__lastInferenceRecord[info['uid']] = {}
        self.__lastInferenceRecord[info['uid']]['serial_num'] = 0
        self.__lastInferenceRecord[info['uid']]['used_time'] = 0
        self.__lastInferenceRecord[info['uid']]['action'] = config.KEY_CLASS[0]
        self.__clientCount += 1
        
    def __clientLeave(self, uid):
        if not isinstance(self.__white_list.get(uid, None), type(None)):
            self.__white_list.pop(uid)
            self.__lastInferenceRecord.pop(uid)
            self.__clientCount -= 1
        
    def run(self):
        os.system('cls')
        self.__sio.on(config.REQ_RECEIVE_CHANNEL, self.__receiveSignal)
        print("Listening requests.")
        try:
            while True:
                clock = time()
                
                try:
                    clientID = self.__req['uid']
                    data = np.array(self.__req['data'].split(",")).astype(np.float32).reshape(config.WINDOW_SIZE, config.CHANNEL_NUMBER * config.NUM_IMF)
                    ser = self.__req['serial_num']
                    
                    self.__req.clear()
                    assert self.__white_list.get(clientID, False), "Client {} not in whitelist.".format(clientID)
                    res = self.__model(data[np.newaxis, :]).numpy().flatten()
                    
                    candidateIdx = np.argmax(res) + 1 if res[np.argmax(res)] > config.BELIEF_THRESHOLD else 0
                    self.__sio.emit(config.RESULT_CHANNEL, {'uid': clientID, 'action': config.KEY_CLASS[candidateIdx]})
                    self.__lastInferenceRecord[clientID]['serial_num'] = ser
                    self.__lastInferenceRecord[clientID]['used_time'] = time() - clock
                    self.__lastInferenceRecord[clientID]['action'] = config.KEY_CLASS[candidateIdx]
                    
                    if self.verbose:
                        inferenceResult = ''
                        for index, client in enumerate(self.__white_list.keys()):
                            inferenceResult += "ID: {}-{}, Spend time: {:.3f}s, Action: {}".format(client, \
                                    self.__lastInferenceRecord[client]['serial_num'],\
                                    self.__lastInferenceRecord[client]['used_time'], \
                                    self.__lastInferenceRecord[client]['action'])
                            if index + 1 < self.__clientCount:
                                inferenceResult += '\n'

                        print(inferenceResult)
                        clear_line(self.__clientCount)
                            
                    # print("ID: {}-{}, Spend time: {:.3f}s, Act: {}".format(clientID, ser, time() - clock, \
                    #       config.KEY_CLASS[candidateIdx]).ljust(MAXCHARLEN + len(clientID) + int(np.log10(ser)) + 36), end='\r')
                
                except KeyboardInterrupt:
                    break
                
                except:
                    pass
                
        except KeyboardInterrupt:
            pass
            
        finally:
            os.system('cls')
            self.__sio.disconnect()
            clear_session()
            
def sock():
    os.system("node socketIO\index.js")
    
def client():
    os.system("python signalInput.py -f")
            
def main2():
    arg = args()
    socketioServer = Process(target = sock)
    client1 = Process(target = client)
    client2 = Process(target = client)
    
    socketioServer.start()
    sleep(2) # wait for socket IO server set up.
    emdCNN = inference(config.SERVER_URL, arg.model, arg.verbose)
    client1.start()
    client2.start()
    try:
        emdCNN.run()
    except KeyboardInterrupt:
        pass
    finally:
        socketioServer.join()
        client1.join()
        client2.join()
        
def main():
    arg = args()
    emdCNN = inference(config.SERVER_URL, arg.model, arg.verbose)
    emdCNN.run()

if __name__ == '__main__':
    main()