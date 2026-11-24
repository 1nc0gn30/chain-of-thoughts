#!/usr/bin/env node
/**
 * Chain of Thoughts (zoth-cot) — HTTP Server & REST API (:8145)
 * Cryptographic Merkle Working Memory DAG, Automatic Fact & Entity Extraction & Braille DAG Studio
 * Engineered by 1nc0gn30 (@1nc0gn30) • NullAI Platform
 */
'use strict';

const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const PORT = Number(process.env.PORT || 8145);
const PUBLIC_DIR = path.resolve(__dirname, 'public');
const DATA_DIR = path.resolve(__dirname, 'data');
const STATE_FILE = process.env.ZOTH_COT_DATA_FILE
  ? path.resolve(process.env.ZOTH_COT_DATA_FILE)
  : path.join(DATA_DIR, 'cot_memory.json');
const MAX_BODY_BYTES = 1024 * 1024; // 1 MB
const VALID_ROLES = new Set(['user', 'assistant', 'system']);

if (!fs.existsSync(path.dirname(STATE_FILE))) {
  fs.mkdirSync(path.dirname(STATE_FILE), { recursive: true });
}

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.mp4': 'video/mp4',
  '.webm': 'video/webm',
  '.wav': 'audio/wav',
  '.glb': 'model/gltf-binary',
  '.woff2': 'font/woff2',
  '.txt': 'text/plain; charset=utf-8',
  '.xml': 'application/xml; charset=utf-8'
};

const KNOWN_TOOLS = [
  'nmap', 'wireshark', 'metasploit', 'burpsuite', 'sqlmap', 'nikto', 'hydra',
  'john', 'aircrack-ng', 'ghidra', 'radare2', 'gitleaks', 'ollama', 'neovim',
  'tmux', 'ripgrep', 'curl', 'wget', 'docker', 'git', 'python3', 'tcpdump',
  'ffuf', 'gobuster', 'hashcat', 'socat', 'netcat', 'tshark', 'masscan',
  'rustc', 'cargo', 'zoth-envguard', 'zoth-ghostbyte', 'zoth-hexstrike',
  'zoth-cot', 'zoth-comm', 'zoth-capsule-jail', 'zoth-node-lite', 'zoth-braille-art'
];

function computeNodeHash(prevHash, thought, phase, timestamp, branch = 'main', version = 2) {
  const payload = version >= 2
    ? `v2|${prevHash}|${branch}|${phase}|${thought}|${timestamp}`
    : `${prevHash}|${thought}|${phase}|${timestamp}`;
  return crypto.createHash('sha256').update(payload, 'utf8').digest('hex').slice(0, 12);
}

function parseNodeIndex(id) {
  const m = /^N(\d+)$/i.exec(String(id || ''));
  return m ? Number(m[1]) : -1;
}

function createGenesisState() {
  const genesisHash = crypto.createHash('sha256').update('ZOTH-COT-GENESIS').digest('hex').slice(0, 12);
  const now = new Date().toISOString();
  const facts = [
    { id: 'fact-operator', category: 'IDENTITY', fact: 'Operator callsign: 1nc0gn30 (@1nc0gn30) • Sovereign AI Workstation.', active: true, ts: now },
    { id: 'fact-engine', category: 'ARCHITECTURE', fact: 'Chain of Thoughts (zoth-cot) Merkle DAG Working Memory Engine.', active: true, ts: now }
  ];
  return {
    headHash: genesisHash,
    head_hash: genesisHash,
    activeBranch: 'main',
    active_branch: 'main',
    branches: { main: genesisHash },
    nextNodeIndex: 1,
    next_node_index: 1,
    maxTurns: 24,
    max_turns: 24,
    pinnedFacts: facts,
    pinned_facts: facts,
    messages: [],
    turns: [],
    nodes: [
      {
        id: 'N00',
        hash: genesisHash,
        parent_hash: '000000000000',
        parentHash: '000000000000',
        branch: 'main',
        thought: '[GENESIS] Initialize Chain of Thoughts Working Memory DAG',
        prompt: '[GENESIS] Initialize Chain of Thoughts Working Memory DAG',
        phase: 'GENESIS',
        tags: ['genesis'],
        confidence: 1.0,
        steps: {
          recall: 'Loaded core semantic engrams into vault.',
          context_link: 'Initialized 24-turn rolling context window.',
          contextLink: 'Initialized 24-turn rolling context window.',
          deduction: 'Armed multi-turn LLM router (Ollama + Cloud Providers).',
          synthesis: 'Chain of Thoughts Merkle DAG online.'
        },
        mood: 'TACTICAL',
        tokens: 64,
        hash_version: 0,
        timestamp: now
      }
    ],
    entities: { ips: [], ports: [], domains: [], paths: [], cves: [], tools: [] },
    checkpoints: [],
    last_checkpoint: null
  };
}

