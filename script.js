const editor = document.querySelector('#editor');
const previewRoot = document.querySelector('#previewRoot');
const pageTemplate = document.querySelector('#pageTemplate');
const tocEditor = document.querySelector('#tocEditor');
const tocPreview = document.querySelector('#tocPreview');
const saveBtn = document.querySelector('#saveBtn');
const loadInput = document.querySelector('#loadInput');
const printBtn = document.querySelector('#printBtn');
const addDataBtn = document.querySelector('#addDataBtn');
const dataTypeInput = document.querySelector('#dataType');
const dataKeyInput = document.querySelector('#dataKey');
const dataValueInput = document.querySelector('#dataValue');
const dataList = document.querySelector('#dataList');
const specTitleInput = document.querySelector('#specTitle');
const specPlayerCountInput = document.querySelector('#specPlayerCount');
const specTypeInput = document.querySelector('#specType');
const specCycleInput = document.querySelector('#specCycle');
const specSkillsInput = document.querySelector('#specSkills');

const project = {
  title: '深淵に揺れる月影',
  spec: {
    playerCount: '4人',
    cycle: '3サイクル',
    type: '協力型',
    skills: '第六感 / 隠形術',
  },
  content: `# 導入
> 夜は深い。漆黒の空に浮かぶ月は、血のように赤い。
| 舞台: 現代日本 / 山間の廃寺

君たちはそれぞれの使命を胸に、禁足地とされた古寺に集う。

:::secret この寺の地下には、妖刀を封じた祭壇がある :::

# 情報収集
PCはそれぞれ、寺の由来と失踪事件を調査する。

{{HO1}}

---

# クライマックス
> 鐘の音が響くたび、忍びたちの影が交差する。

| 判定目標値は7。失敗時は【生命力】を1点失う。

最後に妖刀の封印を巡り、最終決戦が始まる。`,
  data: {
    HO: {
      HO1: '使命: 妖刀の破壊\n秘密: あなたは妖刀の継承者である。',
    },
    NPC: {},
    ENEMY: {},
  },
};

editor.value = project.content;

for (const btn of document.querySelectorAll('.insert-btn')) {
  btn.addEventListener('click', () => insertAtCursor(editor, btn.dataset.insert || ''));
}

editor.addEventListener('input', () => {
  project.content = editor.value;
  renderAll();
});

editor.addEventListener('scroll', () => {
  const ratio = editor.scrollTop / Math.max(1, editor.scrollHeight - editor.clientHeight);
  previewRoot.scrollTop = ratio * Math.max(1, previewRoot.scrollHeight - previewRoot.clientHeight);
});

previewRoot.addEventListener('scroll', () => {
  if (document.activeElement === editor) return;
  const ratio = previewRoot.scrollTop / Math.max(1, previewRoot.scrollHeight - previewRoot.clientHeight);
  editor.scrollTop = ratio * Math.max(1, editor.scrollHeight - editor.clientHeight);
});

saveBtn.addEventListener('click', saveProject);
printBtn.addEventListener('click', () => window.print());
loadInput.addEventListener('change', loadProject);
addDataBtn.addEventListener('click', upsertData);
[specTitleInput, specPlayerCountInput, specTypeInput, specCycleInput, specSkillsInput].forEach((input) => {
  input.addEventListener('input', updateSpecFromForm);
});

document.addEventListener('keydown', (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
    event.preventDefault();
    saveProject();
  }
});

function insertAtCursor(textarea, text) {
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const next = textarea.value.slice(0, start) + text + textarea.value.slice(end);
  textarea.value = next;
  textarea.selectionStart = textarea.selectionEnd = start + text.length;
  textarea.focus();
  textarea.dispatchEvent(new Event('input'));
}

