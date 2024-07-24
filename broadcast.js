const http = require("http");
const sockets = new Map();

//ffmpeg -err_detect ignore_err -i rtmp://localhost/live/tv -c:v copy -c:a copy -f mpegts - | node broadcast.js
process.stdin.on('data', (data) => {
  for (let res of sockets.values()) {
      // console.log('wrote %s bytes to %s sockets', data.length, sockets.size);
      res.write(data);
  }
});
process.stdin.on('end', () => {
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