function normalizeState(raw) {
  const base = createGenesisState();
  if (!raw || typeof raw !== 'object') return base;

  const headHash = raw.headHash || raw.head_hash || base.headHash;
  const activeBranch = raw.activeBranch || raw.active_branch || 'main';
  const maxTurns = Number(raw.maxTurns || raw.max_turns || 24);
  const pinnedFacts = Array.isArray(raw.pinnedFacts)
    ? raw.pinnedFacts
    : (Array.isArray(raw.pinned_facts) ? raw.pinned_facts : base.pinnedFacts);
  const messages = Array.isArray(raw.messages)
    ? raw.messages
    : (Array.isArray(raw.turns) ? raw.turns : []);

  let maxIdx = 0;
  const rawNodes = Array.isArray(raw.nodes) && raw.nodes.length > 0 ? raw.nodes : base.nodes;
  const nodes = rawNodes.map((n) => {
    const node = Object.assign({}, n);
    if (node.parentHash && !node.parent_hash) node.parent_hash = node.parentHash;
    if (node.parent_hash && !node.parentHash) node.parentHash = node.parent_hash;
    if (node.prompt && !node.thought) node.thought = node.prompt;
    if (node.thought && !node.prompt) node.prompt = node.thought;
    if (!node.phase) node.phase = node.mood || 'REASONING';
    if (!node.branch) node.branch = 'main';
    if (!Array.isArray(node.tags)) node.tags = [];
    const idx = parseNodeIndex(node.id);
    if (idx > maxIdx) maxIdx = idx;
    return node;
  });

  const nextNodeIndex = Math.max(Number(raw.nextNodeIndex || raw.next_node_index || 0), maxIdx + 1, nodes.length);
  let branches = {};
  if (raw.branches && typeof raw.branches === 'object' && Object.keys(raw.branches).length > 0) {
    branches = Object.assign({}, raw.branches);
  } else {
    nodes.forEach((n) => { branches[n.branch || 'main'] = n.hash; });
  }
  if (!branches[activeBranch]) branches[activeBranch] = headHash;

  const entities = { ips: [], ports: [], domains: [], paths: [], cves: [], tools: [] };
  if (raw.entities && typeof raw.entities === 'object') {
    for (const k of Object.keys(entities)) {
      if (Array.isArray(raw.entities[k])) {
        entities[k] = Array.from(new Set(raw.entities[k].map(String))).sort();
      }
    }
  }

  const checkpoints = Array.isArray(raw.checkpoints) ? raw.checkpoints : [];
  return {
    headHash,
    head_hash: headHash,
    activeBranch,
    active_branch: activeBranch,
    branches,
    nextNodeIndex,
    next_node_index: nextNodeIndex,
    maxTurns,
    max_turns: maxTurns,
    pinnedFacts,
    pinned_facts: pinnedFacts,
    messages,
    turns: messages,
    nodes,
    entities,
    checkpoints,
    last_checkpoint: checkpoints.length ? checkpoints[checkpoints.length - 1] : null
  };
}

