/**
 * 🚀 YouTube Automation Dashboard — Express Server
 * GOD MODE Control Center
 * 
 * Features:
 * - Real-time pipeline execution via SSE
 * - Script generation preview
 * - One-click video creation
 * - Output file browser
 */

const express = require('express');
const { spawn, execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.DASHBOARD_PORT || 3000;
const PROJECT_ROOT = path.resolve(__dirname, '..');

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// ── API: Generate Script ──
app.post('/api/generate-script', (req, res) => {
    const { topic, videoType } = req.body;
    
    let args = ['scripts/generate_script.py', '--type', videoType || 'short'];
    if (topic) args.push('--topic', topic);
    
    const proc = spawn('python', args, { 
        cwd: PROJECT_ROOT,
        env: { ...process.env, PYTHONUNBUFFERED: '1', PYTHONIOENCODING: 'utf-8' }
    });
    let output = '';
    let error = '';
    
    proc.stdout.on('data', d => output += d.toString());
    proc.stderr.on('data', d => error += d.toString());
    
    proc.on('close', code => {
        if (code === 0) {
            // Find the latest script file
            const scriptsDir = path.join(PROJECT_ROOT, 'output', 'scripts');
            try {
                const files = fs.readdirSync(scriptsDir)
                    .filter(f => f.endsWith('.json'))
                    .sort()
                    .reverse();
                
                if (files.length > 0) {
                    const data = JSON.parse(fs.readFileSync(path.join(scriptsDir, files[0]), 'utf-8'));
                    res.json({ success: true, script: data, file: files[0], log: output });
                } else {
                    res.json({ success: true, log: output });
                }
            } catch (e) {
                res.json({ success: true, log: output });
            }
        } else {
            res.json({ success: false, error: error || output });
        }
    });
});

// ── API: Generate Voice ──
app.post('/api/generate-voice', (req, res) => {
    const { scriptPath, voice, videoType } = req.body;
    
    if (!scriptPath) {
        return res.json({ success: false, error: 'No script path provided' });
    }
    
    let args = ['scripts/generate_voice.py', '--script', scriptPath, '--type', videoType || 'short'];
    if (voice) args.push('--voice', voice);
    
    const proc = spawn('python', args, { 
        cwd: PROJECT_ROOT,
        env: { ...process.env, PYTHONIOENCODING: 'utf-8', PYTHONUNBUFFERED: '1' }
    });
    let output = '';
    let error = '';
    
    proc.stdout.on('data', d => output += d.toString());
    proc.stderr.on('data', d => error += d.toString());
    
    proc.on('error', err => {
        res.json({ success: false, error: 'Failed to start Python: ' + err.message });
    });
    
    proc.on('close', code => {
        res.json({
            success: code === 0,
            log: output,
            error: code !== 0 ? (error || output) : undefined
        });
    });
});

// ── API: Run Full Pipeline (SSE) ──
app.get('/api/pipeline/run', (req, res) => {
    const videoType = req.query.type || 'short';
    const topic = req.query.topic || '';
    const dryRun = req.query.dryRun !== 'false'; // Default to dry-run for safety
    const batch = parseInt(req.query.batch) || 0;
    const voice = req.query.voice || '';
    
    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    });
    
    // Build args cleanly — no add-then-remove hack
    let args = ['pipeline.py', '--type', videoType];
    if (dryRun) args.push('--dry-run');
    if (topic) args.push('--topic', topic);
    if (voice) args.push('--voice', voice);
    if (batch > 0) args.push('--batch', String(batch));
    
    const proc = spawn('python', ['-u', ...args], { 
        cwd: PROJECT_ROOT,
        env: { ...process.env, PYTHONUNBUFFERED: '1', PYTHONIOENCODING: 'utf-8' }
    });
    
    proc.stdout.on('data', data => {
        const lines = data.toString().split('\n');
        lines.forEach(line => {
            if (line.trim()) {
                res.write(`data: ${JSON.stringify({ type: 'log', message: line })}\n\n`);
            }
        });
    });
    
    proc.stderr.on('data', data => {
        const msg = data.toString().trim();
        // Filter out Python warnings that aren't real errors
        if (msg && !msg.startsWith('WARNING') && !msg.includes('FutureWarning')) {
            res.write(`data: ${JSON.stringify({ type: 'error', message: msg })}\n\n`);
        }
    });
    
    proc.on('error', err => {
        res.write(`data: ${JSON.stringify({ type: 'error', message: 'Failed to start: ' + err.message })}\n\n`);
        res.write(`data: ${JSON.stringify({ type: 'done', code: 1 })}\n\n`);
        res.end();
    });
    
    proc.on('close', code => {
        res.write(`data: ${JSON.stringify({ type: 'done', code })}\n\n`);
        res.end();
    });
    
    req.on('close', () => {
        try { proc.kill(); } catch {}
    });
});

// ── API: List Output Files ──
app.get('/api/files', (req, res) => {
    const outputDir = path.join(PROJECT_ROOT, 'output');
    const result = { scripts: [], audio: [], videos: [], thumbnails: [] };
    
    const categories = ['scripts', 'audio', 'videos', 'thumbnails'];
    
    categories.forEach(cat => {
        const dir = path.join(outputDir, cat);
        try {
            if (fs.existsSync(dir)) {
                result[cat] = fs.readdirSync(dir)
                    .filter(f => !f.startsWith('.'))
                    .map(f => {
                        const stats = fs.statSync(path.join(dir, f));
                        return {
                            name: f,
                            size: (stats.size / 1024).toFixed(1) + ' KB',
                            created: stats.birthtime.toISOString()
                        };
                    })
                    .sort((a, b) => new Date(b.created) - new Date(a.created))
                    .slice(0, 20);
            }
        } catch (e) { /* ignore */ }
    });
    
    res.json(result);
});

// ── API: Read Script Content ──
app.get('/api/script/:filename', (req, res) => {
    const filePath = path.join(PROJECT_ROOT, 'output', 'scripts', req.params.filename);
    try {
        const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
        res.json(data);
    } catch (e) {
        res.status(404).json({ error: 'Script not found' });
    }
});

// ── API: System Status ──
app.get('/api/status', (req, res) => {
    const status = {
        node: process.version,
        platform: process.platform,
        ffmpeg: false,
        python: false,
        gemini_key: false
    };
    
    try { execSync('ffmpeg -version', { timeout: 5000 }); status.ffmpeg = true; } catch {}
    try { execSync('python --version', { timeout: 5000 }); status.python = true; } catch {}
    
    try {
        const envPath = path.join(PROJECT_ROOT, '.env');
        if (fs.existsSync(envPath)) {
            const env = fs.readFileSync(envPath, 'utf-8');
            status.gemini_key = env.includes('GEMINI_API_KEY=') && 
                               !env.includes('your_gemini_api_key_here');
        }
    } catch {}
    
    res.json(status);
});

app.listen(PORT, () => {
    console.log(`
╔═══════════════════════════════════════════════════════════════╗
║  🚀 YOUTUBE AUTOMATION DASHBOARD                             ║
║  ─────────────────────────────────────────────────────────── ║
║  URL: http://localhost:${PORT}                                 ║
║  Status: RUNNING                                             ║
╚═══════════════════════════════════════════════════════════════╝
    `);
});
