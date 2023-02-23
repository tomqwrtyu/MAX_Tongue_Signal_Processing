import argparse
import config
import socketio
import numpy as np
import tensorflow as tf
from threading import Lock
from time import time
from copy import deepcopy
from tensorflow.keras.backend import clear_session
tf.keras.mixed_precision.set_global_policy('mixed_float16')

MAXCHARLEN = max([len(config.KEY_CLASS[key]) for key in config.KEY_CLASS])

def args():
    desc = (':3')
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        '-m', '--model', type=str, default='LickingPark0222',
        help=('Model name in model/.'))
    return parser.parse_args()

class inference():
    def __init__(self, url, modelName) -> None:
        # connect to socketIO server
        self.__sio = socketio.Client()
        self.__sio.connect(url)
        try:
            assert isinstance(self.__sio, socketio.Client)
            print("Connected to Socket server.")
        except:
            raise Exception("Maybe server is not online.")
        
        # load model
        self.__model = tf.keras.models.load_model('./model/' + modelName)
        # initialize predictor
        self.__model.predict(np.zeros((1, config.WINDOW_SIZE, config.CHANNEL_NUMBER * config.NUM_IMF)), verbose = False)
        
        self.__lock = Lock()
        self.__white_list = {}
        self.__req = {'uid': None, 'data': None}
        
        self.__sio.on('whiteList', self.__newClient)
        self.__sio.on('rmWhiteList', self.__clientLeave)
        
    def __receiveSignal(self, req): # received clientID + CHANNEL_NUMBER * WINDOW_SIZE size of data
        self.__lock.acquire()
        self.__req = deepcopy(req)
        self.__lock.release()
        
    def  __newClient(self, info):
        self.__white_list[info['uid']] = info['stamp']
        
    def __clientLeave(self, uid):
        self.__white_list.pop(uid)
        
    def run(self):
        print("Listening requests.")
        self.__sio.on(config.REQ_RECEIVE_CHANNEL, self.__receiveSignal)
        try:
            while True:
                clock = time()
                
                try:
                    clientID = self.__req['uid']
                    data = np.array(self.__req['data'].split(",")).astype(np.float32).reshape(config.WINDOW_SIZE, config.CHANNEL_NUMBER * config.NUM_IMF)
                    ser = self.__req['serial_num']
                    
                    self.__req.clear()
                    assert self.__white_list.get(clientID, False), "Client {} not in whitelist.".format(clientID)
                    res = self.__model.predict(data[np.newaxis, :], verbose = False).flatten()
                    
                    candidateIdx = np.argmax(res) + 1 if res[np.argmax(res)] > config.BELIEF_THRESHOLD else 0
                    self.__sio.emit(config.RESULT_CHANNEL, {'uid': clientID, 'action': config.KEY_CLASS[candidateIdx]})
                    print("ID: {}-{: 5d}, Res: {}, Spend time: {:.3f}".format(clientID, ser, config.KEY_CLASS[candidateIdx], time() - clock).ljust(MAXCHARLEN + config.ID_LEN + 36), end='\r')
                
                except KeyboardInterrupt:
                    break
                
                except:
                    pass
                
        except KeyboardInterrupt:
            self.__sio.disconnect()
            clear_session()
            
        finally:
            self.__sio.disconnect()
            clear_session()

def main():
    arg = args()
    emdCNN = inference(config.SERVER_URL, arg.model)
    emdCNN.run()

if __name__ == '__main__':
    main()