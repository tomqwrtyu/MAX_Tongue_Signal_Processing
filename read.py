import serial  # 引用pySerial模組
import plotly.graph_objs as go
import plotly.io as pio

#Data visualization
pio.renderers.default = "png"
fig = go.FigureWidget(data=[go.Scatter(x=[], y=[])])
scatter = fig.data[0]

COM_PORT = 'COM3'    # 指定通訊埠名稱
BAUD_RATES = 115200    # 設定傳輸速率
sampleTime = 1
ser = serial.Serial(COM_PORT, BAUD_RATES)   # 初始化序列通訊埠
# initTime = time.time()
# timeRec = np.array([], dtype=np.float64)
# serialRec = np.array([], dtype=np.int64)

lastTime = 0
lastData = 0
print("Serial online.")
try:
    while True:
        while ser.in_waiting:          # 若收到序列資料…
            data_raw = ser.readline()  # 讀取一行
            rcv = data_raw.decode(errors='surrogateescape').rstrip().split(" ") # 用預設的UTF-8解碼
            try:
                timeStamp, data = map(float, rcv)
                print(timeStamp, data)
                with fig.batch_update():
                    scatter.x += (lastTime, timeStamp)
                    scatter.y += (lastData, data)
                lastTime, lastData = timeStamp, data
            except KeyboardInterrupt:
                break
            except:
                pass
            # timeRec = np.append(timeRec, time.time() - init_time)
            # try:
            #     serialRec = np.append(serialRec, np.int64(data.rstrip()))
            # except:
            #     serialRec = np.append(serialRec, data.rstrip())
            # print('接收到的原始資料：', data_raw)
            # print('接收到的資料：', data)

except KeyboardInterrupt:
    ser.close()    # 清除序列通訊物件
    fig.write_image("res.png")
    print('再見！')