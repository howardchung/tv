const http = require("http");
const { spawn } = require('node:child_process');
const ffmpeg = spawn('ffmpeg', ['-i', 'rtmp://localhost/live/tv', '-c:v', 'copy', '-c:a', 'copy', '-f', 'mpegts', '-']);

const sockets = new Map();
const server = http.createServer();
server.listen(8081, '0.0.0.0', () => {
    console.log(`Server is running on http://${host}:${port}`);
});
server.on('connection', (socket) => {
  const rand = Math.random();
  sockets.put(rand, socket);
  socket.on('finished', () => {
    sockets.delete(rand);
  });
});
ffmpeg.stdout.on('data', (data) => {
  sockets.values().forEach(socket => {
    socket.write(data);
  });
});