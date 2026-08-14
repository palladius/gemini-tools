const http = require('http');
const path = require('path');
const fs = require('fs');
const { execSync, exec } = require('child_process');

const PORT = process.env.PORT || 3333;
const BASE_DIR = path.join(__dirname, '..');
const EVAL_DIR = path.join(BASE_DIR, 'out', 'evals');
const PUBLIC_DIR = path.join(__dirname, 'public');

function getAllRecords() {
    const records = [];
    if (!fs.existsSync(EVAL_DIR)) return records;

    const subjects = fs.readdirSync(EVAL_DIR).filter(f => {
        return fs.statSync(path.join(EVAL_DIR, f)).isDirectory();
    });

    for (const sub of subjects) {
        const jsonlPath = path.join(EVAL_DIR, sub, 'evaluations.jsonl');
        if (fs.existsSync(jsonlPath)) {
            const content = fs.readFileSync(jsonlPath, 'utf8');
            const lines = content.split('\n');
            for (const line of lines) {
                if (line.trim()) {
                    try {
                        records.push(JSON.parse(line.trim()));
                    } catch (e) {}
                }
            }
        }
    }
    return records;
}

function getMimeType(filePath) {
    const ext = path.extname(filePath).toLowerCase();
    const map = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp'
    };
    return map[ext] || 'application/octet-stream';
}

const server = http.createServer((req, res) => {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    const pathname = url.pathname;

    // API: Available character subjects list
    if (pathname === '/api/subjects' && req.method === 'GET') {
        const records = getAllRecords();
        const subjects = Array.from(new Set(records.map(r => r.subject || 'Unknown'))).sort();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ subjects }));
    }

    // API: Pending evaluations
    if (pathname === '/api/pending' && req.method === 'GET') {
        const selectedSubject = url.searchParams.get('subject');
        let records = getAllRecords();
        if (selectedSubject && selectedSubject !== 'ALL') {
            records = records.filter(r => (r.subject || '').toLowerCase().includes(selectedSubject.toLowerCase()));
        }
        const pending = records.filter(r => !r.human_eval || r.human_eval.score === undefined || r.human_eval.score === null);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({
            total: records.length,
            pending_count: pending.length,
            pending: pending
        }));
    }

    // API: Completed evaluations (Ranked Album: Highest scores first)
    if (pathname === '/api/completed' && req.method === 'GET') {
        const selectedSubject = url.searchParams.get('subject');
        let records = getAllRecords();
        if (selectedSubject && selectedSubject !== 'ALL') {
            records = records.filter(r => (r.subject || '').toLowerCase().includes(selectedSubject.toLowerCase()));
        }
        const completed = records.filter(r => r.human_eval && r.human_eval.score !== undefined && r.human_eval.score !== null);
        completed.sort((a, b) => (b.human_eval.score || 0) - (a.human_eval.score || 0));
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({
            total: records.length,
            completed_count: completed.length,
            completed: completed
        }));
    }

    // API: Submit vote
    if (pathname === '/api/vote' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const { eval_id, score, critique } = JSON.parse(body);
                if (!eval_id || score === undefined) {
                    res.writeHead(400, { 'Content-Type': 'application/json' });
                    return res.end(JSON.stringify({ error: 'Missing eval_id or score' }));
                }

                // Update via Python eval_dataset.py
                const pyCmd = `uv run --with python-slugify python -c "import eval_dataset; eval_dataset.record_human_vote('${eval_id}', ${score}, '${(critique || '').replace(/'/g, "\\'")}')"`;
                execSync(pyCmd, { cwd: BASE_DIR });

                const updatedRecords = getAllRecords();
                const remaining = updatedRecords.filter(r => !r.human_eval || r.human_eval.score === undefined || r.human_eval.score === null);

                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({
                    success: true,
                    eval_id,
                    score,
                    remaining_count: remaining.length
                }));
            } catch (e) {
                res.writeHead(500, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ error: e.message }));
            }
        });
        return;
    }

    // Serve files
    let targetPath = '';
    if (pathname.startsWith('/file/')) {
        targetPath = decodeURIComponent(pathname.substring(6));
    } else {
        targetPath = path.join(PUBLIC_DIR, pathname === '/' ? 'index.html' : pathname);
    }

    if (fs.existsSync(targetPath) && fs.statSync(targetPath).isFile()) {
        res.writeHead(200, { 'Content-Type': getMimeType(targetPath) });
        fs.createReadStream(targetPath).pipe(res);
    } else {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('404 Not Found');
    }
});

server.listen(PORT, () => {
    console.log(`\n🚀 Character Consistency Approval Web App running at http://localhost:${PORT}`);
    console.log(`💡 Opening browser... View evaluation queue & ranked leaderboard album.`);
    try {
        exec(`open http://localhost:${PORT}`);
    } catch (e) {}
});
