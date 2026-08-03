
/* ============================================================
   Lab 1 — interactivity
   ============================================================ */

const totalSteps = 6;
const STORAGE_KEY = 'workshop_fsi_lab1_progress';

/* ---------- Copy to clipboard ---------- */
function copyCode(btn) {
    const block = btn.closest('.code-block');
    if (!block) { return; }
    const codeEl = block.querySelector('code');
    if (!codeEl) { return; }
    const text = codeEl.textContent;
    const original = btn.textContent;

    const done = function () {
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(function () {
            btn.textContent = original;
            btn.classList.remove('copied');
        }, 2000);
    };

    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done).catch(function () {
            btn.textContent = 'Press Ctrl+C';
            setTimeout(function () { btn.textContent = original; }, 2000);
        });
    } else {
        btn.textContent = 'Press Ctrl+C';
        setTimeout(function () { btn.textContent = original; }, 2000);
    }
}

/* ---------- Collapse / expand a step ---------- */
function toggleStep(n) {
    const card = document.getElementById('step-' + n);
    if (!card) { return; }
    const content = card.querySelector('.step-content');
    if (content) { content.classList.toggle('collapsed'); }
}

/* ---------- Progress state ---------- */
function readState() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) { return { started: false, completed: false, steps: {} }; }
        const parsed = JSON.parse(raw);
        if (!parsed.steps) { parsed.steps = {}; }
        return parsed;
    } catch (e) {
        return { started: false, completed: false, steps: {} };
    }
}

function writeState(state) {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
        /* storage unavailable — progress simply is not persisted */
    }
}

function countCompleted(state) {
    let n = 0;
    for (let i = 1; i <= totalSteps; i++) {
        if (state.steps[i] === true || state.steps[String(i)] === true) { n++; }
    }
    return n;
}

function isDone(state, i) {
    return state.steps[i] === true || state.steps[String(i)] === true;
}

function renderProgress(state) {
    const completed = countCompleted(state);
    const pct = Math.round((completed / totalSteps) * 100);

    const fill = document.getElementById('progressFill');
    if (fill) { fill.style.width = pct + '%'; }

    const label = document.getElementById('progressPercent');
    if (label) { label.textContent = pct + '%'; }

    for (let i = 1; i <= totalSteps; i++) {
        const done = isDone(state, i);
        const card = document.getElementById('step-' + i);
        if (card) { card.classList.toggle('completed', done); }

        const nav = document.querySelector('.step-nav-item[data-step="' + i + '"]');
        if (nav) { nav.classList.toggle('completed', done); }

        const box = card ? card.querySelector('.completion-checkbox input[type="checkbox"]') : null;
        if (box) { box.checked = done; }
    }
}

function markStepComplete(n) {
    const card = document.getElementById('step-' + n);
    const box = card ? card.querySelector('.completion-checkbox input[type="checkbox"]') : null;
    const checked = box ? box.checked : true;

    const state = readState();
    state.started = true;
    state.steps[n] = checked;
    state.completed = countCompleted(state) === totalSteps;
    state.lastUpdated = new Date().toISOString();
    writeState(state);

    renderProgress(state);
}

function loadProgress() {
    const state = readState();
    renderProgress(state);
    if (!state.started) {
        state.started = true;
        state.startedAt = new Date().toISOString();
        writeState(state);
    }
}

/* ---------- Active nav highlighting on scroll ---------- */
function initScrollSpy() {
    const cards = Array.prototype.slice.call(document.querySelectorAll('.step-card'));
    if (!cards.length) { return; }

    function setActive(n) {
        document.querySelectorAll('.step-nav-item').forEach(function (item) {
            item.classList.toggle('active', item.getAttribute('data-step') === String(n));
        });
    }

    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver(function (entries) {
            const visible = entries.filter(function (e) { return e.isIntersecting; });
            if (!visible.length) { return; }
            visible.sort(function (a, b) { return a.boundingClientRect.top - b.boundingClientRect.top; });
            const id = visible[0].target.id;
            const n = id.replace('step-', '');
            setActive(n);
        }, { rootMargin: '-90px 0px -55% 0px', threshold: 0 });

        cards.forEach(function (card) { observer.observe(card); });
    } else {
        window.addEventListener('scroll', function () {
            let current = 1;
            cards.forEach(function (card) {
                if (card.getBoundingClientRect().top <= 140) {
                    current = card.id.replace('step-', '');
                }
            });
            setActive(current);
        });
    }

    document.querySelectorAll('.step-nav-item').forEach(function (link) {
        link.addEventListener('click', function () {
            setActive(link.getAttribute('data-step'));
        });
    });
}

/* ---------- Init ---------- */
document.addEventListener('DOMContentLoaded', function () {
    loadProgress();
    initScrollSpy();
});