function parseBlocks(content) {
  const lines = content.split('\n');
  const blocks = [];
  const headings = [];

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];

    if (line.trim() === '---') {
      blocks.push({ type: 'manual-break' });
      continue;
    }

    if (line.startsWith('# ')) {
      const title = line.slice(2).trim();
      headings.push(title);
      blocks.push({ type: 'scene', text: title, id: `scene-${headings.length}` });
      continue;
    }

    if (line.startsWith('> ')) {
      blocks.push({ type: 'read', text: line.slice(2).trim() });
      continue;
    }

    if (line.startsWith('| ')) {
      blocks.push({ type: 'sidebar', text: line.slice(2).trim() });
      continue;
    }

    if (line.startsWith(':::secret') && line.endsWith(':::')) {
      const spoiler = line.replace(':::secret', '').replace(':::', '').trim();
      blocks.push({ type: 'spoiler', text: spoiler });
      continue;
    }

    if (line.startsWith('[scene-table]')) {
      const rows = [];
      i += 1;
      while (i < lines.length && !lines[i].startsWith('[/scene-table]')) {
        rows.push(lines[i]);
        i += 1;
      }
      blocks.push({ type: 'scene-table', rows });
      continue;
    }

    if (line.startsWith('[ho ')) {
      const idMatch = line.match(/id=([^\]]+)/);
      const key = idMatch?.[1] || 'HO';
      const body = [];
      i += 1;
      while (i < lines.length && !lines[i].startsWith('[/ho]')) {
        body.push(lines[i]);
        i += 1;
      }
      project.data.HO[key] = body.join('\n');
      blocks.push({ type: 'data-card', title: key, text: body.join('\n') });
      continue;
    }

    if (line.trim() === '') {
      blocks.push({ type: 'space' });
      continue;
    }

    blocks.push({ type: 'paragraph', text: line });
  }

  return { blocks, headings };
}

function resolveTags(text) {
  return text.replace(/\{\{([A-Z]+\d+)\}\}/g, (_full, key) => {
    const type = key.replace(/\d+$/, '');
    const dict = project.data[type] || {};
    const value = dict[key];
    if (!value) return `[${key} not found]`;
    return `\n[data-card:${key}]${value}[/data-card]\n`;
  });
}

function createElementForBlock(block) {
  if (block.type === 'scene') {
    const el = document.createElement('h3');
    el.className = 'scene-header';
    el.textContent = block.text;
    el.id = block.id;
    return el;
  }

  if (block.type === 'read') {
    const el = document.createElement('blockquote');
    el.className = 'read-box';
    el.textContent = block.text;
    return el;
  }

  if (block.type === 'paragraph') {
    const el = document.createElement('p');
    el.textContent = block.text;
    if (block.className) el.className = block.className;
    return el;
  }

  if (block.type === 'spoiler') {
    const el = document.createElement('span');
    el.className = 'spoiler';
    el.textContent = block.text;
    el.addEventListener('click', () => el.classList.toggle('revealed'));
    return el;
  }

  if (block.type === 'data-card') {
    const wrap = document.createElement('section');
    wrap.className = 'data-card';
    const title = document.createElement('div');
    title.className = 'data-title';
    title.textContent = block.title;
    const body = document.createElement('pre');
    body.textContent = block.text;
    body.style.whiteSpace = 'pre-wrap';
    body.style.margin = '4px 0 0';
    wrap.append(title, body);
    return wrap;
  }

  if (block.type === 'scene-table') {
    const table = document.createElement('table');
    table.className = 'spec-table';
    block.rows.forEach((row, idx) => {
      const tr = document.createElement('tr');
      row.split(',').forEach((cell) => {
        const c = document.createElement(idx === 0 ? 'th' : 'td');
        c.textContent = cell.trim();
        tr.appendChild(c);
      });
      table.appendChild(tr);
    });
    return table;
  }

  if (block.type === 'manual-break') {
    const el = document.createElement('hr');
    el.className = 'manual-break';
    return el;
  }

  return document.createElement('br');
}

function createPage(isFirst = false) {
  const page = pageTemplate.content.firstElementChild.cloneNode(true);
  if (isFirst) {
    const header = document.createElement('section');
    header.className = 'page-first-header';
    header.innerHTML = `
      <div class="trailer"></div>
      <h2>${project.title}</h2>
      <table class="spec-table overlay-spec">
        <tr><th>人数</th><td>${project.spec.playerCount}</td><th>タイプ</th><td>${project.spec.type}</td></tr>
        <tr><th>サイクル</th><td>${project.spec.cycle}</td><th>推奨技能</th><td>${project.spec.skills || ''}</td></tr>
      </table>
    `;
    page.querySelector('.page-grid').prepend(header);
  }
  return page;
}

