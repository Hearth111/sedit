const editor = document.getElementById('editor');
const previewDocument = document.getElementById('previewDocument');
const projectTitle = document.getElementById('projectTitle');
const coverImagePath = document.getElementById('coverImagePath');
const saveProjectBtn = document.getElementById('saveProjectBtn');
const loadProjectBtn = document.getElementById('loadProjectBtn');
const exportPdfBtn = document.getElementById('exportPdfBtn');
const statusBar = document.getElementById('statusBar');
const hoTemplate = document.getElementById('hoTemplate');

const project = {
  title: '無題シナリオ',
  imagePath: '',
  text: '# 導入\n> ここに読み上げ\n\n{{HO1}}',
  handouts: {
    HO1: '使命: ここに使命\n秘密: ここに秘密'
  }
};

function setStatus(message) {
  statusBar.textContent = message;
}

function escapeHtml(raw) {
  return raw
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function insertAtCursor(text) {
  const start = editor.selectionStart;
  const end = editor.selectionEnd;
  editor.value = `${editor.value.slice(0, start)}${text}${editor.value.slice(end)}`;
  editor.selectionStart = editor.selectionEnd = start + text.length;
  editor.focus();
  syncFromEditor();
}

function hoElement(key, body) {
  const node = hoTemplate.content.firstElementChild.cloneNode(true);
  node.querySelector('h4').textContent = key;
  node.querySelector('p').textContent = body;
  return node;
}

function renderSceneTable(rows) {
  const table = document.createElement('table');
  table.className = 'scene-table';
  rows.forEach((row, index) => {
    const tr = document.createElement('tr');
    row.split(',').forEach((cell) => {
      const c = document.createElement(index === 0 ? 'th' : 'td');
      c.textContent = cell.trim();
      tr.appendChild(c);
    });
    table.appendChild(tr);
  });
  return table;
}

function renderPreview() {
  previewDocument.innerHTML = '';
  const lines = project.text.split('\n');

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i].trimEnd();

    if (line.startsWith('# ')) {
      const h = document.createElement('h3');
      h.className = 'scene-title';
      h.textContent = line.slice(2).trim();
      previewDocument.appendChild(h);
      continue;
    }

    if (line.startsWith('> ')) {
      const block = document.createElement('blockquote');
      block.className = 'read-aloud';
      block.textContent = line.slice(2).trim();
      previewDocument.appendChild(block);
      continue;
    }

    if (line.startsWith(':::secret') && line.endsWith(':::')) {
      const secret = document.createElement('button');
      secret.className = 'secret';
      secret.type = 'button';
      secret.textContent = line.replace(':::secret', '').replace(':::', '').trim();
      secret.addEventListener('click', () => secret.classList.toggle('revealed'));
      previewDocument.appendChild(secret);
      continue;
    }

    if (line.startsWith('[scene-table]')) {
      const rows = [];
      i += 1;
      while (i < lines.length && !lines[i].startsWith('[/scene-table]')) {
        rows.push(lines[i]);
        i += 1;
      }
      previewDocument.appendChild(renderSceneTable(rows));
      continue;
    }

    const hoMatches = [...line.matchAll(/\{\{([A-Z]+\d+)\}\}/g)];
    if (hoMatches.length > 0) {
      hoMatches.forEach((m) => {
        const key = m[1];
        const body = project.handouts[key] ?? `${key} が未定義です`;
        previewDocument.appendChild(hoElement(key, body));
      });
      continue;
    }

    if (line.trim() === '') {
      previewDocument.appendChild(document.createElement('br'));
      continue;
    }

    const p = document.createElement('p');
    p.className = 'paragraph';
    p.textContent = line;
    previewDocument.appendChild(p);
  }
}

function syncFromEditor() {
  project.text = editor.value;
  project.title = projectTitle.value.trim() || '無題シナリオ';
  project.imagePath = coverImagePath.value.trim();
  renderPreview();
}

function applyProject(loaded) {
  project.title = loaded.title || '無題シナリオ';
  project.imagePath = loaded.imagePath || '';
  project.text = loaded.text || '';
  project.handouts = loaded.handouts || {};

  projectTitle.value = project.title;
  coverImagePath.value = project.imagePath;
  editor.value = project.text;
  renderPreview();
}

function collectPrintHtml() {
  const title = escapeHtml(project.title);
  return `<!doctype html>
<html lang="ja">
<head><meta charset="utf-8"><title>${title}</title></head>
<body>
<main class="preview-panel"><div class="preview-a4"><article class="scenario-body">${previewDocument.innerHTML}</article></div></main>
</body>
</html>`;
}

async function saveProject() {
  syncFromEditor();
  const result = await eel.save_project(project)();
  setStatus(result.message);
}

async function loadProject() {
  const result = await eel.load_project()();
  if (result.ok) {
    applyProject(result.payload);
  }
  setStatus(result.message);
}

async function exportPdf() {
  syncFromEditor();
  const html = collectPrintHtml();
  const css = await fetch('style.css').then((r) => r.text());
  const result = await eel.save_pdf(html, css)();
  setStatus(result.message);
}

Array.from(document.querySelectorAll('.tool')).forEach((btn) => {
  btn.addEventListener('click', () => insertAtCursor(btn.dataset.insert || ''));
});

editor.addEventListener('input', syncFromEditor);
projectTitle.addEventListener('input', syncFromEditor);
coverImagePath.addEventListener('input', syncFromEditor);
saveProjectBtn.addEventListener('click', saveProject);
loadProjectBtn.addEventListener('click', loadProject);
exportPdfBtn.addEventListener('click', exportPdf);

document.addEventListener('keydown', (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
    event.preventDefault();
    saveProject();
  }
});

applyProject(project);
setStatus('編集を開始できます');