let memoryState = createGenesisState();
let lastLoadedMtime = 0;

function syncStateFromDisk() {
  if (!fs.existsSync(STATE_FILE)) return memoryState;
  try {
    const stat = fs.statSync(STATE_FILE);
    if (stat.mtimeMs !== lastLoadedMtime) {
      const parsed = JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'));
      memoryState = normalizeState(parsed);
      lastLoadedMtime = stat.mtimeMs;
    }
  } catch (_e) {}
  return memoryState;
}

function saveState(state) {
  const dir = path.dirname(STATE_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  const payload = Object.assign({}, state, {
    headHash: state.headHash,
    head_hash: state.headHash,
    activeBranch: state.activeBranch,
    active_branch: state.activeBranch,
    nextNodeIndex: state.nextNodeIndex,
    next_node_index: state.nextNodeIndex,
    pinnedFacts: state.pinnedFacts,
    pinned_facts: state.pinnedFacts,
    messages: state.messages,
    turns: state.messages,
    updated_at: new Date().toISOString()
  });
  const tmpFile = `${STATE_FILE}.tmp.${process.pid}`;
  fs.writeFileSync(tmpFile, JSON.stringify(payload, null, 2), 'utf8');
  fs.renameSync(tmpFile, STATE_FILE);
  try {
    lastLoadedMtime = fs.statSync(STATE_FILE).mtimeMs;
  } catch (_e) {}
}

syncStateFromDisk();

function findNode(state, ref) {
  const needle = String(ref || '').trim().toLowerCase();
  if (!needle) return null;
  for (const n of state.nodes) {
    if (String(n.id || '').toLowerCase() === needle || String(n.hash || '').toLowerCase() === needle) return n;
  }
  const matches = state.nodes.filter((n) => String(n.hash || '').toLowerCase().startsWith(needle));
  return matches.length === 1 ? matches[0] : null;
}

function extractEntities(state, text) {
  const p = String(text || '');
  const found = { ips: new Set(), ports: new Set(), domains: new Set(), paths: new Set(), cves: new Set(), tools: new Set() };
  if (!p.trim()) return { ips: [], ports: [], domains: [], paths: [], cves: [], tools: [] };

  for (const m of p.matchAll(/\b(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\b/g)) found.ips.add(m[0]);
  for (const m of p.matchAll(/(?::|(?:\b(?:port|ports|tcp|udp)\s*[:=/]?\s*))(\d{1,5})\b/gi)) {
    const v = Number(m[1]);
    if (v >= 1 && v <= 65535) found.ports.add(String(v));
  }
  for (const m of p.matchAll(/\bCVE-\d{4}-\d{4,7}\b/gi)) found.cves.add(m[0].toUpperCase());
  const noUrls = p.replace(/[a-zA-Z][a-zA-Z0-9+.-]*:\/\/[^\s"'<>]+/g, ' ');
  for (const m of noUrls.matchAll(/(?:(?<![a-zA-Z0-9_./])\/(?:[a-zA-Z0-9_\-.]+\/)+[a-zA-Z0-9_\-.]+|(?:\.\/|\.\.\/)[a-zA-Z0-9_\-./]+)/g)) {
    const c = m[0].replace(/[.,:;!?)"'>]+$/, '');
    if (!c.startsWith('//') && c.length > 2) found.paths.add(c);
  }
  for (const m of p.matchAll(/\b(?!(?:\d{1,3}\.){3}\d{1,3})(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:com|org|net|edu|gov|io|tech|pro|ai|dev|app|co|xyz|me|info|biz|cloud|network|site|mil)\b/gi)) {
    found.domains.add(m[0].toLowerCase());
  }
  const lower = p.toLowerCase();
  for (const tool of KNOWN_TOOLS) {
    const esc = tool.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    if (new RegExp(`\\b${esc}\\b`).test(lower)) found.tools.add(tool);
  }
  const out = {};
  for (const k of Object.keys(found)) {
    const arr = Array.from(found[k]).sort();
    out[k] = arr;
    state.entities[k] = Array.from(new Set([...(state.entities[k] || []), ...arr])).sort();
  }
  return out;
}

function verifyChain(state) {
  const issues = [];
  const hashMap = new Map();
  for (const n of state.nodes) {
    if (!n.hash) { issues.push(`Node ${n.id} missing hash`); continue; }
    if (hashMap.has(n.hash)) issues.push(`Duplicate hash: ${n.hash}`);
    hashMap.set(n.hash, n);
  }
  if (!state.nodes.length) {
    issues.push('Empty DAG');
  } else {
    const gp = state.nodes[0].parent_hash || state.nodes[0].parentHash;
    if (gp !== '000000000000') issues.push(`Genesis node parent mismatch: ${gp}`);
    for (let i = 1; i < state.nodes.length; i++) {
      const n = state.nodes[i];
      const p = n.parent_hash || n.parentHash;
      if (!p || !hashMap.has(p)) issues.push(`Broken parent link on ${n.id}: ${p}`);
      if (n.hash_version === 2) {
        const expected = computeNodeHash(p || '', n.thought || n.prompt || '', n.phase || 'REASONING', n.timestamp || '', n.branch || 'main', 2);
        if (expected !== n.hash) issues.push(`Hash tampering on ${n.id}: expected ${expected}, got ${n.hash}`);
      }
    }
  }
  if (!hashMap.has(state.headHash)) issues.push(`headHash ${state.headHash} missing from DAG`);
  return { valid: issues.length === 0, checked_nodes: state.nodes.length, branch_count: Object.keys(state.branches).length, head_hash: state.headHash, issues };
}

function getStats(state) {
  const phases = {};
  const branches = {};
  const tags = {};
  const confs = [];
  for (const n of state.nodes) {
    const ph = String(n.phase || 'REASONING').toUpperCase();
    phases[ph] = (phases[ph] || 0) + 1;
    const br = String(n.branch || 'main');
    branches[br] = (branches[br] || 0) + 1;
    (n.tags || []).forEach((t) => { tags[t] = (tags[t] || 0) + 1; });
    if (typeof n.confidence === 'number') confs.push(n.confidence);
  }
  const activeFacts = state.pinnedFacts.filter((f) => f.active !== false);
  const entCounts = {};
  let entTotal = 0;
  for (const [k, arr] of Object.entries(state.entities)) {
    entCounts[k] = arr.length;
    entTotal += arr.length;
  }
  return {
    head_hash: state.headHash,
    active_branch: state.activeBranch,
    node_count: state.nodes.length,
    branch_count: Object.keys(state.branches).length,
    message_count: state.messages.length,
    turn_count: Math.floor(state.messages.length / 2),
    checkpoint_count: state.checkpoints.length,
    facts: { total: state.pinnedFacts.length, active: activeFacts.length, inactive: state.pinnedFacts.length - activeFacts.length },
    entities: entCounts,
    entities_total: entTotal,
    phases,
    branches,
    tags,
    avg_confidence: confs.length ? Number((confs.reduce((a, b) => a + b, 0) / confs.length).toFixed(4)) : null,
    merkle_valid: verifyChain(state).valid
  };
}

function exportMarkdown(state) {
  const v = verifyChain(state);
  const lines = [
    `# Chain of Thoughts Trace (\`${state.headHash}\`)`,
    '',
    `- **Active Branch**: \`${state.activeBranch}\``,
    `- **Nodes**: ${state.nodes.length} | **Branches**: ${Object.keys(state.branches).length} | **Turns**: ${Math.floor(state.messages.length / 2)}`,
    `- **Merkle Integrity**: ${v.valid ? 'VALID' : 'INVALID'}`,
    '',
    '## Pinned Facts',
    ...(state.pinnedFacts.length
      ? state.pinnedFacts.map((f) => `- \`[${f.category}]\` (${f.active !== false ? 'active' : 'inactive'}, \`${f.id}\`): ${f.fact}`)
      : ['- None']),
    '',
    '## Reasoning DAG',
    ...state.nodes.map((n) => `- **${n.id}** (\`${n.hash}\`) [branch=\`${n.branch || 'main'}\`, phase=\`${n.phase || 'REASONING'}\`, parent=\`${n.parent_hash || n.parentHash}\`]: ${n.thought || n.prompt || ''}`)
  ];
  return lines.join('\n') + '\n';
}

function sendJson(res, statusCode, data) {
  res.writeHead(statusCode, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  });
  res.end(JSON.stringify(data));
}

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    let size = 0;
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY_BYTES) {
        reject(Object.assign(new Error('Payload too large'), { statusCode: 413 }));
        req.destroy();
        return;
      }
      body += chunk;
    });
    req.on('end', () => {
      try {
        resolve(JSON.parse(body || '{}'));
      } catch (_e) {
        reject(Object.assign(new Error('Invalid JSON payload'), { statusCode: 400 }));
      }
    });
    req.on('error', reject);
  });
}

