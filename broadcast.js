const http = require("http");
const sockets = new Map();

process.stdin.on('data', (data) => {
  for (let res of sockets.values()) {
      // console.error('wrote %s bytes to %s sockets', data.length, sockets.size);
      res.write(data);
  }
  // Pass through stdin so pipeline can continue
  process.stdout.write(data);
});
process.stdin.on('close', () => {
  process.exit(0);
});

const server = http.createServer((req, res) => {
    // nginx sets headers
    // res.setHeader('Access-Control-Allow-Origin', '*');
    if (req.method === "HEAD") {
      return res.end();
    }
    const rand = Math.random();
    sockets.set(rand, res);
    req.once('close', () => {
      console.error('deleting socket %s', rand);
      sockets.delete(rand);
      res.end();
    });
});
const host = '0.0.0.0';
const port = process.argv[2] || 8081;
server.listen(port, host, () => {
    console.error(`Server is running on http://${host}:${port}`);
});
