'use strict';

const WEAPON_COLUMNS = [
  {key: 'runemark', label: 'Runemark', kind: 'text', size: 12},
  {key: 'attacks', label: 'Attacks', kind: 'int'},
  {key: 'strength', label: 'Strength', kind: 'int'},
  {key: 'dmg_hit', label: 'Dmg hit', kind: 'int'},
  {key: 'dmg_crit', label: 'Dmg crit', kind: 'int'},
  {key: 'min_range', label: 'Min range', kind: 'int'},
  {key: 'max_range', label: 'Max range', kind: 'int'},
];
const SUBFACTION_COLUMNS = [
  {key: 'runemark', label: 'Runemark', kind: 'text', size: 32},
  {key: 'bladeborn', label: 'Bladeborn', kind: 'bool'},
  {key: 'heroes_all', label: 'Heroes all', kind: 'bool'},
  {key: 'singleton', label: 'Singleton', kind: 'bool'},
];
const STATS = ['movement', 'toughness', 'wounds', 'points'];
const FLAGS = ['bladeborn', 'heroes_all', 'singleton'];
const FILE_SUFFIXES = {fighters: '_fighters.json', abilities: '_abilities.json', factions: '_faction.json'};

const $ = (id) => document.getElementById(id);
const treeEl = $('tree');
const editorEl = $('editor');
const statusEl = $('status');
const filterEl = $('filter');

let meta = {grand_alliances: [], ability_costs: [], data: ''};
let warbands = new Map();
let contextWarband = '';
let current = null;
let uid = 0;

function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === 'class') node.className = value;
    else if (key in node) node[key] = value;
    else node.setAttribute(key, value);
  }
  node.append(...children);
  return node;
}

function labelOf(key) {
  const text = key.replaceAll('_', ' ');
  return text[0].toUpperCase() + text.slice(1);
}

async function api(method, path, params = {}, body = {}) {
  const options = {method};
  if (method !== 'GET') {
    options.headers = {'Content-Type': 'application/json'};
    options.body = JSON.stringify(body);
  }
  const response = await fetch(`${path}?${new URLSearchParams(params)}`, options);
  const payload = await response.json();
  if (!response.ok) throw new Error((payload.errors ?? [response.statusText]).join('\n'));
  return payload;
}

async function run(action, title = 'Error') {
  try {
    await action();
  } catch (error) {
    showMessage(title, error.message);
  }
}

function showMessage(title, text) {
  const dialog = $('message-dialog');
  if (dialog.open) {
    $('message-text').textContent += `\n\n${title}\n${text}`;
    return;
  }
  $('message-title').textContent = title;
  $('message-text').textContent = text;
  dialog.showModal();
}

function readInt(input, label) {
  const value = input.value.trim();
  if (!/^-?\d+$/.test(value)) throw new Error(`${label} must be a whole number`);
  return Number(value);
}

function readRunemarks(input) {
  return input.value.split(',').map((r) => r.trim()).filter(Boolean);
}

function fileLabel(warband, type) {
  return `${meta.data}/${warband}/${warband.split('/').pop()}${FILE_SUFFIXES[type]}`;
}

// ---- Tree

async function loadTree() {
  const tree = await api('GET', '/api/tree');
  warbands = new Map(tree.warbands.map((w) => [w.id, w]));
  renderTree();
  if (tree.problems.length) showMessage('Cannot read all data', tree.problems.join('\n'));
}

function details(key, text, open, cls) {
  const node = el('details', {class: cls}, el('summary', {}, text));
  node.dataset.key = key;
  node.open = open.has(key);
  return node;
}

function nodeButton(warband, type, id, name, detail, subfaction) {
  const button = el('button', {class: 'node', type: 'button', title: name}, name,
    el('span', {class: 'detail'}, detail ? ` (${detail})` : ''));
  Object.assign(button.dataset, {warband, type, id, search: `${name}\n${subfaction}`.toLowerCase()});
  button.addEventListener('click', () => run(() => select(warband, type, id)));
  return button;
}

function renderTree() {
  const open = new Set([...treeEl.querySelectorAll('details[open]')].map((d) => d.dataset.key));
  const groups = new Map();
  treeEl.replaceChildren();
  for (const w of warbands.values()) {
    let parent = treeEl;
    if (w.group) {
      if (!groups.has(w.group)) {
        groups.set(w.group, details(`g:${w.group}`, w.group, open, 'group'));
        treeEl.append(groups.get(w.group));
      }
      parent = groups.get(w.group);
    }
    const warbandEl = details(`w:${w.id}`, w.name, open, 'warband');
    warbandEl.dataset.id = w.id;
    warbandEl.dataset.search = `${w.group}\n${w.name}`.toLowerCase();
    warbandEl.querySelector('summary').addEventListener('click', () => setContext(w.id));
    if (w.has_faction) warbandEl.append(nodeButton(w.id, 'factions', '', 'Faction', '', ''));
    for (const [type, items] of Object.entries(w.lists)) {
      const listEl = details(`l:${w.id}:${type}`, `${labelOf(type)} (${items.length})`, open, 'list');
      for (const item of items) {
        listEl.append(nodeButton(w.id, type, item._id, item.name, item.detail, item.subfaction));
      }
      warbandEl.append(listEl);
    }
    parent.append(warbandEl);
  }
  markSelection();
  applyFilter();
}

