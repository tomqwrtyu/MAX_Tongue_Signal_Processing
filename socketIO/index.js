const app = require('express')();
const http = require('http').Server(app);
const io = require('socket.io', {transports: ['websocket']})(http);
const port = process.env.PORT || 3000;

let ip = '192.168.1.37';
let ID_LEN = 6;
let signalHandler = new Map();
let availableID = [];
let startUp = Date.now() / 1000;
let inference_cooldown = 50; //ms

app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

io.on('connection', (socket) => {
    console.log('a user connected', socket.id);
    let uid = null;
    let emitUID = null;

    socket.on('chat message', (msg) => {
        io.emit('chat message', msg);
    });

    socket.on('register', (info) => {
        let id = make_id(info['time']);
        signalHandler.set(id, info['time'])
        uid = id;
        availableID.push(id);
        socket.join(id);
        socket.emit('registerInfo', id);
        io.to('inferenceNode').emit('whiteList', {'uid': id, 'stamp': info['time']});
    });

    socket.on('signalRegister', () => {
        if (availableID.length > 0){
            id = availableID.pop();
            emitUID = id;
            socket.emit('registerInfo', id);
            socket.on(id, (rcv) => {
                io.to(id).emit("r" + id, rcv);
            });
        }
        else{
            socket.emit('registerInfo', 'No client available.');
        }
    });

    socket.on('inferenceRegister', () => {
        socket.join('inferenceNode');
    });

    socket.on('inferenceRequest', (req) => {
        if (signalHandler.has(req.uid)){
            io.to('inferenceNode').emit('inference', req);
        }
    });

    socket.on('inferenceResult', (res) => {
        io.emit('chat message', res.uid + ',' + res.action); // need to be spcified
    });

    socket.on('disconnect', () => {
        if (signalHandler.has(uid)){
            signalHandler.delete(uid);
            io.to('inferenceNode').emit('rmWhiteList', uid);
        }
        if (emitUID != null && signalHandler.has(emitUID)){
            availableID.push(emitUID);
        }
        console.log('user disconnected', socket.id);
    });
});

http.listen(port, ip, () => {
    console.log(`Socket.IO server running at http://${ip}:${port}/`);
});

function make_id(data){
    let t = (Number(data) - startUp).toString(16).split('.');
    let f = t[0];
    let b = t[1];
    while(b.length < ID_LEN){
        for (let i = 0; i < f.length; i++){
            if (b.length < ID_LEN){
                b = b + f[i];
            }
        }
    }
    return b;
}