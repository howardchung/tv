const http = require("http");

const sockets = new Map();

process.stdin.on("data", (data) => {
  for (let res of sockets.values()) {
    // console.error('wrote %s bytes to %s sockets', data.length, sockets.size);
    // Each write() goes out as one HTTP/1.1 chunk: <hex length>\r\n<data>\r\n
    res.write(data);
  }
  // Pass through stdin so pipeline can continue
  process.stdout.write(data);
});

process.stdin.on("close", () => {
  process.exit(0);
});

const server = http.createServer((req, res) => {
  res.setHeader("Access-Control-Allow-Origin", "*");
  if (req.method === "HEAD") {
    return res.end();
  }
  // No Content-Length (the stream is unbounded), so use chunked transfer
  // encoding. HTTP/1.0 clients can't do chunked; they get the raw stream
  // delimited by connection close instead.
  if (req.httpVersion === "1.1") {
    res.setHeader("Transfer-Encoding", "chunked");
  }
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("Connection", "keep-alive");
  res.writeHead(200);
  res.flushHeaders();

  const rand = Math.random();
  sockets.set(rand, res);
  req.once("close", () => {
    console.error("deleting socket %s", rand);
    sockets.delete(rand);
    res.end();
  });
});

const host = "0.0.0.0";
const port = process.argv[2] || 8081;
server.listen(port, host, () => {
  console.error(`Server is running on http://${host}:${port}`);
});
