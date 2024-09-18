const http = require("http");

const server = http.createServer((req, res) => {
  req.pipe(process.stdout);
});
const host = '0.0.0.0';
const port = process.argv[2] || 5000;
server.listen(port, host, () => {
    console.error(`Server is running on http://${host}:${port}`);
});
