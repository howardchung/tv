const http = require("http");
const { spawn } = require('child_process');
const ffmpeg = spawn('ffmpeg', ['-i', 'rtmp://localhost/live/tv', '-c:v', 'copy', '-c:a', 'copy', '-f', 'mpegts', '-']);

const sockets = new Map();
const server = http.createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    const rand = Math.random();
    sockets.set(rand, res);
    res.on('end', () => {
      console.log('deleting socket %s', rand);
      sockets.delete(rand);
    });
});
const host = '0.0.0.0';
const port = 8081;
server.listen(port, host, () => {
    console.log(`Server is running on http://${host}:${port}`);
});
server.on('connection', (socket) => {

});
ffmpeg.stdout.on('data', (data) => {
  for (let res of sockets.values()) {
      console.log('wrote %s bytes to %s sockets', data.length, sockets.size);
      res.write(data);
  }
});
