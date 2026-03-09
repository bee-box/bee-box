"""
_bee_prompts.py
Unified calendar-thumbnail grid of all 365 bee prompts.
Missing images show as red-X tiles; existing images show as thumbnails.
Click any tile to open a modal with the prompt + actions.
Holiday-tagged tiles get a red border.
Runs fresh each time and opens bee_prompts.html in the default browser.
"""
import re
import html as html_lib
from datetime import date, timedelta
from pathlib import Path

DIR = Path(__file__).parent
SOURCE = DIR / '_bee_prompts.html'
OUTPUT = DIR / 'bee_prompts.html'

# ── Holiday computation ───────────────────────────────────────────────────────

def nth_weekday(year, month, weekday, n):
    """nth occurrence of weekday (0=Mon…6=Sun) in month. n=-1 = last."""
    if n > 0:
        d = date(year, month, 1)
        delta = (weekday - d.weekday()) % 7
        return d + timedelta(days=delta + 7 * (n - 1))
    else:
        last = date(year, month + 1, 1) - timedelta(1) if month < 12 else date(year, 12, 31)
        delta = (last.weekday() - weekday) % 7
        return last - timedelta(days=delta)

def easter(year):
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return date(year, month, day)

def compute_holidays():
    hols = {}

    def add(d, name, floating):
        key = d.strftime('%m-%d')
        hols.setdefault(key, {})
        if name not in hols[key]:
            hols[key][name] = {'years': [], 'floating': floating}
        hols[key][name]['years'].append(d.year)

    def addf(month, day, name):
        for yr in (2025, 2026, 2027):
            add(date(yr, month, day), name, floating=False)

    addf(1,  1,  "New Year's Day")
    addf(6,  19, "Juneteenth")
    addf(7,  4,  "Independence Day")
    addf(11, 11, "Veterans Day")
    addf(12, 25, "Christmas Day")
    addf(2,  2,  "Groundhog Day")
    addf(2,  14, "Valentine's Day")
    addf(3,  17, "St. Patrick's Day")
    addf(4,  1,  "April Fools' Day")
    addf(4,  15, "Tax Day")
    addf(10, 31, "Halloween")
    addf(12, 24, "Christmas Eve")
    addf(12, 31, "New Year's Eve")

    for year in (2025, 2026, 2027):
        add(nth_weekday(year, 1, 0, 3),  "MLK Day",                floating=True)
        add(nth_weekday(year, 2, 0, 3),  "Presidents' Day",        floating=True)
        add(nth_weekday(year, 5, 0, -1), "Memorial Day",           floating=True)
        add(nth_weekday(year, 9, 0, 1),  "Labor Day",              floating=True)
        add(nth_weekday(year, 10, 0, 2), "Columbus Day",           floating=True)
        add(nth_weekday(year, 11, 3, 4), "Thanksgiving",           floating=True)
        e = easter(year)
        add(e,                            "Easter",                 floating=True)
        add(e - timedelta(2),             "Good Friday",            floating=True)
        add(nth_weekday(year, 5, 6, 2),  "Mother's Day",           floating=True)
        add(nth_weekday(year, 6, 6, 3),  "Father's Day",           floating=True)
        add(nth_weekday(year, 3, 6, 2),  "Daylight Saving Starts",          floating=True)
        add(nth_weekday(year, 11, 6, 1), "Daylight Saving Ends",            floating=True)
        add(nth_weekday(year, 7, 5, 2),  "Running of the Bulls (New Orleans)", floating=True)

    add(date(2025, 12, 14), "Hanukkah", floating=True)
    add(date(2026, 12,  4), "Hanukkah", floating=True)
    add(date(2027, 11, 26), "Hanukkah", floating=True)
    return hols

HOLIDAYS = compute_holidays()

# ── Existing images ───────────────────────────────────────────────────────────

existing = {}
for f in sorted(DIR.iterdir()):
    if f.suffix.lower() == '.png' and re.fullmatch(r'\d\d-\d\d', f.stem):
        existing[f.stem] = f.name

# ── Parse template for card data ──────────────────────────────────────────────

src = SOURCE.read_text(encoding='utf-8')

card_pat = re.compile(
    r'        <div class="prompt-card"[^>]*id="card-([^"]+)"[^>]*data-month="([^"]*)".*?        </div>\n\n',
    re.DOTALL
)

