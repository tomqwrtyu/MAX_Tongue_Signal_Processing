const app = require('express')();
const http = require('http').Server(app);
const io = require('socket.io')(http);
const port = process.env.PORT || 3000;

let ID_LEN = 6;
let user = new Map();
let startUp = Date.now() / 1000;
let inference_cooldown = 10; //ms

app.get('/', (req, res) => {
  res.sendFile(__dirname + '/index.html');
});

io.on('connection', (socket) => {
    console.log('a user connected');
    let uid = null;

    socket.on('chat message', (msg) => {
        io.emit('chat message', msg);
    });

    socket.on('register', (data) => {
        let id = make_id(data);
        user.set(id, data)
        uid = id;
        socket.emit('registerSuccessful', id);
        io.emit('whiteList', {'uid': id, 'stamp': data});
    });

    socket.on('inferenceRequest', (req) => {
        if (user.has(req.uid)){
            io.emit('inference', req);
        }
    });

    socket.on('inferenceResult', (res) => {
        io.emit('chat message', res.uid + ',' + res.action);
    });

    socket.on('disconnect', () => {
        if (user.has(uid)){
            user.delete(uid);
            io.emit('rmWhiteList', {'uid': id});
        }
        console.log('user disconnected');
    });
});

http.listen(port, () => {
    console.log(`Socket.IO server running at http://localhost:${port}/`);
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