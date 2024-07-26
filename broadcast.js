const http = require("http");
const sockets = new Map();

process.stdin.on('data', (data) => {
  for (let res of sockets.values()) {
      // console.log('wrote %s bytes to %s sockets', data.length, sockets.size);
      res.write(data);
  }
});
process.stdin.on('close', () => {
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
const port = process.argv[2] || 8081;
server.listen(port, host, () => {
    console.log(`Server is running on http://${host}:${port}`);
});
