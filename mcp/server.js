#!/usr/bin/env node
// A dependency-free MCP server over stdio (newline-delimited JSON-RPC 2.0).
// It exposes two example tools. For anything bigger, switch to the official
// SDK: npm install @modelcontextprotocol/sdk
"use strict";

const readline = require("readline");

const SERVER_INFO = { name: "starter-kit-tools", version: "0.1.0" };

const TOOLS = [
  {
    name: "current_time",
    description: "Return the current date and time, optionally in a given IANA time zone.",
    inputSchema: {
      type: "object",
      properties: {
        timeZone: { type: "string", description: "IANA time zone, e.g. Europe/Paris. Defaults to UTC." },
      },
    },
    run({ timeZone = "UTC" }) {
      const text = new Date().toLocaleString("en-US", { timeZone, dateStyle: "full", timeStyle: "long" });
      return `${text} (${timeZone})`;
    },
  },
  {
    name: "word_count",
    description: "Count the words, lines and characters in a piece of text.",
    inputSchema: {
      type: "object",
      properties: { text: { type: "string", description: "The text to measure." } },
      required: ["text"],
    },
    run({ text }) {
      const words = text.trim() ? text.trim().split(/\s+/).length : 0;
      const lines = text ? text.split("\n").length : 0;
      return JSON.stringify({ words, lines, characters: text.length });
    },
  },
];

function send(message) {
  process.stdout.write(JSON.stringify({ jsonrpc: "2.0", ...message }) + "\n");
}

function handle(request) {
  const { id, method, params = {} } = request;
  switch (method) {
    case "initialize":
      return {
        protocolVersion: params.protocolVersion || "2025-06-18",
        capabilities: { tools: {} },
        serverInfo: SERVER_INFO,
      };
    case "ping":
      return {};
    case "tools/list":
      return { tools: TOOLS.map(({ run, ...tool }) => tool) };
    case "tools/call": {
      const tool = TOOLS.find((t) => t.name === params.name);
      if (!tool) throw { code: -32602, message: `Unknown tool: ${params.name}` };
      try {
        return { content: [{ type: "text", text: tool.run(params.arguments || {}) }] };
      } catch (err) {
        return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
      }
    }
    default:
      if (id === undefined) return undefined; // Notifications need no reply.
      throw { code: -32601, message: `Method not found: ${method}` };
  }
}

readline.createInterface({ input: process.stdin }).on("line", (line) => {
  if (!line.trim()) return;
  let request;
  try {
    request = JSON.parse(line);
  } catch {
    return send({ id: null, error: { code: -32700, message: "Parse error" } });
  }
  try {
    const result = handle(request);
    if (request.id !== undefined && result !== undefined) send({ id: request.id, result });
  } catch (err) {
    if (request.id !== undefined) send({ id: request.id, error: { code: err.code || -32603, message: err.message || String(err) } });
  }
});