function setContext(warband) {
  contextWarband = warband;
  markSelection();
}

function markSelection() {
  for (const summary of treeEl.querySelectorAll('summary')) {
    summary.classList.toggle('context', summary.parentElement.dataset.id === contextWarband);
  }
  let selected = null;
  for (const node of treeEl.querySelectorAll('.node')) {
    const match = current !== null && !current.isNew && node.dataset.warband === current.warband
      && node.dataset.type === current.type && node.dataset.id === currentId();
    node.classList.toggle('selected', match);
    if (match) selected = node;
  }
  if (selected) {
    for (let d = selected.closest('details'); d; d = d.parentElement.closest('details')) d.open = true;
    selected.scrollIntoView({block: 'nearest'});
  }
}

function applyFilter() {
  const text = filterEl.value.trim().toLowerCase();
  for (const warbandEl of treeEl.querySelectorAll('details.warband')) {
    const warbandHit = !text || warbandEl.dataset.search.includes(text);
    let hits = 0;
    for (const node of warbandEl.querySelectorAll('.node')) {
      const visible = warbandHit || node.dataset.search.includes(text);
      node.hidden = !visible;
      if (visible) hits++;
    }
    if (text && !warbandHit) {
      for (const listEl of warbandEl.querySelectorAll('details.list')) {
        listEl.open = listEl.querySelector('.node:not([hidden])') !== null;
      }
      warbandEl.open = hits > 0;
    }
    warbandEl.hidden = !warbandHit && hits === 0;
  }
  for (const groupEl of treeEl.querySelectorAll('details.group')) {
    groupEl.hidden = !groupEl.querySelector('details.warband:not([hidden])');
    if (text && !groupEl.hidden) groupEl.open = true;
  }
}

// ---- Forms

function formBuilder() {
  const element = el('div', {class: 'form'});
  const inputs = {};
  const add = (label, control, focusable = control) => {
    focusable.id = `field-${++uid}`;
    element.append(el('label', {htmlFor: focusable.id}, label), control);
    return focusable;
  };
  return {
    element,
    inputs,
    info(label, value) {
      element.append(el('span', {class: 'info-label'}, label), el('span', {class: 'info'}, String(value ?? '')));
    },
    text(label, key, value) {
      inputs[key] = add(label, el('input', {class: 'wide', type: 'text', value: value ?? ''}));
    },
    int(label, key, value) {
      inputs[key] = add(label, el('input', {class: 'number', type: 'number', step: 1, value: value ?? ''}));
    },
    choice(label, key, value, options) {
      const choices = options.includes(value ?? '') ? options : [value, ...options];
      const select = el('select', {class: 'wide'}, ...choices.map((o) => el('option', {value: o}, o || '(none)')));
      select.value = value ?? '';
      inputs[key] = add(label, select);
    },
    textarea(label, key, value) {
      inputs[key] = add(label, el('textarea', {value: value ?? ''}));
    },
    checkbox(label, key, value) {
      inputs[key] = add(label, el('input', {type: 'checkbox', checked: Boolean(value)}));
    },
    rows(label, columns, items, defaults) {
      const table = rowTable(columns, items, defaults);
      element.append(el('span', {class: 'info-label'}, label), table.element);
      return table;
    },
  };
}

function rowTable(columns, items, defaults) {
  const body = el('tbody');
  const head = el('thead', {}, el('tr', {}, ...columns.map((c) => el('th', {}, c.label)), el('th')));
  const addRow = (values) => {
    const cells = columns.map((c) => {
      const input = c.kind === 'bool'
        ? el('input', {type: 'checkbox', checked: Boolean(values[c.key])})
        : c.kind === 'int'
          ? el('input', {class: 'number', type: 'number', step: 1, value: values[c.key] ?? ''})
          : el('input', {type: 'text', size: c.size, value: values[c.key] ?? ''});
      input.dataset.key = c.key;
      input.setAttribute('aria-label', c.label);
      return el('td', {}, input);
    });
    const remove = el('button', {type: 'button'}, 'Remove');
    const row = el('tr', {}, ...cells, el('td', {}, remove));
    remove.addEventListener('click', () => row.remove());
    body.append(row);
  };
  items.forEach(addRow);
  const add = el('button', {type: 'button'}, 'Add');
  add.addEventListener('click', () => addRow(defaults));
  return {
    element: el('div', {}, el('table', {class: 'rows'}, head, body), add),
    read() {
      return [...body.rows].map((row, i) => Object.fromEntries(columns.map((c) => {
        const input = row.querySelector(`[data-key="${c.key}"]`);
        if (c.kind === 'bool') return [c.key, input.checked];
        if (c.kind === 'int') return [c.key, readInt(input, `${c.label} in row ${i + 1}`)];
        return [c.key, input.value.trim()];
      })));
    },
  };
}

