import numpy as np
import plotly.express as px

SAMPLE_TIME = 1 / 500
WINDOWSIZE = 750

def main():
    filename = 'coswave'
    filePath = './data/' + filename + '.npy'
    data = np.load(filePath)
    print(data.shape)

    # flatten = data[0]
    # for i in range(1, data.shape[0]):
    #     flatten = np.concatenate([flatten, data[i, :, -1, np.newaxis]], axis=1)
    # windowSize = data[0].shape[1]
    # avgNzP = np.empty((data.shape[0], ))
    
    # for i in range(data.shape[0]):
    #     a, b, c = data[i]
    #     nza, nzb, nzc = np.count_nonzero(a), np.count_nonzero(b), np.count_nonzero(c)
    #     print("Nonzero Percentage: {:.4f}, {:.4f}, {:.4f}".format(nza / windowSize, nzb / windowSize, nzc / windowSize))
    #     avgNzP[i] = (nza + nzb + nzc) / (3 * windowSize)
    #     print("Average nonzero Percentage: {:.4f}".format(avgNzP[i]))
        
    #fig = px.line(y=[flatten[0], flatten[1], flatten[2]])
    fig = px.line(y=[data[0], data[1], data[2]])
    #fig = px.line(y=avgNzP)
    fig.show()
        
    
if __name__ == '__main__':
    main()