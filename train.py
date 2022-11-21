import pandas as pd
import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split

BATCH_SIZE = 4
CHANNEL_NUMBER = 3
WINDOW_SIZE = 600
SLIDING_STEP = int(WINDOW_SIZE * 0.4)
CLASS_NUMBER = 2
if CLASS_NUMBER < 3:
        CLASS_NUMBER = 1

def slicingAndNormalize(arr):
    def normalizer(X):
        ret = np.zeros(X.shape)
        mean = np.average(X, axis=1)
        std = np.std(X, axis=1)
        ret = (X - mean) / std
        return ret
    
    totalLength = arr.shape[0]
    if totalLength <= WINDOW_SIZE:
        return arr
    ret = normalizer((arr[:WINDOW_SIZE, :])[np.newaxis, :])
    
    i = SLIDING_STEP
    while (totalLength - i) > WINDOW_SIZE:
        new = normalizer((arr[i: (i + WINDOW_SIZE), :])[np.newaxis, :])
        ret = np.concatenate([ret, new], axis=0)
        i += SLIDING_STEP
    return ret

def buildModel():
    model = tf.keras.Sequential([
        tf.keras.layers.Conv1D(8, 8, activation='relu', input_shape=(WINDOW_SIZE, CHANNEL_NUMBER)),
        tf.keras.layers.BatchNormalization(axis=1),
        tf.keras.layers.MaxPool1D(padding='same'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Conv1D(32, 8, strides=4, activation='relu'),
        tf.keras.layers.BatchNormalization(axis=1),
        tf.keras.layers.MaxPool1D(padding='same'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Conv1D(48, 8, strides=2, activation='relu'),
        tf.keras.layers.BatchNormalization(axis=1),
        tf.keras.layers.MaxPool1D(padding='same'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Conv1D(96, 8, activation='relu'),
        tf.keras.layers.BatchNormalization(axis=1),
        tf.keras.layers.MaxPool1D(padding='same'),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(512, activation='relu'),
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dense(CLASS_NUMBER, activation='softmax')]
    )
    model.compile(optimizer='adam',
                loss=tf.keras.losses.BinaryCrossentropy(),
                metrics=[tf.keras.metrics.Accuracy(),
                         tf.keras.metrics.Precision(),
                         tf.keras.metrics.Recall()])
    #model.summary()
    return model

def main():
    X = 0
    y = 0
    #Label 1
    for trainFile in ['./data/lick.npy', './data/lick2.npy']:
        Xi = slicingAndNormalize(np.load(trainFile))
        yi = np.array([1] * Xi.shape[0])
        if type(X) == int:
            X = Xi.copy()
            y = yi.copy()
        else:
            print(y.shape, yi.shape)
            X = np.concatenate([X, Xi], axis = 0)
            y = np.concatenate([y, yi])
    #Label 0
    for trainFile in ['./data/notlick.npy']:
        Xi = slicingAndNormalize(np.load(trainFile))
        yi = np.array([0] * Xi.shape[0])
        if type(X) == int:
            X = Xi.copy()
            y = yi.copy()
        else:
            X = np.concatenate([X, Xi], axis = 0)
            y = np.concatenate([y, yi])
    
    print(X.shape, y.shape)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=777)
    model = buildModel()
    model.fit(x=X_train,
              y=y_train,
              epochs=20,
              batch_size=BATCH_SIZE,
              validation_data=(X_test, y_test))
    model.save('LickenPark', save_format='tf')
    
if __name__ == '__main__':
    main()