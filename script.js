const $ = (s) => document.querySelector(s);
const editor = $('#editor');
const preview = $('#preview');
const tocList = $('#toc-list');
const layout = $('#layout');

const STORAGE_KEY = 'shinobi-writer-state-v1';
const SNIPPET_KEY = 'shinobi-writer-snippets-v1';

const defaultText = `# 導入
> 霧深い夜、忍びは静かに集う。

{{HO1}}

## 情報収集
:::secret 本当の黒幕は別にいる :::

{忍}(しの)びの掟を胸に進め。

{{SceneTable}}

---

# クライマックス
> 月下、最後の影が交錯する。`;

function escapeHtml(text) {
  return text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function parseLine(line) {
  if (line.startsWith('# ')) {
    return `<h2 class="scene-title" data-heading>${escapeHtml(line.slice(2))}</h2>`;
  }
  if (line.startsWith('> ')) {
    return `<blockquote class="description-box">${escapeHtml(line.slice(2))}</blockquote>`;
  }
  if (line.trim() === '{{HO1}}') {
    return $('#tpl-ho').innerHTML;
  }
  if (line.trim() === '{{SceneTable}}') {
    return $('#tpl-scene-table').innerHTML;
  }
  if (line.trim() === '---') {
    return '<div class="forced-break" data-block></div>';
  }
  const secretMatch = line.match(/^:::secret\s+(.+)\s+:::$/);
  if (secretMatch) {
    return `<div class="secret-box" data-secret>${escapeHtml(secretMatch[1])}</div>`;
  }

  let text = escapeHtml(line);
  text = text.replace(/\{(.+?)\}\((.+?)\)/g, '<ruby>$1<rt>$2</rt></ruby>');
  text = text.replace(/\|(.+?)\|/g, '<code>$1</code>');
  return text.trim() ? `<p>${text}</p>` : '<br />';
}

function renderPreview() {
  const trailerImage = $('#trailer-image').value.trim();
  const scenarioTitle = escapeHtml($('#scenario-title').value.trim() || '無題シナリオ');
  const summary = escapeHtml($('#scenario-summary').value.trim());

  const lines = editor.value.split('\n');
  const html = lines.map(parseLine).join('');

  const trailer = `<section class="trailer" data-block>
    ${trailerImage ? `<img src="${escapeHtml(trailerImage)}" alt="trailer" />` : ''}
    <h1>${scenarioTitle}</h1>
    ${summary ? `<p>${summary}</p>` : ''}
  </section>`;

  preview.innerHTML = trailer + html;
  bindSecretToggle();
  rebuildTOC();
  saveLocal();
}

function bindSecretToggle() {
  preview.querySelectorAll('[data-secret]').forEach((el) => {
    el.addEventListener('click', () => el.classList.toggle('open'));
  });
}

function rebuildTOC() {
  tocList.innerHTML = '';
  const headings = [...preview.querySelectorAll('[data-heading]')];
  headings.forEach((h, index) => {
    h.id = `heading-${index}`;
    const li = document.createElement('li');
    li.textContent = h.textContent;
    li.addEventListener('click', () => {
      h.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const pos = editor.value.indexOf(`# ${h.textContent}`);
      if (pos >= 0) {
        editor.focus();
        editor.setSelectionRange(pos, pos + h.textContent.length + 2);
      }
    });
    tocList.appendChild(li);
  });
}

function insertAtCursor(text) {
  const start = editor.selectionStart;
  const end = editor.selectionEnd;
  editor.setRangeText(text, start, end, 'end');
  editor.focus();
  renderPreview();
}

function download(filename, content, type) {
  const blob = new Blob([content], { type });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

function currentState() {
  return {
    editor: editor.value,
    scenarioTitle: $('#scenario-title').value,
    trailerImage: $('#trailer-image').value,
    scenarioSummary: $('#scenario-summary').value,
    enemyData: $('#enemy-data').value,
    mode: layout.className,
  };
}

function saveLocal() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(currentState()));
}

function loadLocal() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return;
  try {
    const s = JSON.parse(raw);
    editor.value = s.editor ?? defaultText;
    $('#scenario-title').value = s.scenarioTitle ?? '';
    $('#trailer-image').value = s.trailerImage ?? '';
    $('#scenario-summary').value = s.scenarioSummary ?? '';
    $('#enemy-data').value = s.enemyData ?? '';
    if (s.mode) layout.className = s.mode;
  } catch {
    editor.value = defaultText;
  }
}

