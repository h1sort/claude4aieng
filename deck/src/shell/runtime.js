  (() => {
    /* Config inyectada por assemble.mjs (deck/src/shell/config.json) como window.DECK_CONFIG */
    const CFG = Object.assign({ topline:'Deck', who:'', url:'', urlLabel:'', channel:'deck', x:'', linkedin:'', handle:'' }, window.DECK_CONFIG || {});
    const params = new URLSearchParams(location.search);
    const root = document.documentElement;
    root.classList.remove('no-js');
    const still = params.get('still') === '1';
    const pub = 'public' in root.dataset;
    const presenter = !pub && params.get('presenter') === '1';
    if (still) root.dataset.still = '1';
    if (presenter) root.dataset.presenter = '1';
    const reduced = still || matchMedia('(prefers-reduced-motion: reduce)').matches;
    const slides = [...document.querySelectorAll('#deck > .slide')];
    const total = slides.length;
    const progress = document.getElementById('progress');
    const turn = document.getElementById('turn');
    const pad = n => String(n).padStart(2, '0');
    document.getElementById('slideCount').textContent = total;

    /* ---------- per-slide chrome, atmosphere, steps ---------- */
    slides.forEach((s, i) => {
      const atmo = document.createElement('div');
      atmo.className = 'atmo'; atmo.setAttribute('aria-hidden', 'true');
      atmo.innerHTML = '<div class="wash"></div><div class="grid"></div><div class="shaft"></div><div class="vignette"></div><div class="grain"></div>';
      s.prepend(atmo);
      const top = document.createElement('header');
      top.className = 'topline';
      top.innerHTML = '<span class="mark"><i></i><span class="mk"></span></span><span class="sec"></span>';
      top.querySelector('.mk').textContent = CFG.topline;
      top.querySelector('.sec').textContent = s.dataset.section || '';
      atmo.after(top);
      const bottom = document.createElement('footer');
      bottom.className = 'bottomline';
      const find = '<span class="find"><a class="deck-link" href="' + CFG.url + '">' + CFG.urlLabel + '</a><span class="sep">·</span>'
        + '<a href="' + CFG.x + '" target="_blank" rel="noopener" aria-label="X: @h1sort"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg></a>'
        + '<a href="' + CFG.linkedin + '" target="_blank" rel="noopener" aria-label="LinkedIn: h1sort"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.937 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.064 2.064 0 1 1 0-4.128 2.064 2.064 0 0 1 0 4.128zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0z"/></svg></a>'
        + '<span class="handle">' + CFG.handle + '</span></span>';
      bottom.innerHTML = '<span class="who"></span>' + find + '<span class="folio"></span>';
      bottom.querySelector('.who').textContent = CFG.who;
      bottom.querySelector('.folio').textContent = pad(i + 1) + ' / ' + pad(total);
      const notes = s.querySelector(':scope > .notes');
      s.insertBefore(bottom, notes || null);
      s.id = s.id || 'slide-' + (i + 1);
      s.setAttribute('aria-label', (i + 1) + ' de ' + total + ': ' + (s.dataset.title || ''));
      s.steps = reduced ? 0 : Math.max(0, ...[...s.querySelectorAll('[data-step]')].map(el => +el.dataset.step || 0));   /* reduced motion: no in-slide builds, everything visible */
      s.step = 0;
    });

    /* patterned strokes must not use pathLength (it rescales dash lengths and makes them look solid) */
    document.querySelectorAll(".dg .propose, .dg .return, .dg .rail, .dg .model, .dg .reach, .dg .node.ghost, .dg .node.mod").forEach(p => p.removeAttribute("pathLength"));

    /* ---------- diagram strokes: stagger draws, add pulses on executed paths ---------- */
    document.querySelectorAll('.dg').forEach(svg => {
      [...svg.querySelectorAll('.draw')].forEach((p, i) => { if (!p.style.animationDelay) p.style.animationDelay = (0.15 + i * 0.09).toFixed(2) + 's'; });
      if (reduced) return;
      svg.querySelectorAll('.exec.flow').forEach((p, i) => {
        const pulse = p.cloneNode(false);
        pulse.setAttribute('class', 'pulse');
        pulse.removeAttribute('marker-end'); pulse.removeAttribute('marker-start');
        pulse.style.animationDelay = (1.4 + i * 0.35).toFixed(2) + 's';
        const step = p.closest('[data-step]');
        p.after(pulse);
        pulse.dataset.flowStep = step ? step.dataset.step : '0';
      });
    });

    /* elements are "on" (draw animations run) when the slide is active and their step is reached */
    const applyStep = s => {
      s.querySelectorAll('[data-step]').forEach(el => el.classList.toggle('shown', reduced || +el.dataset.step <= s.step));
      s.querySelectorAll('.draw, .pulse').forEach(el => {
        const host = el.closest('[data-step]');
        el.classList.toggle('on', reduced || !host || +host.dataset.step <= s.step);
      });
    };

    /* ---------- navigation ---------- */
    let current = -1;
    const channel = 'BroadcastChannel' in window ? new BroadcastChannel(CFG.channel) : null;
    const sweep = () => {
      if (reduced) return;
      turn.classList.remove('on'); void turn.offsetWidth; turn.classList.add('on');
    };
    const show = (i, step, opts = {}) => {
      i = Math.max(0, Math.min(total - 1, i));
      const changed = i !== current;
      if (changed && current >= 0 && !opts.instant) sweep();
      slides.forEach((s, k) => s.classList.toggle('active', k === i));
      current = i;
      const s = slides[i];
      s.step = Math.max(0, Math.min(s.steps, step));
      applyStep(s);
      progress.style.width = ((i + 1) / total) * 100 + '%';
      if (!still && !presenter) history.replaceState(null, '', '?slide=' + (i + 1) + (s.step ? '&step=' + s.step : ''));
      renderNotes();
      if (channel && !opts.remote) channel.postMessage({ slide: i, step: s.step });
    };
    const next = () => { const s = slides[current]; s.step < s.steps ? show(current, s.step + 1) : current < total - 1 && show(current + 1, 0); };
    const prev = () => { const s = slides[current]; s.step > 0 ? show(current, s.step - 1) : current > 0 && show(current - 1, slides[current - 1].steps); };

    /* ---------- overlays ---------- */
    const notesPanel = document.getElementById('notesPanel');
    const toggle = (id, force) => {
      const el = document.getElementById(id);
      const open = force ?? !el.classList.contains('open');
      el.classList.toggle('open', open);
      if (open) el.focus();
      return open;
    };
    const anyOpen = () => document.querySelector('.overlay.open');
    function renderNotes() {
      const s = slides[current];
      const n = s.querySelector(':scope > .notes');
      const html = '<button class="close" type="button" data-act="notes">CERRAR</button>'
        + '<h4>' + pad(current + 1) + ' · ' + (s.dataset.title || '') + '</h4>'
        + '<div class="meta">' + (s.dataset.budget ? 'Tiempo: ' + s.dataset.budget : '') + (s.dataset.clock ? ' · Reloj: ' + s.dataset.clock : '') + (s.steps ? ' · Paso ' + s.step + '/' + s.steps : '') + '</div>'
        + (n ? n.innerHTML : '<p>Sin notas.</p>');
      notesPanel.innerHTML = html;
      if (presenter) renderPresenter();
    }
    let t0 = null;
    function renderPresenter() {
      const s = slides[current], nx = slides[current + 1];
      const p = document.getElementById('presenter');
      const n = s.querySelector(':scope > .notes');
      p.innerHTML = '<div><div class="label">Ahora · ' + pad(current + 1) + '/' + pad(total) + (s.steps ? ' · paso ' + s.step + '/' + s.steps : '') + '</div><div class="now">' + (s.dataset.title || '') + '</div><p class="label">' + (s.dataset.budget || '') + ' · ' + (s.dataset.clock || '') + '</p></div>'
        + '<div><div class="clock" id="pclock">00:00</div><p class="next">Siguiente: ' + (nx ? nx.dataset.title : '— fin —') + '</p><p class="label">← → navegan ambas ventanas · R reinicia el reloj</p></div>'
        + '<div class="pnotes">' + (n ? n.innerHTML : '') + '</div>';
      tick();
    }
    function tick() {
      const el = document.getElementById('pclock'); if (!el || t0 === null) return;
      const sec = Math.floor((Date.now() - t0) / 1000);
      el.textContent = pad(Math.floor(sec / 60)) + ':' + pad(sec % 60);
    }
    if (presenter) { t0 = Date.now(); setInterval(tick, 1000); }
    if (channel) channel.onmessage = e => { if (e.data && Number.isInteger(e.data.slide)) show(e.data.slide, e.data.step, { remote: true, instant: true }); };

    const act = a => {
      if (a === 'notes') toggle('notesPanel');
      if (a === 'help') toggle('helpPanel');
      if (a === 'sources') toggle('sourcesPanel');
      if (a === 'full') { document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen?.().catch(() => {}); }
      if (a === 'presenter') window.open(location.pathname + '?presenter=1&slide=' + (current + 1), 'presenter', 'width=1100,height=760');
    };
    document.addEventListener('click', e => { const b = e.target.closest('[data-act]'); if (b) act(b.dataset.act); });

    addEventListener('keydown', e => {
      const t = e.target;
      if (t && (t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === 'Escape') { document.querySelectorAll('.overlay.open').forEach(o => o.classList.remove('open')); return; }
      const k = e.key.toLowerCase();
      if (pub && (k === 'n' || k === 'p' || k === '?' || k === 'h')) return;
      if (k === 'n') return act('notes');
      if (k === 's') return act('sources');
      if (k === '?' || k === 'h') return act('help');
      if (k === 'f') return act('full');
      if (k === 'p') return act('presenter');
      if (k === 'r' && presenter) { t0 = Date.now(); return tick(); }
      if (still && !presenter) return;
      /* while an overlay is open, let it scroll with arrows/space */
      if (anyOpen() && ['ArrowDown', 'ArrowUp', ' ', 'PageDown', 'PageUp'].includes(e.key)) return;
      if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].includes(e.key)) { e.preventDefault(); next(); }
      else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(e.key)) { e.preventDefault(); prev(); }
      else if (e.key === 'Home') { e.preventDefault(); show(0, 0); }
      else if (e.key === 'End') { e.preventDefault(); show(total - 1, 0); }
    });

    if (!still && !presenter) {
      let locked = false, lockedAt = 0, idle = null, startX = 0, startY = 0;
      addEventListener('wheel', e => {
        if (e.target.closest('.overlay')) return;          /* notes/sources stay scrollable */
        e.preventDefault();
        /* one step per gesture: stay locked until trackpad inertia has been quiet for 220ms (min 650ms) */
        clearTimeout(idle);
        idle = setTimeout(() => { if (Date.now() - lockedAt > 650) locked = false; else setTimeout(() => locked = false, 650 - (Date.now() - lockedAt)); }, 220);
        if (locked || Math.abs(e.deltaY) + Math.abs(e.deltaX) < 14) return;
        locked = true; lockedAt = Date.now();
        (e.deltaY || e.deltaX) > 0 ? next() : prev();
      }, { passive: false });
      addEventListener('touchstart', e => { if (e.target.closest('.overlay')) return; startX = e.touches[0].clientX; startY = e.touches[0].clientY; }, { passive: true });
      addEventListener('touchend', e => {
        if (e.target.closest('.overlay')) return;
        const dx = startX - e.changedTouches[0].clientX, dy = startY - e.changedTouches[0].clientY;
        const d = Math.abs(dx) > Math.abs(dy) ? dx : dy;
        if (Math.abs(d) > 45) d > 0 ? next() : prev();
      }, { passive: true });
    }

    /* ---------- initial position ---------- */
    const req = Number.parseInt(params.get('slide'), 10);
    const reqStep = params.get('step') === 'all' ? 99 : Number.parseInt(params.get('step'), 10) || 0;
    const start = Number.isInteger(req) ? req - 1 : 0;
    if (still) {
      if (Number.isInteger(req)) root.dataset.solo = '1';
      slides.forEach(s => { s.step = s.steps; applyStep(s); });
    }
    show(start, still ? 99 : reqStep, { instant: true });
    if (still) slides.forEach(s => { if (!root.dataset.solo) s.classList.add('active'); });
  })();
  
