import { RARITY_COLOR } from '../clothing/catalog.js';
import { PRESETS, SLIDERS, FACES, SKINS } from '../avatar/presets.js';

// DOM overlay UI — dark glass, neon gradients, zero framework.

const ui = () => document.getElementById('ui');
export function clearUI() { ui().innerHTML = ''; }

function el(tag, cls, html) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
}

// ---------------------------------------------------------------- main menu
export function showMenu({ onStart }) {
  clearUI();
  const s = el('div', 'screen fade');
  s.append(el('div', 'wordmark', 'FINAL FIT'));
  s.append(el('div', 'tagline', 'ANIME FASHION BATTLE · STYLE IS THE WEAPON'));
  const b = el('button', 'btn primary', 'ENTER THE FIT');
  b.style.marginTop = '34px';
  b.onclick = onStart;
  s.append(b);
  const note = el('div', 'tagline', 'WASD WALK · MOUSE CAMERA · E BROWSE · R PRESENT');
  note.style.marginTop = '18px'; note.style.fontSize = '11px';
  s.append(note);
  ui().append(s);
}

// ------------------------------------------------------------------ creator
export function showCreator(state, { onChange, onGo }) {
  clearUI();
  ui().append(el('div', '', '<div id="creator-title" class="fade">CHARACTER CREATOR</div>'));

  // left: presets, skin, face, hair
  const left = el('div', 'panel fade'); left.id = 'creator-left';
  left.append(el('h3', '', 'PRESETS'));
  const presetBtns = {};
  for (const [key, p] of Object.entries(PRESETS)) {
    const b = el('button', 'btn small preset-btn' + (state.preset === key ? ' active' : ''), p.name);
    b.onclick = () => {
      state.preset = key;
      state.body = null;           // reset to preset body
      state.faceKey = p.face;
      state.hairId = p.hair;
      onChange(true);
      refreshActive();
      sliderBox.refresh();
      faceCycler.refresh(); hairCycler.refresh();
    };
    presetBtns[key] = b;
    left.append(b);
  }
  const refreshActive = () => {
    for (const [k, b] of Object.entries(presetBtns))
      b.classList.toggle('active', state.preset === k);
  };

  left.append(el('h3', '', 'SKIN TONE'));
  const sw = el('div', 'swatches');
  SKINS.forEach((hexColor, i) => {
    const d = el('div', 'swatch' + (state.skin === i ? ' active' : ''));
    d.style.background = hexColor;
    d.onclick = () => {
      state.skin = i; onChange(true);
      sw.querySelectorAll('.swatch').forEach((x, j) => x.classList.toggle('active', j === i));
    };
    sw.append(d);
  });
  left.append(sw);

  const cycler = (title, getLabel, onCycle) => {
    left.append(el('h3', '', title));
    const row = el('div', 'cycler');
    const prev = el('button', 'btn small', '‹');
    const val = el('div', 'val', getLabel());
    const next = el('button', 'btn small', '›');
    prev.onclick = () => { onCycle(-1); val.textContent = getLabel(); };
    next.onclick = () => { onCycle(1); val.textContent = getLabel(); };
    row.append(prev, val, next);
    left.append(row);
    return { refresh: () => (val.textContent = getLabel()) };
  };

  const faceKeys = Object.keys(FACES);
  const faceCycler = cycler('FACE', () => FACES[state.faceKey].name, (d) => {
    const i = (faceKeys.indexOf(state.faceKey) + d + faceKeys.length) % faceKeys.length;
    state.faceKey = faceKeys[i];
    onChange(true);
  });
  const hairCycler = cycler('HAIR', () => state.hairName(), (d) => { state.cycleHair(d); onChange(true); });

  ui().append(left);

  // right: sliders
  const right = el('div', 'panel fade'); right.id = 'creator-right';
  right.append(el('h3', '', 'BODY SLIDERS'));
  const inputs = [];
  for (const [key, label, min, max] of SLIDERS) {
    const row = el('div', 'slider-row');
    const lab = el('label', '', label);
    const inp = el('input');
    inp.type = 'range'; inp.min = min; inp.max = max; inp.step = 0.01;
    inp.value = state.getBody()[key];
    inp.oninput = () => { state.getBody()[key] = parseFloat(inp.value); onChange(false); };
    row.append(lab, inp);
    right.append(row);
    inputs.push([key, inp]);
  }
  const sliderBox = {
    refresh() { for (const [key, inp] of inputs) inp.value = state.getBody()[key]; },
  };
  ui().append(right);

  const go = el('button', 'btn primary fade', 'ENTER THE STORE →');
  go.id = 'creator-go';
  go.onclick = onGo;
  ui().append(go);
}