card_data = {}
for m in card_pat.finditer(src):
    stem = m.group(1)
    if not re.fullmatch(r'\d\d-\d\d', stem):
        continue
    chtml = m.group(0)
    date_m   = re.search(r'<div class="date">([^<]+)</div>', chtml)
    prompt_m = re.search(r'id="prompt-[^"]+">([^<]+)</div>', chtml)
    card_data[stem] = {
        'month':      m.group(2),
        'date_label': date_m.group(1)   if date_m   else stem,
        'prompt':     prompt_m.group(1) if prompt_m else '',
    }

missing_stems = {s for s in card_data if s not in existing}
all_stems = sorted(set(existing) | missing_stems)

# ── Holiday helpers ───────────────────────────────────────────────────────────

def holiday_tags(stem):
    entries = HOLIDAYS.get(stem, {})
    tags = []
    for name, info in entries.items():
        years_str = '; '.join(str(y) for y in sorted(set(info['years'])))
        tag = f"{years_str} · {name}"
        if info['floating']:
            tag += ' · Floating'
        tags.append(tag)
    return tags

# ── Build container ───────────────────────────────────────────────────────────

container = '\n'
for stem in all_stems:
    data      = card_data.get(stem, {})
    month     = data.get('month', stem[:2])
    date_lbl  = data.get('date_label', stem)
    prompt    = data.get('prompt', '')
    htags     = holiday_tags(stem)

    cls = 'cal-card'
    if stem not in existing: cls += ' missing'
    if htags:                cls += ' holiday'

    completed = 'true' if stem in existing else 'false'
    h_attr = f' data-holiday="{html_lib.escape(" | ".join(htags))}"' if htags else ''

    if stem in existing:
        inner = f'            <img src="{existing[stem]}" alt="{stem}" loading="lazy">\n'
    else:
        inner = '            <div class="cal-x">\u2715</div>\n'

    container += (
        f'        <div class="{cls}" id="card-{stem}"\n'
        f'             data-stem="{stem}" data-month="{month}" data-completed="{completed}"\n'
        f'             data-prompt="{html_lib.escape(prompt)}" data-date="{html_lib.escape(date_lbl)}"{h_attr}\n'
        f'             onclick="openModal(\'{stem}\')">\n'
        f'{inner}'
        f'            <div class="cal-label">{stem}</div>\n'
        f'        </div>\n'
    )

# ── Inject container ──────────────────────────────────────────────────────────

html = src
before, rest = html.split('<div id="prompts-container">', 1)
_, after = rest.split('\n    </div>\n\n    <script>', 1)
holiday_groups_div = '\n    <div id="holiday-groups" style="display:none;"></div>\n'
html = before + '<div id="prompts-container">' + container + '    </div>\n' + holiday_groups_div + '\n    <script>' + after

# ── Extra CSS ─────────────────────────────────────────────────────────────────