function serveStatic(req, res, filePath) {
  const resolved = path.resolve(filePath);
  if (!resolved.startsWith(PUBLIC_DIR)) {
    res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('403 Forbidden');
    return;
  }

  fs.stat(resolved, (err, stats) => {
    if (err || !stats.isFile()) {
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

    const ext = path.extname(resolved).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';
    res.writeHead(200, {
      'Content-Type': contentType,
      'X-Frame-Options': 'SAMEORIGIN',
      'X-Content-Type-Options': 'nosniff',
      'Referrer-Policy': 'strict-origin-when-cross-origin'
    });
    fs.createReadStream(resolved).pipe(res);
  });
}

const server = http.createServer(async (req, res) => {
  const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const pathname = parsedUrl.pathname;

  if (req.method === 'OPTIONS') {
    res.writeHead(204, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type'
    });
    res.end();
    return;
  }

  const state = syncStateFromDisk();

  // Health endpoints
  if ((pathname === '/health' || pathname === '/api/health') && req.method === 'GET') {
    sendJson(res, 200, {
      ok: true,
      status: 'ONLINE',
      engine: 'Chain of Thoughts (zoth-cot)',
      version: '1.1.0',
      nodes: state.nodes.length,
      branches: Object.keys(state.branches).length,
      activeBranch: state.activeBranch,
      headHash: state.headHash,
      timestamp: new Date().toISOString()
    });
    return;
  }

  if (pathname === '/api/state' && req.method === 'GET') {
    sendJson(res, 200, state);
    return;
  }

  if (pathname === '/api/stats' && req.method === 'GET') {
    sendJson(res, 200, getStats(state));
    return;
  }

  if (pathname === '/api/verify' && req.method === 'GET') {
    sendJson(res, 200, verifyChain(state));
    return;
  }

  if (pathname === '/api/export' && req.method === 'GET') {
    const fmt = (parsedUrl.searchParams.get('format') || 'json').toLowerCase();
    if (fmt === 'markdown' || fmt === 'md') {
      const md = exportMarkdown(state);
      res.writeHead(200, {
        'Content-Type': 'text/markdown; charset=utf-8',
        'Access-Control-Allow-Origin': '*'
      });
      res.end(md);
      return;
    }
    sendJson(res, 200, {
      head_hash: state.headHash,
      active_branch: state.activeBranch,
      branches: state.branches,
      verification: verifyChain(state),
      stats: getStats(state),
      pinned_facts: state.pinnedFacts,
      entities: state.entities,
      nodes: state.nodes,
      messages: state.messages
    });
    return;
  }

  if (pathname === '/api/search' && req.method === 'GET') {
    const q = (parsedUrl.searchParams.get('q') || '').trim().toLowerCase();
    const phase = (parsedUrl.searchParams.get('phase') || '').trim().toUpperCase() || null;
    const branch = (parsedUrl.searchParams.get('branch') || '').trim() || null;
    const tag = (parsedUrl.searchParams.get('tag') || '').trim().toLowerCase() || null;
    const minConfParam = parsedUrl.searchParams.get('min_confidence');
    const minConf = minConfParam !== null && minConfParam !== '' ? Number(minConfParam) : null;

    const textMatch = (txt) => !q || String(txt || '').toLowerCase().includes(q);
    const matchedThoughts = state.nodes.filter((n) => {
      if (phase && String(n.phase || '').toUpperCase() !== phase) return false;
      if (branch && (n.branch || 'main') !== branch) return false;
      if (tag && !(n.tags || []).includes(tag)) return false;
      if (minConf !== null && (typeof n.confidence !== 'number' || n.confidence < minConf)) return false;
      return textMatch(`${n.thought || n.prompt} ${n.phase} ${n.branch} ${(n.tags || []).join(' ')}`);
    });
    const matchedFacts = (!phase && !branch && !tag && minConf === null)
      ? state.pinnedFacts.filter((f) => textMatch(`${f.fact} ${f.category}`))
      : [];
    const matchedTurns = (!phase && !tag && minConf === null)
      ? state.messages.filter((m) => (!branch || (m.branch || 'main') === branch) && textMatch(`${m.content} ${m.role}`))
      : [];

    sendJson(res, 200, {
      query: q,
      matched_facts: matchedFacts,
      matched_turns: matchedTurns,
      matched_thoughts: matchedThoughts,
      total_matches: matchedFacts.length + matchedTurns.length + matchedThoughts.length
    });
    return;
  }

  if (pathname === '/api/pin' && req.method === 'POST') {
    try {
      const payload = await readJsonBody(req);
      const fact = String(payload.fact || '').trim();
      const category = String(payload.category || 'PINNED').trim().toUpperCase();
      if (!fact) { sendJson(res, 400, { error: 'Fact content is required' }); return; }
      const newFact = {
        id: 'fact-' + Date.now().toString(36) + '-' + crypto.randomBytes(2).toString('hex'),
        category,
        fact,
        active: true,
        ts: new Date().toISOString()
      };
      state.pinnedFacts.unshift(newFact);
      saveState(state);
      sendJson(res, 200, { success: true, fact: newFact });
    } catch (e) {
      sendJson(res, e.statusCode || 400, { error: e.message });
    }
    return;
  }

  if (pathname === '/api/unpin' && req.method === 'POST') {
    try {
      const payload = await readJsonBody(req);
      const factId = String(payload.fact_id || payload.id || '').trim();
      const del = Boolean(payload.delete);
      const idx = state.pinnedFacts.findIndex((f) => f.id === factId);
      if (idx === -1) { sendJson(res, 404, { error: `Fact '${factId}' not found` }); return; }
      if (del) {
        const [removed] = state.pinnedFacts.splice(idx, 1);
        saveState(state);
        sendJson(res, 200, { success: true, action: 'deleted', fact: removed });
      } else {
        state.pinnedFacts[idx].active = false;
        saveState(state);
        sendJson(res, 200, { success: true, action: 'deactivated', fact: state.pinnedFacts[idx] });
      }
    } catch (e) {
      sendJson(res, e.statusCode || 400, { error: e.message });
    }
    return;
  }

  if (pathname === '/api/turn' && req.method === 'POST') {
    try {
      const payload = await readJsonBody(req);
      const role = String(payload.role || 'user').trim().toLowerCase();
      const content = String(payload.content || '').trim();
      if (!VALID_ROLES.has(role)) { sendJson(res, 400, { error: `Invalid role '${role}'` }); return; }
      if (!content) { sendJson(res, 400, { error: 'Turn content is required' }); return; }
      const entities = extractEntities(state, content);
      const msg = {
        id: `msg-${state.messages.length + 1}`,
        role,
        content,
        timestamp: new Date().toISOString(),
        node_hash: state.headHash,
        branch: state.activeBranch
      };
      state.messages.push(msg);
      if (state.messages.length > state.maxTurns * 2) {
        state.messages = state.messages.slice(-(state.maxTurns * 2));
      }
      saveState(state);
      sendJson(res, 200, { success: true, turn: msg, extracted_entities: entities, head_hash: state.headHash });
    } catch (e) {
      sendJson(res, e.statusCode || 400, { error: e.message });
    }
    return;
  }

  if (pathname === '/api/step' && req.method === 'POST') {
    try {
      const payload = await readJsonBody(req);
      const thought = String(payload.thought || payload.prompt || '').trim();
      const phase = String(payload.phase || 'REASONING').trim().toUpperCase();
      const branch = String(payload.branch || state.activeBranch || 'main').trim() || 'main';
      if (!thought) { sendJson(res, 400, { error: 'Thought content is required' }); return; }

      let conf = null;
      if (payload.confidence !== undefined && payload.confidence !== null) {
        conf = Number(payload.confidence);
        if (Number.isNaN(conf) || conf < 0 || conf > 1) {
          sendJson(res, 400, { error: 'Confidence must be between 0.0 and 1.0' });
          return;
        }
      }

      let prevHash;
      if (payload.parent_hash || payload.parentHash) {
        const pnode = findNode(state, payload.parent_hash || payload.parentHash);
        if (!pnode) { sendJson(res, 404, { error: 'Parent node not found' }); return; }
        prevHash = pnode.hash;
      } else if (state.branches[branch]) {
        prevHash = state.branches[branch];
      } else {
        prevHash = state.headHash;
      }

      const idx = state.nextNodeIndex++;
      const nodeId = `N${idx < 10 ? '0' + idx : idx}`;
      const ts = new Date().toISOString();
      const hash = computeNodeHash(prevHash, thought, phase, ts, branch, 2);
      const tags = Array.isArray(payload.tags)
        ? Array.from(new Set(payload.tags.map((t) => String(t).trim().toLowerCase()).filter(Boolean)))
        : [];

      const newNode = {
        id: nodeId,
        hash,
        parent_hash: prevHash,
        parentHash: prevHash,
        branch,
        thought,
        prompt: thought,
        phase,
        mood: String(payload.mood || 'TACTICAL').toUpperCase(),
        tags,
        confidence: conf,
        steps: {
          recall: `Linked to prior head ${prevHash} on branch '${branch}'.`,
          context_link: `Phase ${phase} step.`,
          contextLink: `Phase ${phase} step.`,
          deduction: thought.slice(0, 60),
          synthesis: thought
        },
        tokens: Math.max(32, Math.round(thought.length / 3.8)),
        hash_version: 2,
        timestamp: ts
      };
      state.nodes.push(newNode);
      state.headHash = hash;
      state.activeBranch = branch;
      state.branches[branch] = hash;
      saveState(state);
      sendJson(res, 200, { success: true, node: newNode });
    } catch (e) {
      sendJson(res, e.statusCode || 400, { error: e.message });
    }
    return;
  }

  if (pathname === '/api/clear' && req.method === 'POST') {
    state.messages = [];
    state.turns = [];
    saveState(state);
    sendJson(res, 200, { success: true, message: 'Cleared conversation turns.' });
    return;
  }

  // Serve static files from public
  let safePath = path.normalize(pathname).replace(/^(\.\.[/\\])+/, '');
  if (safePath === '/' || safePath === '') safePath = '/index.html';
  const filePath = path.join(PUBLIC_DIR, safePath);
  serveStatic(req, res, filePath);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`◈ Chain of Thoughts (zoth-cot) Studio listening on http://localhost:${PORT}`);
});