function fighterForm(fighter, warband) {
  const b = formBuilder();
  b.info('ID', fighter._id);
  b.text('Name', 'name', fighter.name);
  b.info('Warband', fighter.warband);
  b.info('Grand alliance', fighter.grand_alliance);
  b.choice('Subfaction', 'subfaction', fighter.subfaction ?? '', ['', ...warband.subfactions]);
  for (const stat of STATS) b.int(labelOf(stat), stat, fighter[stat]);
  b.text('Runemarks (comma separated)', 'runemarks', (fighter.runemarks ?? []).join(', '));
  const weapons = b.rows('Weapons', WEAPON_COLUMNS, fighter.weapons ?? [], {min_range: 0});
  return {
    element: b.element,
    read: () => ({
      name: b.inputs.name.value,
      subfaction: b.inputs.subfaction.value,
      ...Object.fromEntries(STATS.map((s) => [s, readInt(b.inputs[s], labelOf(s))])),
      weapons: weapons.read(),
      runemarks: readRunemarks(b.inputs.runemarks),
    }),
  };
}

function abilityForm(ability, warband) {
  const b = formBuilder();
  b.info('ID', ability._id);
  b.text('Name', 'name', ability.name);
  b.choice('Warband', 'warband', ability.warband, warband.ability_warbands);
  b.choice('Cost', 'cost', ability.cost, meta.ability_costs);
  b.text('Runemarks (comma separated)', 'runemarks', (ability.runemarks ?? []).join(', '));
  b.textarea('Description', 'description', ability.description);
  return {
    element: b.element,
    read: () => ({
      name: b.inputs.name.value,
      warband: b.inputs.warband.value,
      cost: b.inputs.cost.value,
      description: b.inputs.description.value,
      runemarks: readRunemarks(b.inputs.runemarks),
    }),
  };
}

function factionForm(faction) {
  const b = formBuilder();
  b.info('Warband', faction.warband);
  b.info('Grand alliance', faction.grand_alliance);
  for (const flag of FLAGS) b.checkbox(labelOf(flag), flag, faction[flag]);
  const subfactions = b.rows('Subfactions', SUBFACTION_COLUMNS, faction.subfactions ?? [], {});
  return {
    element: b.element,
    read: () => ({
      ...Object.fromEntries(FLAGS.map((f) => [f, b.inputs[f].checked])),
      subfactions: subfactions.read(),
    }),
  };
}

// ---- Editor

function currentId() {
  return current.type === 'factions' ? '' : current.entity._id;
}

function snapshot() {
  try {
    return JSON.stringify(current.read());
  } catch {
    return null;
  }
}

function isDirty() {
  return current !== null && (current.isNew || snapshot() !== current.baseline);
}

function confirmDiscard() {
  return !isDirty() || window.confirm('Discard the unsaved changes?');
}

function show(warband, type, entity, isNew) {
  const summary = warbands.get(warband);
  const form = type === 'fighters' ? fighterForm(entity, summary)
    : type === 'abilities' ? abilityForm(entity, summary)
      : factionForm(entity);
  editorEl.replaceChildren(...(isNew ? [el('span', {class: 'badge'}, 'New - not saved')] : []), form.element);
  current = {warband, type, entity, isNew, read: form.read, baseline: null};
  current.baseline = snapshot();
  history.replaceState(null, '', isNew ? location.pathname : `#${warband}/${type}/${currentId()}`);
  statusEl.textContent = `${isNew ? 'NEW - ' : ''}${fileLabel(warband, type)}`;
  setContext(warband);
}

function clearEditor() {
  current = null;
  editorEl.replaceChildren(el('p', {class: 'hint'}, 'Select a faction, fighter or ability.'));
  history.replaceState(null, '', location.pathname);
  markSelection();
}

async function select(warband, type, id) {
  if (current && current.warband === warband && current.type === type && currentId() === id) return;
  if (!confirmDiscard()) return;
  show(warband, type, await api('GET', '/api/entity', {warband, type, id}), false);
}

