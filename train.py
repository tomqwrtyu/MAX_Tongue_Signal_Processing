import pandas as pd
import numpy as np
import tensorflow as tf

BATCH_SIZE = 4
CHANNEL_NUMBER = 3
WINDOW_SIZE = 750
SLIDING_STEP = int(WINDOW_SIZE * 0.4)
CLASS_NUMBER = 2

def slicingAndNormalize(arr):
    def normalizer(X):
        ret = np.zeros(X.shape)
        for i in range(CHANNEL_NUMBER):
            mean = np.mean(X[0, i])
            std = np.std(X[0, i])
            for j in range(WINDOW_SIZE):
                ret[0, i, j] = (X[0, i, j] - mean) / std
                    
        return ret
    
    totalLength = arr.shape[-1]
    if totalLength <= WINDOW_SIZE:
        return arr
    ret = normalizer(arr[np.newaxis, :, :WINDOW_SIZE])
    
    i = SLIDING_STEP
    while (totalLength - i) > WINDOW_SIZE:
        new = normalizer(arr[np.newaxis, :, i:(i + WINDOW_SIZE)])
        ret = np.concatenate([ret, new], axis=0)
        i += SLIDING_STEP
    return ret

def buildModel():
    model = tf.keras.Sequential([
        tf.keras.layers.Conv1D(8, 12, activation='relu', input_shape=(CHANNEL_NUMBER, WINDOW_SIZE)),
        tf.keras.layers.MaxPool1D(padding='same'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Conv1D(32, 12, strides=5, activation='relu'),
        tf.keras.layers.MaxPool1D(padding='same'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Conv1D(48, 12, strides=3, activation='relu'),
        tf.keras.layers.MaxPool1D(padding='same'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Conv1D(96, 12, activation='relu'),
        tf.keras.layers.Dense(512, activation='relu'),
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dense(CLASS_NUMBER, activation='softmax')]
    )
    model.compile(optimizer='adam',
                loss=tf.keras.losses.BinaryCrossentropy(),
                metrics=[tf.keras.metrics.Precision(),
                         tf.keras.metrics.Recall()])
    model.summary()
    return model

def main():
    trainFile = './data/coswave.npy'
    X = slicingAndNormalize(np.load(trainFile))
    y = tf.keras.layers.Conv1D(8, 12, activation='relu', input_shape=(CHANNEL_NUMBER, WINDOW_SIZE))(X)
    print(y.shape)
    #model = buildModel()
    
if __name__ == '__main__':
    main()