extra_css = """
        /* ── Calendar grid ──────────────────────────────────────── */
        #prompts-container {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            padding: 8px 0;
            align-items: flex-start;
        }
        .cal-card {
            width: 90px;
            background: #fff;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            cursor: pointer;
            overflow: hidden;
            transition: transform 0.12s, box-shadow 0.12s;
            flex-shrink: 0;
            position: relative;
        }
        .cal-card:hover {
            transform: scale(1.07);
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            z-index: 1;
        }
        .cal-card img {
            width: 90px;
            height: 82px;
            object-fit: cover;
            display: block;
        }
        .cal-x {
            width: 90px;
            height: 82px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            color: #E53935;
            background: #FFEBEE;
        }
        .cal-label {
            font-size: 9px;
            color: #999;
            text-align: center;
            padding: 3px 2px;
            white-space: nowrap;
            overflow: hidden;
        }
        .cal-card.missing .cal-label { color: #C62828; font-weight: bold; }
        .cal-card.holiday {
            box-shadow: 0 0 0 2px #E53935, 0 1px 4px rgba(0,0,0,0.15);
        }
        .cal-card.holiday:hover {
            box-shadow: 0 0 0 2px #E53935, 0 4px 12px rgba(0,0,0,0.25);
        }
        .cal-card.missing[data-completed="true"] .cal-x {
            background: #E8F5E9;
            color: #4CAF50;
        }
        .cal-card.current-prompt { outline: 3px solid #FFC107; }

        /* ── Modal ───────────────────────────────────────────────── */
        #modal-overlay {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.55);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        #modal-overlay.open { display: flex; }
        #modal-box {
            background: #fff;
            border-radius: 10px;
            padding: 24px;
            max-width: 620px;
            width: 92%;
            max-height: 85vh;
            overflow-y: auto;
            position: relative;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        #modal-close {
            position: absolute;
            top: 12px; right: 14px;
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            color: #888;
            padding: 2px 6px;
            line-height: 1;
        }
        #modal-close:hover { color: #333; }
        #modal-title { font-size: 19px; font-weight: bold; color: #1976D2; margin-bottom: 8px; }
        #modal-holiday {
            background: #E53935;
            color: white;
            font-size: 11px;
            font-weight: bold;
            padding: 3px 10px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        #modal-prompt {
            background: #f9f9f9;
            padding: 14px;
            border-radius: 6px;
            font-family: monospace;
            line-height: 1.6;
            white-space: pre-wrap;
            margin: 10px 0;
            font-size: 13px;
        }
        #modal-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
        #modal-img { width: 100%; border-radius: 6px; margin-bottom: 10px; display: block; }
        .fname-btn { background: #546E7A; color: white; font-family: monospace; }
        .fname-btn:hover { background: #37474F; }
        .fname-btn.copied { background: #4CAF50; }
        .tag-toggle-btn { background: #E53935; color: white; }
        .tag-toggle-btn:hover { background: #B71C1C; }
        .tag-toggle-btn.active { background: #B71C1C; outline: 2px solid #FFC107; }

        /* ── Holiday groups view ─────────────────────────────────── */
        .holiday-group { margin-bottom: 20px; }
        .holiday-group-header {
            font-size: 14px;
            font-weight: bold;
            color: #B71C1C;
            padding: 4px 8px;
            background: #FFEBEE;
            border-radius: 4px;
            margin-bottom: 6px;
        }
        .holiday-group-cards {
            display: flex;
            flex-wrap: nowrap;
            gap: 6px;
            align-items: stretch;
        }
        .holiday-today-divider {
            width: 3px;
            min-height: 100px;
            background: #FFC107;
            border-radius: 2px;
            flex-shrink: 0;
            position: relative;
        }
        .holiday-today-divider::after {
            content: 'TODAY';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(90deg);
            font-size: 7px;
            font-weight: bold;
            color: #795548;
            white-space: nowrap;
            letter-spacing: 1px;
        }
"""

html = html.replace('    </style>', extra_css + '    </style>')

# ── Modal HTML (injected before </body>) ─────────────────────────────────────

modal_html = """
    <div id="modal-overlay" onclick="overlayClick(event)">
        <div id="modal-box">
            <button id="modal-close" onclick="closeModal()">&#x2715;</button>
            <div id="modal-title"></div>
            <div id="modal-holiday" style="display:none;"></div>
            <img id="modal-img" style="display:none;" alt="">
            <div id="modal-prompt"></div>
            <div id="modal-actions">
                <button class="copy-btn" onclick="modalCopy()">&#x1F916; Open in ChatGPT</button>
                <button class="done-btn" id="modal-done-btn" onclick="modalDone()">&#x2713; Mark Done</button>
                <button class="undo-btn" id="modal-undo-btn" onclick="modalUndo()">&#x21B6; Undo</button>
                <button class="next-btn" onclick="modalDoneAndNext()">&#x2713; Done &amp; Next &#x27A1;</button>
                <button class="fname-btn" id="modal-fname-btn" onclick="modalCopyFilename()">&#x1F4CB; 03-29.png</button>
            </div>
        </div>
    </div>
"""

# ── Override JS (separate block — later definitions win over template ones) ───

