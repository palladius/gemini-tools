let pendingQueue = [];
let currentIndex = 0;
let isFaceZoomMode = true;
let selectedSubject = 'ALL';
let currentMode = 'VOTE'; // 'VOTE' or 'ALBUM'

const queueBadge = document.getElementById('queueBadge');
const subjectTag = document.getElementById('subjectTag');
const modelTitle = document.getElementById('modelTitle');
const targetImage = document.getElementById('targetImage');
const promptText = document.getElementById('promptText');
const robotScorePill = document.getElementById('robotScorePill');
const robotCritiqueText = document.getElementById('robotCritiqueText');
const referenceMosaic = document.getElementById('referenceMosaic');
const scoreInput = document.getElementById('scoreInput');
const validationMsg = document.getElementById('validationMsg');
const presetButtons = document.querySelectorAll('.rating-presets button');
const critiqueInput = document.getElementById('critiqueInput');
const submitVoteBtn = document.getElementById('submitVoteBtn');
const allDoneOverlay = document.getElementById('allDoneOverlay');
const viewAlbumFromOverlayBtn = document.getElementById('viewAlbumFromOverlayBtn');

const faceZoomBtn = document.getElementById('faceZoomBtn');
const fullPhotoBtn = document.getElementById('fullPhotoBtn');

const filterPills = document.getElementById('filterPills');
const modeVoteBtn = document.getElementById('modeVoteBtn');
const modeAlbumBtn = document.getElementById('modeAlbumBtn');
const voteWorkspace = document.getElementById('voteWorkspace');
const leaderboardWorkspace = document.getElementById('leaderboardWorkspace');
const albumGrid = document.getElementById('albumGrid');

function isValidScore(valStr) {
    if (!valStr || typeof valStr !== 'string') return false;
    const str = valStr.trim();
    const regex = /^(10(\.0)?|[0-9](\.[0-9])?)$/;
    if (!regex.test(str)) return false;
    const num = parseFloat(str);
    return !isNaN(num) && num >= 0.0 && num <= 10.0;
}

function updateValidationUI() {
    const val = scoreInput.value.trim();
    if (isValidScore(val)) {
        scoreInput.classList.remove('invalid');
        validationMsg.classList.remove('invalid');
        validationMsg.textContent = '✓ Valid Float (0.0 - 10.0)';
        submitVoteBtn.disabled = false;
        return true;
    } else {
        scoreInput.classList.add('invalid');
        validationMsg.classList.add('invalid');
        validationMsg.textContent = '❌ Invalid (Max 1 decimal place, 0.0 - 10.0)';
        submitVoteBtn.disabled = true;
        return false;
    }
}

// Mode Switcher handlers
modeVoteBtn.addEventListener('click', () => setMode('VOTE'));
modeAlbumBtn.addEventListener('click', () => setMode('ALBUM'));
viewAlbumFromOverlayBtn.addEventListener('click', () => {
    allDoneOverlay.classList.add('hidden');
    setMode('ALBUM');
});

function setMode(mode) {
    currentMode = mode;
    if (mode === 'VOTE') {
        modeVoteBtn.classList.add('active');
        modeAlbumBtn.classList.remove('active');
        voteWorkspace.classList.remove('hidden');
        leaderboardWorkspace.classList.add('hidden');
        loadQueue();
    } else {
        modeAlbumBtn.classList.add('active');
        modeVoteBtn.classList.remove('active');
        leaderboardWorkspace.classList.remove('hidden');
        voteWorkspace.classList.add('hidden');
        allDoneOverlay.classList.add('hidden');
        loadLeaderboardAlbum();
    }
}

// Face Zoom Toggle
faceZoomBtn.addEventListener('click', () => {
    isFaceZoomMode = true;
    faceZoomBtn.classList.add('active');
    fullPhotoBtn.classList.remove('active');
    updateTargetImageDisplay();
});

fullPhotoBtn.addEventListener('click', () => {
    isFaceZoomMode = false;
    fullPhotoBtn.classList.add('active');
    faceZoomBtn.classList.remove('active');
    updateTargetImageDisplay();
});