// ---- Actions

async function save() {
  if (!current) return;
  let edited;
  try {
    edited = current.read();
  } catch (error) {
    showMessage('Cannot save', error.message);
    return;
  }
  const {warband, type} = current;
  const saved = await api('PUT', '/api/entity', {warband, type, id: currentId()}, edited);
  show(warband, type, saved, false);
  await loadTree();
  statusEl.textContent = `Saved ${fileLabel(warband, type)}`;
}

async function newEntity(type) {
  if (!contextWarband) {
    showMessage(`New ${type}`, 'Select a warband first.');
    return;
  }
  if (!confirmDiscard()) return;
  show(contextWarband, type, await api('POST', '/api/new', {warband: contextWarband, type}), true);
}

async function duplicate() {
  if (!current || current.type === 'factions' || current.isNew) {
    showMessage('Duplicate', 'Select a saved fighter or ability.');
    return;
  }
  if (!confirmDiscard()) return;
  const {warband, type} = current;
  show(warband, type, await api('POST', '/api/duplicate', {warband, type, id: currentId()}), false);
  await loadTree();
}

async function deleteEntity() {
  if (!current || current.type === 'factions') {
    showMessage('Delete', 'Select a fighter or ability.');
    return;
  }
  if (!window.confirm(`Delete ${current.entity.name || 'this new item'}?`)) return;
  if (!current.isNew) await api('DELETE', '/api/entity', {warband: current.warband, type: current.type, id: currentId()});
  clearEditor();
  await loadTree();
}

function newWarband() {
  if (!confirmDiscard()) return;
  const dialog = $('warband-dialog');
  const fields = dialog.querySelector('form').elements;
  fields.grand_alliance.replaceChildren(...meta.grand_alliances.map((a) => el('option', {value: a}, a)));
  const group = warbands.get(contextWarband)?.group;
  if (meta.grand_alliances.includes(group)) fields.grand_alliance.value = group;
  fields.warband_name.value = '';
  dialog.showModal();
}

async function createWarband() {
  const fields = $('warband-dialog').querySelector('form').elements;
  const created = await api('POST', '/api/warband', {},
    {grand_alliance: fields.grand_alliance.value, name: fields.warband_name.value});
  current = null;
  await loadTree();
  await select(created.id, 'factions', '');
}

async function deleteWarband() {
  const warband = warbands.get(contextWarband);
  if (!warband || !warband.has_faction) {
    showMessage('Delete warband', 'Select a warband first.');
    return;
  }
  if (!window.confirm(`Delete ${warband.name} and every file in ${warband.id}?`)) return;
  await api('DELETE', '/api/warband', {warband: warband.id});
  if (current && current.warband === warband.id) clearEditor();
  contextWarband = '';
  await loadTree();
}

async function validateAll() {
  const {errors} = await api('GET', '/api/validate');
  if (errors.length) showMessage(`${errors.length} validation errors`, errors.join('\n'));
  else showMessage('Validate all', 'Validation passed.');
}

async function reload() {
  if (!confirmDiscard()) return;
  const previous = current && !current.isNew ? {...current, id: currentId()} : null;
  clearEditor();
  await loadTree();
  if (previous) await select(previous.warband, previous.type, previous.id).catch(() => clearEditor());
}

// ---- Start

$('save').addEventListener('click', () => run(save, 'Cannot save'));
$('new-fighter').addEventListener('click', () => run(() => newEntity('fighters')));
$('new-ability').addEventListener('click', () => run(() => newEntity('abilities')));
$('duplicate').addEventListener('click', () => run(duplicate));
$('delete').addEventListener('click', () => run(deleteEntity));
$('new-warband').addEventListener('click', newWarband);
$('delete-warband').addEventListener('click', () => run(deleteWarband));
$('validate').addEventListener('click', () => run(validateAll));
$('reload').addEventListener('click', () => run(reload));
filterEl.addEventListener('input', applyFilter);
$('warband-dialog').addEventListener('close', (event) => {
  if (event.target.returnValue === 'create') run(createWarband, 'Cannot create warband');
});
document.addEventListener('keydown', (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 's') {
    event.preventDefault();
    run(save, 'Cannot save');
  }
});
window.addEventListener('beforeunload', (event) => {
  if (isDirty()) event.preventDefault();
});

run(async () => {
  const parts = decodeURIComponent(location.hash.slice(1)).split('/');
  meta = await api('GET', '/api/meta');
  document.title = `Warcry data editor - ${meta.data}`;
  clearEditor();
  await loadTree();
  if (parts.length >= 3) {
    const id = parts.pop();
    const type = parts.pop();
    if (warbands.has(parts.join('/'))) await select(parts.join('/'), type, id);
  }
});