// --------------------------------------------------------------------- HUD
export function buildHUD(themeName) {
  clearUI();
  const banner = el('div', 'panel fade'); banner.id = 'hud-banner';
  banner.innerHTML = `<span class="theme">ROUND THEME · ${themeName}</span><span id="hud-timer">10:00</span>`;
  ui().append(banner);

  const prompt = el('div', ''); prompt.id = 'hud-prompt';
  ui().append(prompt);

  const hint = el('div', ''); hint.id = 'hud-hint';
  hint.textContent = 'CLICK TO LOOK · WASD WALK · SHIFT SPRINT · E BROWSE · R PRESENT THE FIT';
  ui().append(hint);

  const fit = el('div', 'panel fade'); fit.id = 'fit-panel';
  fit.innerHTML = '<h3>YOUR FIT</h3><div id="fit-items"></div>';
  ui().append(fit);

  const timerEl = banner.querySelector('#hud-timer');
  return {
    setPrompt(t) { prompt.textContent = t || ''; },
    setTimer(seconds) {
      const m = Math.max(0, Math.floor(seconds / 60));
      const sec = Math.max(0, Math.floor(seconds % 60));
      timerEl.textContent = `${m}:${String(sec).padStart(2, '0')}`;
      timerEl.className = seconds <= 10 ? 'danger' : seconds <= 60 ? 'warn' : '';
      timerEl.id = 'hud-timer';
    },
    updateFit(equipped) {
      const box = fit.querySelector('#fit-items');
      if (equipped.size === 0) { box.innerHTML = '<div class="slot">nothing equipped — go raid the racks</div>'; return; }
      let html = '';
      for (const [slot, { item }] of equipped)
        html += `<div class="slot">${slot.toUpperCase()}</div>
                 <div class="item" style="color:${RARITY_COLOR[item.rarity]}">${item.name}</div>`;
      box.innerHTML = html;
    },
    hideForCinematic() {
      prompt.textContent = ''; hint.style.display = 'none';
      fit.style.display = 'none'; banner.style.display = 'none';
    },
  };
}

// ------------------------------------------------------------------ browse
export function openBrowse({ zone, items, isEquipped, onToggle, onClose }) {
  document.getElementById('browse')?.remove();
  const panel = el('div', 'panel fade'); panel.id = 'browse';
  panel.innerHTML = `<h2>${zone.toUpperCase()}</h2>
    <div class="sub">click a piece to equip it — drip shows instantly · E / ESC to close</div>
    <div id="browse-list"></div>`;
  const list = panel.querySelector('#browse-list');

  const render = () => {
    list.innerHTML = '';
    for (const item of items) {
      const card = el('div', 'card');
      card.style.setProperty('--rarity', RARITY_COLOR[item.rarity]);
      card.style.setProperty('--c1', '#' + item.c1.toString(16).padStart(6, '0'));
      card.style.setProperty('--c2', '#' + item.c2.toString(16).padStart(6, '0'));
      const on = isEquipped(item);
      card.innerHTML = `<div class="sw"></div>
        <div class="info">
          <div class="name">${item.name}</div>
          <div class="meta">${item.brand} · ${item.rarity.toUpperCase()} · $${item.price}</div>
        </div>`;
      const btn = el('button', 'btn small' + (on ? '' : ' primary'), on ? 'REMOVE' : 'EQUIP');
      btn.onclick = () => { onToggle(item); render(); };
      card.append(btn);
      list.append(card);
    }
  };
  render();

  const close = el('button', 'btn small', 'CLOSE [E]');
  close.style.marginTop = '10px';
  close.onclick = onClose;
  panel.append(close);
  ui().append(panel);

  return { close: () => panel.remove(), refresh: render };
}

// ----------------------------------------------------------------- results
export function showResults(result, { onStore, onMenu }) {
  document.getElementById('results')?.remove();
  const s = el('div', 'screen fade'); s.id = 'results';
  s.innerHTML = `
    <div class="tagline">THE JUDGES HAVE DECIDED</div>
    <div class="score-big">${result.total}</div>
    <div class="rank">RANK ${result.rank}</div>
    <div class="cats">${result.catLabels.map(([k, label]) =>
      `<div class="cat panel"><div class="v">${result.cats[k]}</div><div class="k">${label}</div></div>`).join('')}
    </div>
    <div class="comments">${result.comments.join('<br/>')}<br/><br/>
      <b>Strongest:</b> ${result.best} &nbsp;·&nbsp; <b>Weakest:</b> ${result.worst}<br/>
      <b>Tip:</b> ${result.tip}</div>`;
  const row = el('div', '');
  row.style.cssText = 'display:flex;gap:14px;margin-top:22px';
  const again = el('button', 'btn primary', 'BACK TO THE STORE');
  again.onclick = onStore;
  const menu = el('button', 'btn', 'MAIN MENU');
  menu.onclick = onMenu;
  row.append(again, menu);
  s.append(row);
  ui().append(s);
}