function saveSnippets(snippets) {
  localStorage.setItem(SNIPPET_KEY, JSON.stringify(snippets));
}

function getSnippets() {
  try {
    return JSON.parse(localStorage.getItem(SNIPPET_KEY) || '[]');
  } catch {
    return [];
  }
}

function renderSnippets() {
  const list = $('#snippet-list');
  const snippets = getSnippets();
  list.innerHTML = '';
  snippets.forEach((s, idx) => {
    const li = document.createElement('li');
    const useBtn = document.createElement('button');
    useBtn.textContent = `挿入: ${s.name}`;
    useBtn.addEventListener('click', () => insertAtCursor(`${s.content}\n`));
    const delBtn = document.createElement('button');
    delBtn.textContent = '削除';
    delBtn.addEventListener('click', () => {
      snippets.splice(idx, 1);
      saveSnippets(snippets);
      renderSnippets();
    });
    li.append(useBtn, delBtn);
    list.appendChild(li);
  });
}

function setMode(mode) {
  layout.className = `layout ${mode}`;
  ['mode-dual', 'mode-editor', 'mode-preview'].forEach((id) => {
    const b = document.getElementById(id);
    b.classList.toggle('active', id === `mode-${mode.split('-')[0]}`);
  });
  saveLocal();
}

$('#mode-dual').addEventListener('click', () => setMode('dual-view'));
$('#mode-editor').addEventListener('click', () => setMode('editor-only'));
$('#mode-preview').addEventListener('click', () => setMode('preview-only'));
$('#btn-print').addEventListener('click', () => window.print());

$('#btn-export-md').addEventListener('click', () => download('scenario.md', editor.value, 'text/markdown'));
$('#btn-export-txt').addEventListener('click', () => download('scenario.txt', editor.value, 'text/plain'));
$('#btn-export-html').addEventListener('click', () => {
  const html = `<!doctype html><html lang="ja"><head><meta charset="UTF-8"><title>scenario</title></head><body>${preview.innerHTML}</body></html>`;
  download('scenario.html', html, 'text/html');
});

$('#btn-save-json').addEventListener('click', () => {
  download('shinobi-project.json', JSON.stringify(currentState(), null, 2), 'application/json');
});

$('#file-json').addEventListener('change', async (e) => {
  const file = e.target.files?.[0];
  if (!file) return;
  const text = await file.text();
  const data = JSON.parse(text);
  editor.value = data.editor ?? '';
  $('#scenario-title').value = data.scenarioTitle ?? '';
  $('#trailer-image').value = data.trailerImage ?? '';
  $('#scenario-summary').value = data.scenarioSummary ?? '';
  $('#enemy-data').value = data.enemyData ?? '';
  layout.className = data.mode || 'layout dual-view';
  renderPreview();
});

$('#btn-copy-selection').addEventListener('click', async () => {
  const selected = editor.value.slice(editor.selectionStart, editor.selectionEnd) || editor.value;
  await navigator.clipboard.writeText(selected);
});

$('#btn-copy-enemy-json').addEventListener('click', async () => {
  const value = $('#enemy-data').value.trim();
  const parsed = JSON.parse(value || '[]');
  await navigator.clipboard.writeText(JSON.stringify(parsed, null, 2));
});

$('#btn-add-snippet').addEventListener('click', () => {
  const name = $('#snippet-name').value.trim();
  const content = $('#snippet-content').value.trim();
  if (!name || !content) return;
  const snippets = getSnippets();
  snippets.push({ name, content });
  saveSnippets(snippets);
  $('#snippet-name').value = '';
  $('#snippet-content').value = '';
  renderSnippets();
});

document.querySelectorAll('[data-insert]').forEach((btn) => {
  btn.addEventListener('click', () => insertAtCursor(btn.dataset.insert || ''));
});

['input', 'keyup'].forEach((ev) => editor.addEventListener(ev, renderPreview));
['scenario-title', 'trailer-image', 'scenario-summary'].forEach((id) => {
  $(`#${id}`).addEventListener('input', renderPreview);
});

document.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
    e.preventDefault();
    $('#btn-save-json').click();
  }
});

loadLocal();
if (!editor.value.trim()) editor.value = defaultText;
renderSnippets();
renderPreview();