function paginate(blocks) {
  previewRoot.innerHTML = '';
  let page = createPage(true);
  previewRoot.appendChild(page);

  let left = page.querySelector('.body-column.left');
  let right = page.querySelector('.body-column.right');
  let currentBody = left;

  for (const block of blocks) {
    if (block.type === 'manual-break') {
      page = createPage();
      previewRoot.appendChild(page);
      left = page.querySelector('.body-column.left');
      right = page.querySelector('.body-column.right');
      currentBody = left;
      continue;
    }

    const nextBlock = block.type === 'sidebar' ? { type: 'paragraph', text: block.text, className: 'sidebar-note' } : block;
    const el = createElementForBlock(nextBlock);
    currentBody.appendChild(el);

    if (currentBody.scrollHeight > currentBody.clientHeight) {
      currentBody.removeChild(el);

      if (currentBody === left) {
        currentBody = right;
        currentBody.appendChild(el);
        if (currentBody.scrollHeight > currentBody.clientHeight) {
          currentBody.removeChild(el);
          page = createPage();
          previewRoot.appendChild(page);
          left = page.querySelector('.body-column.left');
          right = page.querySelector('.body-column.right');
          currentBody = left;
          currentBody.appendChild(el);
        }
      } else {
        page = createPage();
        previewRoot.appendChild(page);
        left = page.querySelector('.body-column.left');
        right = page.querySelector('.body-column.right');
        currentBody = left;
        currentBody.appendChild(el);
      }
    }
  }
}

function buildToc(headings) {
  tocEditor.innerHTML = '';
  tocPreview.innerHTML = '';

  headings.forEach((name, index) => {
    const btnEditor = document.createElement('button');
    btnEditor.textContent = name;
    btnEditor.addEventListener('click', () => {
      const token = `# ${name}`;
      const pos = editor.value.indexOf(token);
      if (pos >= 0) {
        editor.focus();
        editor.setSelectionRange(pos, pos);
        const before = editor.value.slice(0, pos).split('\n').length;
        editor.scrollTop = (before / Math.max(1, editor.value.split('\n').length)) * editor.scrollHeight;
      }
    });

    const btnPreview = document.createElement('button');
    btnPreview.textContent = `${index + 1}. ${name}`;
    btnPreview.addEventListener('click', () => {
      const target = previewRoot.querySelector(`#scene-${index + 1}`);
      target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    tocEditor.appendChild(btnEditor);
    tocPreview.appendChild(btnPreview);
  });
}

function renderDataList() {
  dataList.innerHTML = '';
  for (const [type, items] of Object.entries(project.data)) {
    for (const [key, value] of Object.entries(items)) {
      const li = document.createElement('li');
      li.innerHTML = `<strong>${type}:${key}</strong><br><small>${value.replace(/\n/g, '<br>')}</small>`;
      dataList.appendChild(li);
    }
  }
}

function upsertData() {
  const type = dataTypeInput.value;
  const key = dataKeyInput.value.trim();
  const value = dataValueInput.value.trim();
  if (!key || !value) return;
  project.data[type][key] = value;
  renderAll();
  dataKeyInput.value = '';
  dataValueInput.value = '';
}

function saveProject() {
  const blob = new Blob([JSON.stringify(project, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'scenario-project.json';
  a.click();
  URL.revokeObjectURL(url);
}

async function loadProject(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  const text = await file.text();
  const parsed = JSON.parse(text);
  project.title = parsed.title || project.title;
  project.spec = { ...project.spec, ...(parsed.spec || {}) };
  project.content = parsed.content || '';
  project.data = parsed.data || project.data;
  editor.value = project.content;
  syncSpecForm();
  renderAll();
}



function syncSpecForm() {
  specTitleInput.value = project.title;
  specPlayerCountInput.value = project.spec.playerCount || '';
  specTypeInput.value = project.spec.type || '';
  specCycleInput.value = project.spec.cycle || '';
  specSkillsInput.value = project.spec.skills || '';
}

function updateSpecFromForm() {
  project.title = specTitleInput.value.trim() || '無題シナリオ';
  project.spec.playerCount = specPlayerCountInput.value.trim();
  project.spec.type = specTypeInput.value.trim();
  project.spec.cycle = specCycleInput.value.trim();
  project.spec.skills = specSkillsInput.value.trim();
  renderAll();
}

function renderAll() {
  const resolved = resolveTags(project.content).split('\n');
  const normalized = [];
  for (const line of resolved) {
    const dataMatch = line.match(/^\[data-card:([^\]]+)\](.*)\[\/data-card\]$/);
    if (dataMatch) {
      normalized.push(`[ho id=${dataMatch[1]}]`);
      normalized.push(...dataMatch[2].split('\n'));
      normalized.push('[/ho]');
    } else {
      normalized.push(line);
    }
  }

  const { blocks, headings } = parseBlocks(normalized.join('\n'));
  paginate(blocks);
  buildToc(headings);
  renderDataList();
}

syncSpecForm();
renderAll();
