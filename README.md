# MAX-Tongue-repo
### Prerequisite [Local inference server]
#### CUDA & cuDNN
CUDA = 11.7, cuDNN = 8.2.1
#### Python
This project is developed in Python 3.10.7.
<br>
<br>   `pip3 install -r requirement.txt` 
<br>
#### Socket IO
Make sure NodeJS(https://nodejs.org/en/) is downloaded and install express, socket.io <br>
as the instructions in https://socket.io/get-started/chat. 
<br>
<br> `npm install express@4`
<br> `npm install socket.io@2.5.0`
<br>
### Usage
* Open socketIO server with
<br> `node index.js` <br>
* Run inference.py for inference request, check config.py for some settings.
<br> `python inference.py` <br>
### Experimental concept
Inspired by label smoothing, we assigned random value to label with "undefined action" which is usually assiged with [0] * #class 
beacuse we want model to learn whether the signal is a defined class or just a noise but assigning all zero value will result in 
gradient vanishing. Also, we think it is reasonable to assign those values since signals by human muscles have some similarity, 
differences could be caused by muscle strength or sensor detaching (however, we found interesting is that only "appropriate" value 
can prevnt gradient vanishing). <br>
### Problem
Reversing left and right channel on the fly could not reverse the inference result, a possible reason is that positional encoding is not implemented on channel but only on time series? <br>
### Reference
Model Architecture: ConTraNet - https://arxiv.org/abs/2206.10677 (kernel size and component layers are modified)