override_js = """
    <script>
        let _modalStem = null;
        let _tagsOnly = false;
        let _groupByTag = false;

        function openModal(stem) {
            const card = document.getElementById('card-' + stem);
            if (!card) return;
            _modalStem = stem;
            const isMissing = card.classList.contains('missing');
            const isDone    = card.dataset.completed === 'true';
            const holiday   = card.dataset.holiday || '';
            const prompt    = card.dataset.prompt  || '';
            const dateLabel = card.dataset.date    || stem;
            const imgSrc    = isMissing ? '' : card.querySelector('img')?.src || '';

            document.getElementById('modal-title').textContent = dateLabel + '\u2002(' + stem + ')';

            const hEl = document.getElementById('modal-holiday');
            hEl.textContent   = holiday;
            hEl.style.display = holiday ? 'inline-block' : 'none';

            const imgEl = document.getElementById('modal-img');
            imgEl.src          = imgSrc;
            imgEl.style.display = imgSrc ? 'block' : 'none';

            document.getElementById('modal-prompt').textContent = prompt;
            document.getElementById('modal-prompt').style.display = prompt ? 'block' : 'none';

            const fnBtn = document.getElementById('modal-fname-btn');
            fnBtn.textContent = '\U0001F4CB ' + stem + '.png';
            fnBtn.classList.remove('copied');

            const actions = document.getElementById('modal-actions');
            actions.style.display = isMissing ? 'flex' : 'none';
            if (isMissing) {
                document.getElementById('modal-done-btn').style.display = isDone ? 'none'         : 'inline-block';
                document.getElementById('modal-undo-btn').style.display = isDone ? 'inline-block' : 'none';
            }

            document.getElementById('modal-overlay').classList.add('open');
        }

        function overlayClick(e) {
            if (e.target === document.getElementById('modal-overlay')) closeModal();
        }

        function closeModal() {
            document.getElementById('modal-overlay').classList.remove('open');
            _modalStem = null;
        }

        function modalCopy() {
            if (!_modalStem) return;
            const card = document.getElementById('card-' + _modalStem);
            window.open('https://chatgpt.com/?q=' + encodeURIComponent(card.dataset.prompt || ''), '_blank');
        }

        function modalDone() {
            if (!_modalStem) return;
            markDone(_modalStem);
            document.getElementById('modal-done-btn').style.display = 'none';
            document.getElementById('modal-undo-btn').style.display = 'inline-block';
        }

        function modalUndo() {
            if (!_modalStem) return;
            markUndone(_modalStem);
            document.getElementById('modal-done-btn').style.display = 'inline-block';
            document.getElementById('modal-undo-btn').style.display = 'none';
        }

        function modalCopyFilename() {
            if (!_modalStem) return;
            const fname = _modalStem + '.png';
            navigator.clipboard.writeText(fname).then(() => {
                const btn = document.getElementById('modal-fname-btn');
                btn.textContent = '\u2713 Copied!';
                btn.classList.add('copied');
                setTimeout(() => {
                    btn.textContent = '\U0001F4CB ' + fname;
                    btn.classList.remove('copied');
                }, 1500);
            });
        }

        function modalDoneAndNext() {
            if (!_modalStem) return;
            markDone(_modalStem);
            closeModal();
            jumpToNext();
        }

        function checkMissingFiles() {
            document.querySelectorAll('.cal-card.missing').forEach(card => {
                const stem = card.dataset.stem;
                const img = new Image();
                img.onload = () => {
                    card.classList.remove('missing');
                    card.dataset.completed = 'true';
                    const xEl = card.querySelector('.cal-x');
                    if (xEl) {
                        const imgEl = document.createElement('img');
                        imgEl.src = stem + '.png';
                        imgEl.alt = stem;
                        imgEl.loading = 'lazy';
                        card.replaceChild(imgEl, xEl);
                    }
                    updateStats();
                };
                img.src = stem + '.png?' + Date.now();
            });
        }

        // Override template functions to work with .cal-card

        function markDone(stem) {
            const card = document.getElementById('card-' + stem);
            if (!card) return;
            card.dataset.completed = 'true';
            const completed = getCompletedPrompts();
            completed[stem] = true;
            saveCompletedPrompts(completed);
            updateStats();
        }

        function markUndone(stem) {
            const card = document.getElementById('card-' + stem);
            if (!card) return;
            card.dataset.completed = 'false';
            const completed = getCompletedPrompts();
            delete completed[stem];
            saveCompletedPrompts(completed);
            updateStats();
        }

        function loadCompletionState() {
            const completed = getCompletedPrompts();
            document.querySelectorAll('.cal-card.missing').forEach(card => {
                if (completed[card.dataset.stem]) card.dataset.completed = 'true';
            });
            updateStats();
            checkMissingFiles();
        }

        function updateStats() {
            const total = document.querySelectorAll('.cal-card').length;
            const done  = document.querySelectorAll('.cal-card[data-completed="true"]').length;
            document.getElementById('total-count').textContent     = total;
            document.getElementById('completed-count').textContent = done;
            document.getElementById('remaining-count').textContent = total - done;
            const pct = total > 0 ? Math.round(done / total * 100) : 0;
            const bar = document.getElementById('progress-bar');
            bar.style.width = pct + '%';
            bar.textContent = pct + '%';
        }

        function applyFilters() {
            document.querySelectorAll('.cal-card').forEach(card => {
                const done  = card.dataset.completed === 'true';
                const month = card.dataset.month;
                const okStatus = currentFilter === 'all'
                    || (currentFilter === 'todo'      && !done)
                    || (currentFilter === 'completed' && done);
                const okMonth = currentMonth === 'all' || month === currentMonth;
                const okTags  = !_tagsOnly || card.classList.contains('holiday');
                card.style.display = (okStatus && okMonth && okTags) ? '' : 'none';
            });
        }

        function toggleTagsOnly() {
            _tagsOnly = !_tagsOnly;
            document.getElementById('fb-tags').classList.toggle('active', _tagsOnly);
            applyFilters();
        }

        function toggleGroupByTag() {
            _groupByTag = !_groupByTag;
            document.getElementById('fb-group-tags').classList.toggle('active', _groupByTag);
            const container = document.getElementById('prompts-container');
            const groups    = document.getElementById('holiday-groups');
            if (_groupByTag) {
                renderHolidayGroups();
                container.style.display = 'none';
                groups.style.display    = 'block';
            } else {
                container.style.display = '';
                groups.style.display    = 'none';
            }
        }

        function renderHolidayGroups() {
            // Build map: holiday name -> [{card, year}]
            // year is null for fixed holidays (same MM-DD every year)
            const groups = {};
            const todayStr = new Date().toISOString().slice(0, 10); // "YYYY-MM-DD"

            document.querySelectorAll('.cal-card.holiday').forEach(card => {
                const attr = card.dataset.holiday || '';
                attr.split(' | ').forEach(entry => {
                    const parts = entry.split(' \u00b7 ');
                    const name  = parts[1] || entry;
                    const yearNums = parts[0].split(';').map(y => parseInt(y.trim()));
                    // floating = single year per card; fixed = multiple years, one card
                    const year = yearNums.length === 1 ? yearNums[0] : null;
                    if (year === null) return; // skip fixed holidays
                    if (!groups[name]) groups[name] = [];
                    groups[name].push({ card, year });
                });
            });

            // Pre-sort each group's items by (year, stem)
            const itemSort = (a, b) =>
                (a.year + '-' + a.card.dataset.stem).localeCompare(b.year + '-' + b.card.dataset.stem);
            Object.values(groups).forEach(items => items.sort(itemSort));

            const container = document.getElementById('holiday-groups');
            container.innerHTML = '';

            Object.keys(groups)
                .sort((a, b) => {
                    const aFirst = groups[a][0];
                    const bFirst = groups[b][0];
                    return (aFirst.year + '-' + aFirst.card.dataset.stem)
                        .localeCompare(bFirst.year + '-' + bFirst.card.dataset.stem);
                })
                .forEach(name => {
                const items = groups[name];

                const section = document.createElement('div');
                section.className = 'holiday-group';

                const header = document.createElement('div');
                header.className = 'holiday-group-header';
                header.textContent = name + '  (' + items.length + ')';
                section.appendChild(header);

                const cardsRow = document.createElement('div');
                cardsRow.className = 'holiday-group-cards';

                let dividerInserted = false;
                items.forEach(({ card, year }) => {
                    // Insert today-divider before the first card that is today or in the future
                    // Only meaningful for floating holidays (year !== null) with multiple cards
                    if (!dividerInserted && year !== null && items.length > 1) {
                        const itemDate = year + '-' + card.dataset.stem;
                        if (itemDate >= todayStr) {
                            const div = document.createElement('div');
                            div.className = 'holiday-today-divider';
                            cardsRow.appendChild(div);
                            dividerInserted = true;
                        }
                    }

                    const clone = card.cloneNode(true);
                    const stem  = card.dataset.stem;
                    clone.onclick = () => openModal(stem);
                    if (year !== null) {
                        const lbl = clone.querySelector('.cal-label');
                        if (lbl) lbl.textContent = year + ' · ' + stem;
                    }
                    cardsRow.appendChild(clone);
                });

                section.appendChild(cardsRow);
                container.appendChild(section);
            });
        }

        function jumpToNext() {
            document.querySelectorAll('.cal-card.current-prompt').forEach(c => c.classList.remove('current-prompt'));
            for (const card of document.querySelectorAll('.cal-card.missing')) {
                if (card.dataset.completed !== 'true' && card.style.display !== 'none') {
                    card.classList.add('current-prompt');
                    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    return;
                }
            }
            alert('All prompts are done! Great work! \U0001F41D');
        }

        document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
    </script>
"""

html = html.replace('</body>', modal_html + override_js + '\n</body>')

# ── Write output ──────────────────────────────────────────────────────────────

OUTPUT.write_text(html, encoding='utf-8')
tagged = sum(1 for s in all_stems if s in HOLIDAYS)
print(f"Generated {OUTPUT.name}: {len(missing_stems)} missing, {len(existing)} existing, {tagged} holiday-tagged")
import subprocess; subprocess.Popen(f'start chrome "{OUTPUT}"', shell=True)
