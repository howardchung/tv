const http = require("http");
const { spawn } = require("child_process");
const sockets = new Map();

//ffmpeg -err_detect ignore_err -i rtmp://localhost:1935/live/tv -c:v copy -c:a copy -f mpegts - | node broadcast.js
const ffmpeg = spawn("ffmpeg", ["-err_detect", "ignore_err", "-i", "rtmp://localhost:1935/live/tv", "-c:v", "copy", "-c:a", "copy", "-f", "mpegts", "-"]);
ffmpeg.stderr.on('data', (data) => {
  console.log(data);
});
ffmpeg.stdout.on('data', (data) => {
  for (let res of sockets.values()) {
      // console.log('wrote %s bytes to %s sockets', data.length, sockets.size);
      res.write(data);
  }
});
ffmpeg.stdout.on('close', () => {
  process.exit(0);
});

const server = http.createServer((req, res) => {
    // nginx sets headers
    // res.setHeader('Access-Control-Allow-Origin', '*');
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
