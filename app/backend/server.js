const express = require("express");

const app = express();
const PORT = process.env.PORT || 3000;
const API_KEY = process.env.API_KEY;

app.use(express.json());

// JSON logs stdout pe
function log(level, message, extra = {}) {
  console.log(JSON.stringify({ time: new Date().toISOString(), level, message, ...extra }));
}

// Har request ka log
app.use((req, res, next) => {
  const start = Date.now();
  res.on("finish", () => {
    log("info", "request", { method: req.method, path: req.path, status: res.statusCode, ms: Date.now() - start });
  });
  next();
});

// API key check
function requireApiKey(req, res, next) {
  if (!API_KEY || req.get("x-api-key") !== API_KEY) {
    return res.status(401).json({ error: "unauthorized" });
  }
  next();
}

// Health check
app.get("/health", (req, res) => {
  res.json({ status: "ok", uptime: Math.round(process.uptime()) });
});

// App data
const items = [
  { id: 1, name: "Server monitoring" },
  { id: 2, name: "Log analysis" },
  { id: 3, name: "Auto restart" },
];
app.get("/api/items", (req, res) => res.json(items));

// Demo: CPU busy karo
app.post("/api/stress", requireApiKey, (req, res) => {
  const seconds = Math.min(Number(req.body.seconds) || 10, 60);
  log("warn", "cpu stress started", { seconds });
  res.json({ message: `CPU stress for ${seconds}s` });
  setImmediate(() => {
    const end = Date.now() + seconds * 1000;
    while (Date.now() < end) {}
  });
});

// Demo: app crash karo
app.post("/api/crash", requireApiKey, (req, res) => {
  log("error", "crash requested, exiting");
  res.json({ message: "crashing" });
  setTimeout(() => process.exit(1), 100);
});

const server = app.listen(PORT, () => log("info", "backend started", { port: PORT }));

// Graceful shutdown
process.on("SIGTERM", () => {
  log("info", "SIGTERM received, shutting down");
  server.close(() => process.exit(0));
});