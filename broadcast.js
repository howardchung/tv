const http = require("http");
const { spawn } = require('child_process');
const sockets = new Map();

const ffmpeg = spawn('ffmpeg', ['-i', 'rtmp://localhost/live/tv', '-c:v', 'copy', '-c:a', 'copy', '-f', 'mpegts', '-']);
ffmpeg.stdout.on('data', (data) => {
  for (let res of sockets.values()) {
      console.log('wrote %s bytes to %s sockets', data.length, sockets.size);
      res.write(data);
  }
});

const server = http.createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    const rand = Math.random();
    sockets.set(rand, res);
    req.once('close', () => {
      console.log('deleting socket %s', rand);
      sockets.delete(rand);
    });
});
const host = '0.0.0.0';
const port = 8081;
server.listen(port, host, () => {
    console.log(`Server is running on http://${host}:${port}`);
});
