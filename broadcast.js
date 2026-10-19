const http = require("http");
const crypto = require("crypto");

const GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";
const sockets = new Set();

// Build an unmasked server->client frame
function frame(opcode, payload) {
  const len = payload.length;
  let header;
  if (len < 126) {
    header = Buffer.from([0x80 | opcode, len]);
  } else if (len < 65536) {
    header = Buffer.alloc(4);
    header[0] = 0x80 | opcode;
    header[1] = 126;
    header.writeUInt16BE(len, 2);
  } else {
    header = Buffer.alloc(10);
    header[0] = 0x80 | opcode;
    header[1] = 127;
    header.writeBigUInt64BE(BigInt(len), 2);
  }
  return Buffer.concat([header, payload]);
}

process.stdin.on("data", (data) => {
  if (sockets.size) {
    const msg = frame(0x2, data); // binary frame, encoded once for all clients
    for (const socket of sockets) {
      socket.write(msg);
    }
  }
  // Pass through stdin so pipeline can continue
  process.stdout.write(data);
});

process.stdin.on("close", () => {
  process.exit(0);
});

const server = http.createServer((req, res) => {
  res.writeHead(426, { Upgrade: "websocket" });
  res.end("WebSocket connections only");
});

server.on("upgrade", (req, socket) => {
  const key = req.headers["sec-websocket-key"];
  if (
    !key ||
    (req.headers.upgrade || "").toLowerCase() !== "websocket"
  ) {
    socket.end("HTTP/1.1 400 Bad Request\r\n\r\n");
    return;
  }
  const accept = crypto
    .createHash("sha1")
    .update(key + GUID)
    .digest("base64");
  socket.write(
    "HTTP/1.1 101 Switching Protocols\r\n" +
      "Upgrade: websocket\r\n" +
      "Connection: Upgrade\r\n" +
      `Sec-WebSocket-Accept: ${accept}\r\n\r\n`
  );
  socket.setNoDelay(true);
  sockets.add(socket);
  console.error("client connected (%s total)", sockets.size);

  let buf = Buffer.alloc(0);
  socket.on("data", (chunk) => {
    buf = Buffer.concat([buf, chunk]);
    // Parse client frames; we only care about ping and close
    while (buf.length >= 2) {
      const opcode = buf[0] & 0x0f;
      const masked = (buf[1] & 0x80) !== 0;
      let len = buf[1] & 0x7f;
      let offset = 2;
      if (len === 126) {
        if (buf.length < 4) return;
        len = buf.readUInt16BE(2);
        offset = 4;
      } else if (len === 127) {
        if (buf.length < 10) return;
        len = Number(buf.readBigUInt64BE(2));
        offset = 10;
      }
      if (len > 1 << 20) return socket.destroy(); // clients shouldn't send much
      const total = offset + (masked ? 4 : 0) + len;
      if (buf.length < total) return;
      const payload = Buffer.from(
        buf.subarray(offset + (masked ? 4 : 0), total)
      );
      if (masked) {
        const mask = buf.subarray(offset, offset + 4);
        for (let i = 0; i < payload.length; i++) payload[i] ^= mask[i & 3];
      }
      buf = buf.subarray(total);

      if (opcode === 0x8) {
        // close: echo and end
        socket.end(frame(0x8, payload.subarray(0, 2)));
        return;
      } else if (opcode === 0x9) {
        socket.write(frame(0xa, payload)); // ping -> pong
      }
      // text/binary/pong from clients are ignored
    }
  });

  const cleanup = () => {
    if (sockets.delete(socket)) {
      console.error("client disconnected (%s total)", sockets.size);
    }
  };
  socket.on("close", cleanup);
  socket.on("error", () => socket.destroy());
});

const host = "0.0.0.0";
const port = Number(process.argv[2]) || 8081;
server.listen(port, host, () => {
  console.error(`WebSocket server is running on ws://${host}:${port}`);
});
