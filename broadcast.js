const http = require("http");
const { spawn } = require('child_process');
const ffmpeg = spawn('ffmpeg', ['-i', 'rtmp://localhost/live/tv', '-c:v', 'copy', '-c:a', 'copy', '-f', 'mpegts', '-']);

const sockets = new Map();
const server = http.createServer();
const host = '0.0.0.0';
const port = 8081;
server.listen(port, host, () => {
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
  for (let socket of sockets.values()) {
      console.log('wrote %s bytes to socket', data.length);
      socket.write(data);
  }
});
