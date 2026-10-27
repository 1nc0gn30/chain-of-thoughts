#!/usr/bin/env node
/**
 * Chain of Thoughts (zoth-cot) — HTTP Server & API (:8145)
 * Cryptographic Merkle Working Memory DAG, Automatic Fact Extraction & Braille DAG Studio
 * Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const PORT = Number(process.env.PORT || 8145);
const PUBLIC_DIR = path.join(__dirname, 'public');
const DATA_DIR = path.join(__dirname, 'data');
const STATE_FILE = path.join(DATA_DIR, 'cot_memory.json');

if (!fs.existsSync(DATA_DIR)) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.txt': 'text/plain; charset=utf-8',
  '.xml': 'application/xml; charset=utf-8'
};

function loadState() {
  if (fs.existsSync(STATE_FILE)) {
    try {
      return JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
    } catch (_e) {}
  }
  const genesisHash = crypto.createHash('sha256').update('ZOTH-COT-GENESIS').digest('hex').slice(0, 12);
  return {
    headHash: genesisHash,
    maxTurns: 24,
    pinnedFacts: [
      { id: 'fact-1', category: 'IDENTITY', fact: 'Operator callsign: Neal (@1nc0gn30) • Sovereign AI Workstation.', active: true, ts: new Date().toISOString() },
      { id: 'fact-2', category: 'ARCHITECTURE', fact: 'Chain of Thoughts (zoth-cot) Merkle DAG Working Memory Engine.', active: true, ts: new Date().toISOString() },
      { id: 'fact-3', category: 'SECURITY', fact: 'Strict zero-leak pre-commit rule: EnvGuard active on all repositories.', active: true, ts: new Date().toISOString() },
      { id: 'fact-4', category: 'INFRASTRUCTURE', fact: 'Dual checkout rails enabled: Stripe Buy Us a Coffee + Solana Tip Wallet.', active: true, ts: new Date().toISOString() }
    ],
    turns: [],
    nodes: [
      {
        id: 'N00',
        hash: genesisHash,
        parentHash: '000000000000',
        prompt: '[GENESIS] Initialize Chain of Thoughts Working Memory DAG',
        steps: {
          recall: 'Loaded core semantic engrams into vault.',
          contextLink: 'Initialized 24-turn rolling context window.',
          deduction: 'Armed multi-turn LLM router (Ollama + Cloud Providers).',
          synthesis: 'Chain of Thoughts Merkle DAG online.'
        },
        mood: 'TACTICAL',
        tokens: 64,
        timestamp: new Date().toISOString()
      }
    ],
    entities: {}
  };
}

function saveState(state) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2), 'utf8');
}

let memoryState = loadState();

function sendJson(res, statusCode, data) {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  });
  res.end(JSON.stringify(data));
}

function serveStatic(req, res, filePath) {
  fs.stat(filePath, (err, stats) => {
    if (err || !stats.isFile()) {
      // SPA Fallback
      const indexPath = path.join(PUBLIC_DIR, 'index.html');
      fs.readFile(indexPath, (readErr, content) => {
        if (readErr) {
          res.writeHead(404, { 'Content-Type': 'text/plain' });
          res.end('404 Not Found');
          return;
        }
        res.writeHead(200, {
          'Content-Type': 'text/html; charset=utf-8',
          'X-Frame-Options': 'SAMEORIGIN',
          'X-Content-Type-Options': 'nosniff',
          'Referrer-Policy': 'strict-origin-when-cross-origin'
        });
        res.end(content);
      });
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    res.writeHead(200, {
      'Content-Type': contentType,
      'X-Frame-Options': 'SAMEORIGIN',
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'strict-origin-when-cross-origin'
    });
    fs.createReadStream(filePath).pipe(res);
  });
}

const server = http.createServer((req, res) => {
  const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const pathname = parsedUrl.pathname;

  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    });
    res.end();
    return;
  }

  // API Endpoints
  if (pathname === '/api/health') {
    sendJson(res, 200, {
      status: 'ONLINE',
      engine: 'Chain of Thoughts (zoth-cot)',
      nodes: memoryState.nodes.length,
      headHash: memoryState.headHash,
      timestamp: new Date().toISOString()
    });
    return;
  }

  if (pathname === '/api/state' && req.method === 'GET') {
    sendJson(res, 200, memoryState);
    return;
  }

  if (pathname === '/api/pin' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const payload = JSON.parse(body || '{}');
        const fact = (payload.fact || '').trim();
        const category = (payload.category || 'PINNED').toUpperCase();
        if (!fact) {
          sendJson(res, 400, { error: 'Fact content is required' });
          return;
        }
        const newFact = {
          id: 'fact-' + Date.now().toString(36),
          category: category,
          fact: fact,
          active: true,
          ts: new Date().toISOString()
        };
        memoryState.pinnedFacts.unshift(newFact);
        saveState(memoryState);
        sendJson(res, 200, { success: true, fact: newFact });
      } catch (e) {
        sendJson(res, 400, { error: 'Invalid JSON payload' });
      }
    });
    return;
  }

  if (pathname === '/api/clear' && req.method === 'POST') {
    memoryState.turns = [];
    saveState(memoryState);
    sendJson(res, 200, { success: true, message: 'Cleared conversation turns.' });
    return;
  }

  // Serve static files from public
  let safePath = path.normalize(pathname).replace(/^(\.\.[\/\\])+/, '');
  if (safePath === '/' || safePath === '') safePath = '/index.html';
  const filePath = path.join(PUBLIC_DIR, safePath);
  serveStatic(req, res, filePath);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`◈ Chain of Thoughts (zoth-cot) Studio listening on http://localhost:${PORT}`);
});