function updateTargetImageDisplay() {
    if (currentIndex >= pendingQueue.length) return;
    const item = pendingQueue[currentIndex];
    const imgObj = item.generated_image || {};

    let imgPath = '';
    if (isFaceZoomMode) {
        if (imgObj.face_crop_path) {
            imgPath = imgObj.face_crop_path;
        } else {
            const ann = imgObj.annotated_path || imgObj.raw_path || '';
            imgPath = ann.replace('_annotated.png', '_face.png').replace('_raw.png', '_face.png');
        }
    } else {
        imgPath = imgObj.annotated_path || imgObj.raw_path || '';
    }

    if (imgPath) {
        targetImage.src = `/file/${imgPath}`;
    } else {
        targetImage.src = '';
    }
}

scoreInput.addEventListener('input', () => {
    updateValidationUI();
    const val = scoreInput.value.trim();
    presetButtons.forEach(btn => {
        if (btn.getAttribute('data-val') === val) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
});

presetButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const val = btn.getAttribute('data-val');
        scoreInput.value = val;
        updateValidationUI();
        presetButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    });
});

async function loadSubjects() {
    try {
        const res = await fetch('/api/subjects');
        const data = await res.json();
        const subjects = data.subjects || [];

        filterPills.innerHTML = '<button data-subject="ALL" class="pill-btn active">ALL</button>';
        subjects.forEach(sub => {
            const btn = document.createElement('button');
            btn.className = 'pill-btn';
            btn.setAttribute('data-subject', sub);
            btn.textContent = sub;
            filterPills.appendChild(btn);
        });

        // Add event listeners
        document.querySelectorAll('.pill-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                selectedSubject = btn.getAttribute('data-subject');
                if (currentMode === 'VOTE') {
                    loadQueue();
                } else {
                    loadLeaderboardAlbum();
                }
            });
        });
    } catch (e) {
        console.error('Failed loading subjects:', e);
    }
}

async function loadQueue() {
    try {
        const url = selectedSubject === 'ALL' ? '/api/pending' : `/api/pending?subject=${encodeURIComponent(selectedSubject)}`;
        const res = await fetch(url);
        const data = await res.json();
        pendingQueue = data.pending || [];
        queueBadge.textContent = `${pendingQueue.length} Pending Evaluation(s)`;
        
        if (pendingQueue.length === 0) {
            allDoneOverlay.classList.remove('hidden');
        } else {
            allDoneOverlay.classList.add('hidden');
            currentIndex = 0;
            renderCurrentItem();
        }
    } catch (e) {
        console.error('Failed loading pending queue:', e);
        queueBadge.textContent = 'Error Loading Queue';
    }
}

async function loadLeaderboardAlbum() {
    try {
        const url = selectedSubject === 'ALL' ? '/api/completed' : `/api/completed?subject=${encodeURIComponent(selectedSubject)}`;
        const res = await fetch(url);
        const data = await res.json();
        const completed = data.completed || [];

        albumGrid.innerHTML = '';
        if (completed.length === 0) {
            albumGrid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 3rem;">No completed evaluations yet for this subject filter.</div>';
            return;
        }

        completed.forEach(item => {
            const humanScore = (item.human_eval && item.human_eval.score !== undefined) ? item.human_eval.score.toFixed(1) : '-';
            const robotScore = (item.robot_eval && item.robot_eval.character_consistency_score) || '-';
            const imgObj = item.generated_image || {};
            const imgPath = imgObj.face_crop_path || imgObj.annotated_path || imgObj.raw_path || '';

            let badgeClass = 'human-rank-badge';
            const numScore = parseFloat(humanScore);
            if (numScore >= 8.0) badgeClass += ' top-tier';
            else if (numScore <= 4.0) badgeClass += ' low-tier';

            const card = document.createElement('div');
            card.className = 'album-card';
            card.innerHTML = `
                <div class="album-card-img-wrap">
                    <img src="/file/${imgPath}" alt="${item.model_name}">
                    <span class="${badgeClass}">★ ${humanScore}</span>
                    <span class="robot-rank-badge">🤖 ${robotScore}/10</span>
                </div>
                <div class="album-card-body">
                    <div class="model-name">${item.model_name} (${item.subject || 'Subject'})</div>
                    <p class="prompt-snippet">${item.prompt || ''}</p>
                    ${item.human_eval && item.human_eval.critique ? `<div class="critique-snippet">"${item.human_eval.critique}"</div>` : ''}
                    <button class="edit-vote-btn" data-eval-id="${item.eval_id}">✏️ Edit Rating</button>
                </div>
            `;
            
            const editBtn = card.querySelector('.edit-vote-btn');
            editBtn.addEventListener('click', () => {
                editSingleItemVote(item);
            });
            
            albumGrid.appendChild(card);
        });
    } catch (e) {
        console.error('Failed loading leaderboard album:', e);
    }
}

