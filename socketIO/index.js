const app = require('express')();
const http = require('http').Server(app);
const io = require('socket.io')(http);
const port = process.env.PORT || 3000;

let ip = '192.168.1.37';
let ID_LEN = 6;
let signalHandler = new Map();
let availableHandler = [];
let availableSignal = [];
let startUp = Date.now() / 1000;

app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

io.on('connection', (socket) => {
    console.log('[', Date(Date.now()).toString(), '] a user connected, Online user count:', Object.keys(io.sockets.sockets).length);
    let uid = null;
    let emitUID = null;

    socket.on('chat message', (msg) => {
        io.emit('chat message', msg);
    });

    socket.on('inferenceRegister', () => {
        socket.join('inferenceNode');
        socket.on('inferenceResult', (res) => {
            io.emit("chat message", res.uid + ": " + res.action);
            io.to('players').emit(res.uid + '_action', res.action); // need to be specified
        });
    });

    socket.on('playerRegister', () => {
        socket.join('players');
    });

    socket.on('remoteSignalRegister', () => { //ISSUE: how to connect with specific player?
        if (availableHandler.length > 0){
            id = availableHandler.pop();
            availableSignal.push(id);
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

    socket.on('signalHandlerRegister', (info) => {
        let id = make_id(info['time']);
        // let id = info['localIP'];
        signalHandler.set(id, info['time']);
        uid = id;
        availableHandler.push(id);
        socket.join(id);
        socket.emit('registerInfo', id);
        io.to('inferenceNode').emit('whiteList', {'uid': id, 'stamp': info['time']});
        socket.on('inferenceRequest', (req) => {
            if (signalHandler.has(req.uid)){
                io.to('inferenceNode').emit('inference', req);
            }
        });
    });

    socket.on('disconnect', () => {
        if (uid != null && signalHandler.has(uid)){
            signalHandler.delete(uid);
            io.to('inferenceNode').emit('rmWhiteList', uid);
        }
        if (emitUID != null && signalHandler.has(emitUID)){
            availableID.push(emitUID);
        }
        console.log('[', Date(Date.now()).toString(), '] a user disconnected, Online user count:', Object.keys(io.sockets.sockets).length);
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