function editSingleItemVote(item) {
    // Switch view to vote queue workspace
    currentView = 'vote';
    modeVoteBtn.classList.add('active');
    modeAlbumBtn.classList.remove('active');
    voteWorkspace.classList.remove('hidden');
    leaderboardWorkspace.classList.add('hidden');
    allDoneOverlay.classList.add('hidden');

    // Pre-fill queue with single item and display
    pendingQueue = [item];
    currentIndex = 0;
    renderCurrentItem();

    // Pre-fill existing score and critique
    if (item.human_eval) {
        if (item.human_eval.score !== undefined) {
            scoreInput.value = item.human_eval.score.toFixed(1);
            validateScoreInput(scoreInput.value);
            // Highlight preset if exact match
            const presetBtn = document.querySelector(`.rating-presets button[data-val="${item.human_eval.score.toFixed(1)}"]`);
            if (presetBtn) {
                document.querySelectorAll('.rating-presets button').forEach(b => b.classList.remove('active'));
                presetBtn.classList.add('active');
            }
        }
        if (item.human_eval.critique) {
            critiqueInput.value = item.human_eval.critique;
        }
    }
}

function renderCurrentItem() {
    if (currentIndex >= pendingQueue.length) {
        allDoneOverlay.classList.remove('hidden');
        return;
    }

    const item = pendingQueue[currentIndex];
    
    subjectTag.textContent = item.subject || 'Subject';
    modelTitle.textContent = item.model_name || 'Gemini Model';
    promptText.textContent = item.prompt || 'No prompt specified';

    updateTargetImageDisplay();

    // Robot LLM judge
    const robot = item.robot_eval || {};
    const robotScore = robot.character_consistency_score || robot.score || '-';
    robotScorePill.textContent = `Score: ${robotScore}/10 (${robot.verdict || 'EVAL'})`;
    robotCritiqueText.textContent = robot.resemblance_critique || robot.critique || 'No critique available.';

    // References Mosaic
    referenceMosaic.innerHTML = '';
    const refs = item.reference_images || [];
    refs.forEach(r => {
        const img = document.createElement('img');
        img.className = 'ref-thumb';
        const p = r.local_path || r;
        img.src = `/file/${p}`;
        img.alt = r.name || 'Reference';
        referenceMosaic.appendChild(img);
    });

    // Reset default rating to 7.0
    scoreInput.value = '7.0';
    updateValidationUI();
    critiqueInput.value = '';
    scoreInput.focus();
}

async function submitVote() {
    if (!updateValidationUI()) {
        return;
    }

    if (currentIndex >= pendingQueue.length) return;
    const item = pendingQueue[currentIndex];
    const scoreVal = parseFloat(scoreInput.value.trim());

    submitVoteBtn.disabled = true;
    submitVoteBtn.textContent = 'Submitting Rating...';

    try {
        const res = await fetch('/api/vote', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                eval_id: item.eval_id,
                score: scoreVal,
                critique: critiqueInput.value
            })
        });

        const data = await res.json();
        if (data.success) {
            pendingQueue.splice(currentIndex, 1);
            queueBadge.textContent = `${pendingQueue.length} Pending Evaluation(s)`;
            
            if (pendingQueue.length === 0) {
                allDoneOverlay.classList.remove('hidden');
            } else {
                renderCurrentItem();
            }
        } else {
            alert('Error: ' + (data.error || 'Failed submitting rating'));
        }
    } catch (e) {
        alert('Failed to submit vote: ' + e.message);
    } finally {
        submitVoteBtn.disabled = false;
        submitVoteBtn.textContent = 'Submit Rating & Next ➔ (Enter)';
    }
}

submitVoteBtn.addEventListener('click', submitVote);

// Keyboard hotkey listeners
document.addEventListener('keydown', (e) => {
    if (currentMode === 'VOTE' && e.key === 'Enter' && allDoneOverlay.classList.contains('hidden')) {
        e.preventDefault();
        submitVote();
    }
});

// Init on startup
loadSubjects();
loadQueue();
