/* RhemaFlow web - the page. All decisions live in core.js (tested in Node). */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const VERSION = 'RhemaFlow Web 0.2';
  const PD_BASE = 'https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/json';
  const PD = [['ASV', 'American Standard Version (1901)'], ['YLT', "Young's Literal (1898)"], ['Darby', 'Darby (1890)'], ['BBE', 'Bible in Basic English'], ['Webster', "Webster's (1833)"], ['AKJV', 'American KJV']];
  const IS_STAGE = location.hash === '#stage';
  const S = {
    kjv: null, idx: null, versions: {}, translation: 'KJV', stage: { kind: 'blank', label: '', text: '', translation: 'KJV', passage: null },
    seq: 0, blackout: false, zoom: 1, style: 'classic', live: false, start: null, lines: [], cites: [], cards: [], nextCard: 1, history: [],
    plan: [], planPos: 0, autoApprove: false, showAll: true, autoRead: false, lang: 'en-US', title: '', church: '', saveSrt: true, saveMd: true, saveRec: true,
    autoStaged: 0, approved: 0, dismissed: 0, br: { book: 0, chapter: 1, anchor: null, scroll: true, lastSeq: 0, query: '', visible: true },
    speaking: false, echoUntil: 0, stageWin: null, chunks: [], recorder: null, rec: null, timer: null,
  };
  const chan = 'BroadcastChannel' in window ? new BroadcastChannel('rhemaflow') : null;

  // ------------------------------------------------------------- tiny helpers
  let toastT;
  function toast(msg, ms) { const t = $('toast'); t.textContent = msg; t.classList.add('show'); clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove('show'), ms || 2800); }
  let flashT;
  function flash(msg) { const f = $('cmdflash'); if (!f) return; f.textContent = '\u25b6 ' + msg; f.classList.add('show'); clearTimeout(flashT); flashT = setTimeout(() => f.classList.remove('show'), 1400); }
  function save() { try { localStorage.setItem('rf.settings', JSON.stringify({ translation: S.translation, zoom: S.zoom, style: S.style, autoApprove: S.autoApprove, showAll: S.showAll, autoRead: S.autoRead, lang: S.lang, title: S.title, church: S.church, saveSrt: S.saveSrt, saveMd: S.saveMd, saveRec: S.saveRec, brVisible: S.br.visible })); } catch (e) { /* private mode */ } }
  function load() { try { Object.assign(S, JSON.parse(localStorage.getItem('rf.settings') || '{}')); if (S.brVisible !== undefined) { S.br.visible = S.brVisible; } } catch (e) { /* ignore */ } }
  const bibleNow = () => S.versions[S.translation] || S.kjv;
  const label = (p) => RF.passageLabel(S.kjv, p);
  const serviceMs = () => (S.live && S.start ? Date.now() - S.start.getTime() : 0);

  // ------------------------------------------------------------- stage drawing (preview, stage window)
  function drawStage(root, st, opts) {
    root.className = 'stage ' + opts.style + (opts.blackout ? ' blackout' : '');
    const box = root.querySelector('.box'), txt = root.querySelector('.txt'), ref = root.querySelector('.ref');
    if (st.kind !== 'scripture') { box.style.opacity = 0; return; }
    txt.textContent = st.text; ref.textContent = st.label + ' \u2014 ' + st.translation;
    box.style.opacity = opts.blackout ? 0 : 1;
    const W = root.clientWidth || 640, H = root.clientHeight || 360, len = st.text.length;
    const lower = opts.style === 'lower', large = opts.style === 'large';
    let size = Math.min(W, H * 1.4) / (len > 180 ? 22 : len > 90 ? 17 : 13) * opts.zoom * (large ? 1.35 : 1) * (lower ? 0.55 : 1);
    box.style.fontSize = size + 'px';
    for (let i = 0; i < 14 && box.scrollHeight > box.clientHeight + 1 && size > 9; i++) { size *= 0.92; box.style.fontSize = size + 'px'; }
  }
  function render() {
    drawStage($('prev'), S.stage, { style: S.style, zoom: S.zoom, blackout: S.blackout });
    $('zoom').value = Math.round(S.zoom * 100); $('zpct').textContent = Math.round(S.zoom * 100) + '%';
    $('bBlack').classList.toggle('on', S.blackout);
    $('bStop').disabled = !S.speaking;
    chan && chan.postMessage({ t: 'state', stage: S.stage, style: S.style, zoom: S.zoom, blackout: S.blackout });
  }

  // ------------------------------------------------------------- staging
  function passageText(p) {
    const b = bibleNow();
    let t = b.passage(p.book, p.chapter, p.from, p.to);
    if (!t && b !== S.kjv) t = S.kjv.passage(p.book, p.chapter, p.from, p.to);
    return t;
  }
  function stagePassage(p, source, chapterOnly) {
    if (!p.chapter) return;
    const text = passageText(p); if (!text) return;
    S.stage = { kind: 'scripture', label: label(p), text, translation: S.translation, passage: { book: p.book, chapter: p.chapter, from: p.from, to: p.to }, chapterOnly: !!chapterOnly };
    S.seq++; S.blackout = false;
    const l = S.stage.label; S.history = S.history.filter((h) => h.label !== l); S.history.unshift({ label: l, p: S.stage.passage }); S.history.length = Math.min(S.history.length, 14);
    S.cites.push({ ms: serviceMs(), label: l, source, text });
    // drop pending cards for the same passage
    S.cards = S.cards.filter((c) => !(c.book === p.book && c.chapter === p.chapter && c.from === p.from));
    renderCards(); render(); renderRecent(); followStage();
    if (S.autoRead) speak();
  }
  function setTranslation(name) {
    S.translation = name; save(); fillTranslations();
    const p = S.stage.passage;
    if (S.stage.kind === 'scripture' && p) { const text = passageText(p); if (text) { S.stage.text = text; S.stage.translation = name; S.seq++; } }
    render(); renderBrowser();
  }
  function nav(kind) {
    const p = S.stage.passage; if (S.stage.kind !== 'scripture' || !p) { toast('Nothing on the stage yet \u2014 say or click a verse first'); return; }
    const k = S.kjv; let { book, chapter, to } = p, v = to;
    if (kind === 'next_verse') { v++; if (v > k.verseCount(book, chapter)) { v = 1; chapter++; if (chapter > k.chapterCount(book)) { book = (book + 1) % 66; chapter = 1; } } stagePassage({ book, chapter, from: v, to: v }, 'nav'); }
    else if (kind === 'prev_verse') { v = p.from - 1; if (v < 1) { chapter--; if (chapter < 1) { book = (book + 65) % 66; chapter = k.chapterCount(book); } v = k.verseCount(book, chapter); } stagePassage({ book, chapter, from: v, to: v }, 'nav'); }
    else if (kind === 'next_chapter') { chapter++; if (chapter > k.chapterCount(book)) { book = (book + 1) % 66; chapter = 1; } stagePassage({ book, chapter, from: 1, to: 1 }, 'nav', true); }
    else if (kind === 'prev_chapter') { chapter--; if (chapter < 1) { book = (book + 65) % 66; chapter = k.chapterCount(book); } stagePassage({ book, chapter, from: 1, to: 1 }, 'nav', true); }
  }
  function clearStage() { S.stage = { kind: 'blank', label: '', text: '', translation: S.translation, passage: null }; S.seq++; render(); }
  function setZoom(pct) { S.zoom = Math.max(0.6, Math.min(4, pct / 100)); save(); render(); }

  // ------------------------------------------------------------- commands (voice, keys, buttons)
  function run(name) {
    if (/^zoom_\d+$/.test(name)) return setZoom(parseInt(name.slice(5), 10));
    switch (name) {
      case 'next_verse': case 'prev_verse': case 'next_chapter': case 'prev_chapter': return nav(name);
      case 'first_verse': if (S.stage.passage) stagePassage({ ...S.stage.passage, from: 1, to: 1 }, 'nav'); return;
      case 'last': if (S.history[0]) stagePassage(S.history[0].p, 'nav'); return;
      case 'clear': return clearStage();
      case 'blackout': S.blackout = !S.blackout; return render();
      case 'zoom_in': return setZoom(S.zoom * 100 + 20);
      case 'zoom_out': return setZoom(S.zoom * 100 - 20);
      case 'approve': return approveFirst();
      case 'dismiss': return dismissFirst();
      case 'pick_1': case 'pick_2': case 'pick_3': case 'pick_4': case 'pick_5': return pickMatch(parseInt(name.slice(5), 10));
      case 'plan_next': return planNext();
      case 'read': return speak();
      case 'stop_reading': return stopSpeaking();
      case 'auto_on': S.autoApprove = true; $('autoApprove').checked = true; save(); return toast('auto-approve ON');
      case 'auto_off': S.autoApprove = false; $('autoApprove').checked = false; save(); return toast('auto-approve OFF');
      case 'open_stage': return openStage();
      case 'close_stage': return closeStage();
      case 'fullscreen': if (!openStage()) toast('Browsers need a click for full screen: click the stage window and press F', 4500); else toast('Click the stage window and press F for full screen', 4500); return;
      case 'exit_fullscreen': if (document.fullscreenElement) document.exitFullscreen(); chan && chan.postMessage({ t: 'exitfs' }); return;
      case 'help': $('dlgHelp').showModal(); return;
      default:
    }
  }
  function openStage() {
    if (S.stageWin && !S.stageWin.closed) { S.stageWin.focus(); return true; }
    const w = window.open(location.pathname + '#stage', 'rf-stage', 'width=960,height=540');
    if (!w) { toast('The browser blocked the stage window. Click "Open stage" (popups must be allowed).', 4500); return false; }
    S.stageWin = w; $('bStage').textContent = 'Close stage'; return true;
  }
  function closeStage() { if (S.stageWin && !S.stageWin.closed) S.stageWin.close(); S.stageWin = null; $('bStage').textContent = 'Open stage'; }

  // ------------------------------------------------------------- review cards
  function cardTitle(c) { return label({ book: c.book, chapter: c.chapter, from: c.from, to: c.to }); }
  function addCard(c) {
    if (c.kind === 'book' && S.cards.some((x) => x.kind === 'book' && x.book === c.book)) return;
    if (S.cards.some((x) => x.kind === c.kind && x.book === c.book && x.chapter === c.chapter && x.from === c.from)) return;
    c.id = S.nextCard++; S.cards.push(c); renderCards();
  }
  function renderCards() {
    const el = $('cards'); el.textContent = '';
    if (!S.cards.length) { el.innerHTML = '<div class="muted">Nothing needs review.<br>Clear detections are staged automatically.</div>'; return; }
    for (const c of S.cards) {
      const d = document.createElement('div'); d.className = 'card';
      const kind = c.kind === 'quote' ? 'POSSIBLE QUOTATION' : c.kind === 'book' ? 'BOOK ONLY' : c.kind === 'chapter' ? 'CHAPTER ONLY' : 'CONFIRM';
      d.innerHTML = `<div class="k">${kind}</div><div class="big"></div><div class="muted small"></div>`;
      d.querySelector('.big').textContent = c.kind === 'book' ? RF.passageLabel(S.kjv, { book: c.book, chapter: 0 }) : cardTitle(c);
      d.querySelector('.small').textContent = c.note || '';
      if (c.kind === 'quote') {
        const rows = [{ book: c.book, chapter: c.chapter, from: c.from, to: c.to, pct: c.pct }, ...(c.alts || [])];
        const sh = S.showAll ? rows : rows.slice(0, 1);
        sh.forEach((r, i) => {
          const b = document.createElement('button'); b.className = 'alt' + (i === 0 ? ' top' : ''); b.textContent = `${i + 1}.  ${cardTitle(r)}   ${r.pct}%`;
          b.onclick = () => { S.approved++; stagePassage(r, 'quotation'); removeCard(c.id); }; d.appendChild(b);
        });
        if (!S.showAll && rows.length > 1) { const m = document.createElement('div'); m.className = 'muted small'; m.textContent = `+${rows.length - 1} more hidden (turn on "show all matches")`; d.appendChild(m); }
        const sn = document.createElement('div'); sn.className = 'snip'; sn.textContent = S.kjv.passage(c.book, c.chapter, c.from, c.to).slice(0, 150); d.appendChild(sn);
      }
      const row = document.createElement('div'); row.className = 'bar';
      if (c.chapter > 0 && c.kind !== 'quote') { const a = document.createElement('button'); a.className = 'go'; a.textContent = 'Approve'; a.onclick = () => approveCard(c); row.appendChild(a); }
      if (c.kind === 'book') { const o = document.createElement('button'); o.textContent = 'Open book'; o.onclick = () => { S.br.book = c.book; S.br.chapter = 1; S.br.scroll = true; renderBrowser(); removeCard(c.id); }; row.appendChild(o); }
      const x = document.createElement('button'); x.className = 'no'; x.textContent = 'Dismiss'; x.onclick = () => { S.dismissed++; removeCard(c.id); }; row.appendChild(x);
      d.appendChild(row); el.appendChild(d);
    }
  }
  function removeCard(id) { S.cards = S.cards.filter((c) => c.id !== id); renderCards(); }
  function approveCard(c) { S.approved++; stagePassage(c, c.kind === 'quote' ? 'quotation' : 'confirm', c.kind === 'chapter'); removeCard(c.id); }
  const firstReviewable = () => S.cards.find((c) => c.chapter > 0);
  function approveFirst() { const c = firstReviewable(); if (c) approveCard(c); else if (S.plan.length) planNext(); }
  function dismissFirst() { if (S.cards.length) { S.dismissed++; S.cards.shift(); renderCards(); } }
  function pickMatch(n) { const c = firstReviewable(); if (!c) return; const rows = c.kind === 'quote' ? [c, ...(c.alts || [])] : [c]; const r = rows[n - 1]; if (r) { S.approved++; stagePassage(r, 'quotation'); removeCard(c.id); } }

  // ------------------------------------------------------------- one utterance
  function addLine(text) {
    const ms = serviceMs(); S.lines.push({ ms, text });
    const d = document.createElement('div'); d.className = 'line';
    d.innerHTML = '<span class="t"></span><span class="w"></span>'; d.firstChild.textContent = RF.hms(ms).slice(3); d.lastChild.textContent = text;
    const box = $('lines'); if (S.lines.length === 1) box.textContent = ''; box.appendChild(d); $('left').scrollTop = 1e9;
    try { localStorage.setItem('rf.live', JSON.stringify({ start: S.start.getTime(), title: S.title, church: S.church, lines: S.lines, cites: S.cites, translation: S.translation })); } catch (e) { /* full */ }
  }
  function handleFinal(text, already) {
    already = already || [];
    text = String(text || '').trim(); if (!text) return;
    if (Date.now() < S.echoUntil || S.speaking) { if (RF.isBareStop(text) || RF.matchCommands(text, false).includes('stop_reading')) stopSpeaking(); return; } // the mic hears our own voice
    if (RF.isBareStop(text)) { if (S.speaking) { stopSpeaking(); return; } }
    addLine(text);
    const r = RF.interpret(S.kjv, S.idx, text, S.stage.passage ? { last: S.stage.passage } : null, { floor: 0.75, autoApprove: S.autoApprove });
    let result = [];
    for (const c of r.commands) { if (already.includes(c)) { result.push(RF.cmdLabel(c)); continue; } run(c); flash(RF.cmdLabel(c)); result.push(RF.cmdLabel(c)); }
    for (const d of r.stage) { stagePassage(d, d.kind === 'quote' ? 'quotation (auto)' : 'voice'); if (d.kind === 'quote') S.autoStaged++; else if (d.conf >= 0.75) S.autoStaged++; result.push(cardTitle(d)); }
    for (const c of r.cards) { addCard(c); result.push('review: ' + (c.kind === 'book' ? S.kjv.names[c.book] : cardTitle(c))); }
    for (const e of r.errors) result.push(e);
    $('heardTxt').textContent = `\u201c${text}\u201d \u2192 ${result.join(', ') || 'no scripture or command'}`;
  }
  window.__rf = { handleFinal, S, RF }; // test hook

  // ------------------------------------------------------------- speech in
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  // Interim (unfinished) results arrive ~1 s before the final one. A command made only of command words
  // ("next verse") is acted on once the interim text has been STABLE for 450 ms, so "next" can still
  // become "next chapter" first. The final result then skips what was already done. Scripture is never
  // staged from interim text.
  const pending = {}, fired = {};
  function interimCommand(idx, text) {
    const cmds = RF.pureCommands(text);
    clearTimeout(pending[idx]);
    if (!cmds.length || (fired[idx] && fired[idx].text === text)) return;
    pending[idx] = setTimeout(() => {
      if (Date.now() < S.echoUntil || S.speaking) return;
      fired[idx] = { text, cmds };
      cmds.forEach((c) => { run(c); flash(RF.cmdLabel(c)); });
    }, 450);
  }
  function startListening() {
    if (!SR) { $('sttNote').textContent = 'This browser has no speech recognition. Use Chrome, Edge or Safari, or type in the search box.'; return; }
    S.rec = new SR(); S.rec.continuous = true; S.rec.interimResults = true; S.rec.lang = S.lang; S.rec.maxAlternatives = 1;
    S.rec.onresult = (e) => {
      let interim = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i], t = r[0].transcript;
        if (r.isFinal) { clearTimeout(pending[i]); const done = fired[i] ? fired[i].cmds : []; delete fired[i]; handleFinal(t, done); }
        else { interim += t; interimCommand(i, t); }
      }
      $('interim').textContent = interim;
    };
    S.rec.onerror = (e) => {
      const note = $('sttNote'); note.className = 'small warn';
      if (e.error === 'not-allowed' || e.error === 'service-not-allowed') { note.textContent = location.protocol === 'file:' ? 'The browser refused the microphone because this page was opened as a file. Serve it instead: run  python3 -m http.server 8000  in the web folder and open http://localhost:8000/rhemaflow-app.html' : 'Microphone blocked. Allow it in the browser address bar, then Start again.'; S.listening = false; }
      else if (e.error === 'network') note.textContent = 'Speech recognition needs internet in this browser (it uses the vendor\u2019s service).';
      else if (e.error !== 'no-speech' && e.error !== 'aborted') note.textContent = 'speech: ' + e.error;
    };
    S.rec.onend = () => { Object.keys(pending).forEach((k) => clearTimeout(pending[k])); Object.keys(fired).forEach((k) => delete fired[k]); if (S.live && S.listening !== false) setTimeout(() => { try { S.rec.start(); } catch (e) { /* already started */ } }, 200); };
    S.listening = true; try { S.rec.start(); } catch (e) { /* ignore */ }
    $('sttNote').textContent = ''; $('sttNote').className = 'muted small';
  }
  function stopListening() { S.listening = false; try { S.rec && S.rec.stop(); } catch (e) { /* ignore */ } }

  // ------------------------------------------------------------- speech out
  function speak() {
    if (!('speechSynthesis' in window) || S.stage.kind !== 'scripture') return;
    stopSpeaking();
    const u = new SpeechSynthesisUtterance(S.stage.text + '. ' + S.stage.label);
    u.onstart = () => { S.speaking = true; render(); };
    u.onend = u.onerror = () => { S.speaking = false; S.echoUntil = Date.now() + 1500; render(); };
    S.speaking = true; window.speechSynthesis.speak(u); render();
  }
  function stopSpeaking() { if ('speechSynthesis' in window) window.speechSynthesis.cancel(); S.speaking = false; S.echoUntil = Date.now() + 800; render(); }

  // ------------------------------------------------------------- service, recording, saving
  async function startService() {
    if (S.live) return;
    S.live = true; S.start = new Date(); S.lines = []; S.cites = []; S.cards = []; S.autoStaged = S.approved = S.dismissed = 0; S.chunks = [];
    $('lines').innerHTML = '<span class="muted">listening&hellip;</span>'; renderCards();
    $('btnStart').textContent = '\u25a0 End service'; $('btnStart').className = 'no'; $('chipState').textContent = 'LIVE'; $('chipState').className = 'chip live';
    $('clock').className = ''; $('clock').textContent = '00:00'; $('sttNote').textContent = '';
    S.timer = setInterval(() => { $('clock').textContent = RF.hms(serviceMs()).replace(/^00:/, ''); }, 500);
    startListening();
    if (S.saveRec && navigator.mediaDevices && window.MediaRecorder) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true }); S.stream = stream;
        const mime = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/webm'].find((m) => MediaRecorder.isTypeSupported(m));
        S.recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined); S.recMime = S.recorder.mimeType;
        S.recorder.ondataavailable = (e) => { if (e.data && e.data.size) S.chunks.push(e.data); };
        S.recorder.start(2000); $('chipRec').hidden = false;
      } catch (e) { toast('Recording unavailable: ' + e.message, 4000); }
    }
  }
  async function endService() {
    if (!S.live) return;
    const end = new Date(), duration = serviceMs() || end - S.start;
    S.live = false; stopListening(); stopSpeaking(); clearInterval(S.timer);
    $('clock').textContent = 'ended ' + RF.hms(duration).replace(/^00:/, ''); $('clock').className = 'ended'; $('sttNote').textContent = '';
    let recBlob = null;
    if (S.recorder && S.recorder.state !== 'inactive') { await new Promise((res) => { S.recorder.onstop = res; S.recorder.stop(); }); }
    if (S.stream) S.stream.getTracks().forEach((t) => t.stop());
    if (S.chunks.length) recBlob = new Blob(S.chunks, { type: S.recMime || 'audio/webm' });
    $('chipRec').hidden = true; $('btnStart').textContent = '\u25b6 Start service'; $('btnStart').className = 'go'; $('chipState').textContent = 'IDLE'; $('chipState').className = 'chip';
    showSaved(S.start, end, duration, recBlob, S.lines, S.cites);
    try { localStorage.removeItem('rf.live'); } catch (e) { /* ignore */ }
  }
  function showSaved(start, end, duration, recBlob, lines, cites, titleOverride) {
    const title = titleOverride !== undefined ? titleOverride : S.title, base = RF.finalBase(start, end, title);
    const ext = recBlob ? (/mp4/.test(recBlob.type) ? 'm4a' : 'webm') : '';
    const meta = { title, church: S.church, version: VERSION, start, end, duration, translation: S.translation, engine: SR ? 'Browser Web Speech API' : 'none', mic: '', recording: recBlob ? `${base} - recording.${ext}` : '', autoStaged: S.autoStaged, approved: S.approved, dismissed: S.dismissed };
    const files = [[`${base} - transcript.txt`, new Blob([RF.toTxt(meta, lines, cites)], { type: 'text/plain' })]];
    if (S.saveSrt) files.push([`${base} - transcript.srt`, new Blob([RF.toSrt(lines, duration)], { type: 'text/plain' })]);
    if (S.saveMd) files.push([`${base} - sermon notes.md`, new Blob([RF.toMarkdown(meta, lines, cites)], { type: 'text/markdown' })]);
    if (recBlob) files.push([`${base} - recording.${ext}`, recBlob]);
    const box = $('savedLinks'); box.textContent = '';
    S.savedFiles = files.map(([name, blob]) => { const a = document.createElement('a'); a.className = 'dl'; a.href = URL.createObjectURL(blob); a.download = name; a.textContent = `${name}  (${Math.max(1, Math.round(blob.size / 1024))} KB)`; box.appendChild(a); return a; });
    $('savedNote').textContent = `${RF.folderName(start)} \u2014 files go to your browser's Downloads folder. Tip: put them in a folder named "${RF.folderName(start)}".`;
    $('dlgSaved').showModal();
  }
  $('dlAll').onclick = () => { (S.savedFiles || []).forEach((a, i) => setTimeout(() => a.click(), i * 400)); };

  // ------------------------------------------------------------- scripture browser
  function followStage() {
    const b = S.br; if (b.lastSeq === S.seq) return; b.lastSeq = S.seq;
    const p = S.stage.passage; if (S.stage.kind === 'scripture' && p) { b.book = p.book; b.chapter = p.chapter; b.anchor = p.from; b.scroll = true; b.query = ''; $('q').value = ''; }
    renderBrowser();
  }
  function renderRecent() { const el = $('recent'); el.textContent = ''; if (!S.history.length) return; const l = document.createElement('span'); l.className = 'muted small'; l.textContent = 'recent'; el.appendChild(l); S.history.slice(0, 10).forEach((h) => { const b = document.createElement('button'); b.textContent = h.label; b.onclick = () => stagePassage(h.p, 'browser'); el.appendChild(b); }); }
  function renderBrowser() {
    $('browser').classList.toggle('hidden', !S.br.visible); $('bBrowser').textContent = S.br.visible ? 'Hide scripture' : 'Show scripture';
    if (!S.br.visible) return;
    const b = S.br, bible = bibleNow(), q = b.query.trim();
    $('cols').hidden = !!q; $('results').hidden = !q;
    if (q) { renderResults(q, bible); return; }
    const books = $('books'); if (!books.childElementCount) { S.kjv.names.forEach((n, i) => { const x = document.createElement('button'); x.className = 'bk ' + (i < 39 ? 'ot' : 'nt'); x.textContent = n; x.onclick = () => { b.book = i; b.chapter = 1; b.anchor = null; b.scroll = true; renderBrowser(); }; books.appendChild(x); }); }
    [...books.children].forEach((x, i) => x.classList.toggle('sel', i === b.book));
    const chaps = $('chaps'); chaps.textContent = '';
    for (let c = 1; c <= bible.chapterCount(b.book); c++) { const x = document.createElement('button'); x.textContent = c; if (c === b.chapter) x.className = 'sel'; x.onclick = () => { b.chapter = c; b.anchor = null; b.scroll = true; renderBrowser(); }; chaps.appendChild(x); }
    const vs = $('verses'); vs.textContent = ''; const sp = S.stage.kind === 'scripture' ? S.stage.passage : null;
    for (let v = 1; v <= bible.verseCount(b.book, b.chapter); v++) {
      const d = document.createElement('div'); d.className = 'vs'; const on = sp && sp.book === b.book && sp.chapter === b.chapter && v >= sp.from && v <= sp.to; if (on) d.classList.add('staged');
      d.innerHTML = '<b></b><span></span>'; d.firstChild.textContent = v; d.lastChild.textContent = bible.verse(b.book, b.chapter, v);
      d.onclick = (e) => { const [from, to] = e.shiftKey && b.anchor ? [Math.min(b.anchor, v), Math.max(b.anchor, v)] : [v, v]; b.anchor = from; stagePassage({ book: b.book, chapter: b.chapter, from, to }, 'browser'); };
      vs.appendChild(d); if (on && b.scroll && sp.from === v) d.scrollIntoView({ block: 'center' });
    }
    if (b.scroll) { const sel = books.children[b.book]; sel && sel.scrollIntoView({ block: 'center' }); const cs = chaps.querySelector('.sel'); cs && cs.scrollIntoView({ block: 'center' }); b.scroll = false; }
  }
  function renderResults(q, bible) {
    const el = $('results'); el.textContent = ''; const res = RF.search(bible, S.idx, q, 40);
    if (!res.length) { el.innerHTML = '<div class="muted">nothing found \u2014 try fewer words, or a book name</div>'; return; }
    for (const r of res) {
      const d = document.createElement('div'); d.className = 'res';
      if (r.type === 'book') { d.innerHTML = '<span class="ref"></span> <span class="muted">\u2014 open book</span>'; d.firstChild.textContent = '\ud83d\udcd6 ' + S.kjv.names[r.book]; d.onclick = () => openBook(r.book, 1); }
      else if (r.type === 'chapter') { d.innerHTML = '<span class="ref"></span> <span class="muted">\u2014 open chapter</span>'; d.firstChild.textContent = '\ud83d\udcd6 ' + S.kjv.names[r.book] + ' ' + r.chapter; d.onclick = () => openBook(r.book, r.chapter); }
      else { d.innerHTML = '<span class="ref"></span><span class="pct"></span><span class="t"></span>'; d.children[0].textContent = label(r); d.children[1].textContent = r.pct + '%'; d.children[2].textContent = r.text.slice(0, 170); d.onclick = () => { $('q').value = ''; S.br.query = ''; stagePassage(r, 'browser'); }; }
      el.appendChild(d);
    }
    el._first = res[0];
  }
  function openBook(book, chapter) { S.br.book = book; S.br.chapter = chapter; S.br.anchor = null; S.br.scroll = true; S.br.query = ''; $('q').value = ''; renderBrowser(); }

  // ------------------------------------------------------------- versions (IndexedDB)
  function idb() { return new Promise((res, rej) => { const r = indexedDB.open('rhemaflow', 1); r.onupgradeneeded = () => r.result.createObjectStore('bibles', { keyPath: 'name' }); r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); }); }
  async function idbAll() { try { const db = await idb(); return await new Promise((res) => { const q = db.transaction('bibles').objectStore('bibles').getAll(); q.onsuccess = () => res(q.result || []); q.onerror = () => res([]); }); } catch (e) { return []; } }
  async function idbPut(rec) { try { const db = await idb(); db.transaction('bibles', 'readwrite').objectStore('bibles').put(rec); } catch (e) { /* private mode: lives only this session */ } }
  async function idbDel(name) { try { const db = await idb(); db.transaction('bibles', 'readwrite').objectStore('bibles').delete(name); } catch (e) { /* ignore */ } }
  function fillTranslations() { const sel = $('trans'); sel.textContent = ''; ['KJV', ...Object.keys(S.versions)].forEach((n) => { const o = document.createElement('option'); o.textContent = n; if (n === S.translation) o.selected = true; sel.appendChild(o); }); }
  function addVersion(name, data) { S.versions[name] = RF.makeBible(data); fillTranslations(); renderInstalled(); }
  function renderInstalled() {
    const el = $('installed'); el.textContent = ''; const names = Object.keys(S.versions); if (!names.length) { el.innerHTML = '<span class="muted small">no extra versions yet</span>'; }
    names.forEach((n) => { const r = document.createElement('div'); r.className = 'row'; r.innerHTML = '<b class="gold"></b>'; r.firstChild.textContent = n; const u = document.createElement('button'); u.textContent = 'use'; u.onclick = () => setTranslation(n); const x = document.createElement('button'); x.textContent = 'remove'; x.onclick = async () => { delete S.versions[n]; await idbDel(n); if (S.translation === n) setTranslation('KJV'); else fillTranslations(); renderInstalled(); }; r.append(u, x); el.appendChild(r); });
    const pd = $('pdlist'); pd.textContent = ''; PD.forEach(([n, d]) => { const b = document.createElement('button'); b.textContent = S.versions[n] ? n + ' \u2713' : n; b.title = d; b.disabled = !!S.versions[n]; b.onclick = () => downloadPD(n); pd.appendChild(b); });
  }
  async function downloadPD(name) {
    const msg = $('vmsg'); msg.textContent = `downloading ${name}\u2026`;
    try { const r = await fetch(`${PD_BASE}/${name}.json`); if (!r.ok) throw new Error('HTTP ' + r.status); const data = RF.importBible(await r.text(), S.kjv.names); await idbPut({ name, ...data }); addVersion(name, data); msg.textContent = `${name} ready`; }
    catch (e) { msg.textContent = `${name} failed: ${e.message}`; msg.style.color = 'var(--red)'; }
  }
  $('bibleFile').onchange = async (e) => {
    for (const f of e.target.files) {
      const name = f.name.replace(/\.[^.]+$/, ''); try { const data = RF.importBible(await f.text(), S.kjv.names); await idbPut({ name, ...data }); addVersion(name, data); $('vmsg').textContent = `${name} ready`; $('vmsg').style.color = ''; }
      catch (err) { $('vmsg').textContent = `${f.name}: ${err.message}`; $('vmsg').style.color = 'var(--red)'; }
    }
    e.target.value = '';
  };

  // ------------------------------------------------------------- sermon plan
  function renderPlan() {
    const el = $('planList'); el.textContent = ''; if (!S.plan.length) { el.innerHTML = '<div class="muted small">no scriptures yet</div>'; $('bPlan').textContent = 'Plan'; return; }
    $('bPlan').textContent = `Plan (${S.plan.length})`;
    S.plan.forEach((it, i) => { const r = document.createElement('div'); r.className = 'row'; const mark = document.createElement('span'); mark.textContent = i === S.planPos ? '\u25b6' : i < S.planPos ? '\u2713' : ' '; mark.style.width = '1.2em'; const b = document.createElement('button'); b.textContent = it.label; if (i === S.planPos) b.className = 'go'; b.onclick = () => planStage(i); const t = document.createElement('span'); t.className = 'muted small'; t.textContent = S.kjv.passage(it.passage.book, it.passage.chapter, it.passage.from, it.passage.to).slice(0, 70); r.append(mark, b, t); el.appendChild(r); });
  }
  function planStage(i) { const it = S.plan[i]; if (!it) return; S.planPos = i + 1; stagePassage(it.passage, 'plan'); renderPlan(); }
  function planNext() { if (S.planPos < S.plan.length) planStage(S.planPos); }
  $('planFind').onclick = () => { S.plan = RF.planFromText(S.kjv, S.idx, $('planText').value); S.planPos = 0; renderPlan(); };
  $('planNext').onclick = planNext; $('planReset').onclick = () => { S.planPos = 0; renderPlan(); }; $('planClear').onclick = () => { S.plan = []; S.planPos = 0; $('planText').value = ''; renderPlan(); };

  function renderCmds(q) {
    const el = $('cmdlist'); el.textContent = ''; q = q.trim().toLowerCase();
    for (const g of RF.commandList()) {
      const ph = g.phrases.filter((x) => !q || x.p.includes(q) || g.label.toLowerCase().includes(q)); if (!ph.length) continue;
      const row = document.createElement('div'); row.className = 'g';
      const n = document.createElement('div'); n.className = 'n'; n.textContent = g.label;
      const p = document.createElement('div'); p.className = 'p';
      ph.forEach((x, i) => { const sp = document.createElement('span'); sp.textContent = '\u201c' + x.p + '\u201d'; p.appendChild(sp); if (x.short) { const t = document.createElement('i'); t.textContent = ' (short)'; p.appendChild(t); } if (i < ph.length - 1) p.appendChild(document.createTextNode('  \u00b7  ')); });
      row.append(n, p); el.appendChild(row);
    }
    if (!el.childElementCount) el.innerHTML = '<div class="muted">no command matches that search</div>';
  }

  // ------------------------------------------------------------- wiring
  function wire() {
    $('btnStart').onclick = () => (S.live ? endService() : startService());
    $('btnSettings').onclick = () => { $('title').value = S.title; $('church').value = S.church; $('saveSrt').checked = S.saveSrt; $('saveMd').checked = S.saveMd; $('saveRec').checked = S.saveRec; $('dlgSettings').showModal(); };
    $('dlgSettings').addEventListener('close', () => { S.title = $('title').value; S.church = $('church').value; S.saveSrt = $('saveSrt').checked; S.saveMd = $('saveMd').checked; S.saveRec = $('saveRec').checked; save(); });
    $('btnVersions').onclick = () => { renderInstalled(); $('dlgVersions').showModal(); };
    $('btnHelp').onclick = () => $('dlgHelp').showModal();
    $('bPrevV').onclick = () => nav('prev_verse'); $('bNextV').onclick = () => nav('next_verse'); $('bPrevC').onclick = () => nav('prev_chapter'); $('bNextC').onclick = () => nav('next_chapter');
    $('bStage').onclick = () => (S.stageWin && !S.stageWin.closed ? closeStage() : openStage());
    $('bBlack').onclick = () => run('blackout'); $('bClear').onclick = clearStage;
    $('style').onchange = (e) => { S.style = e.target.value; save(); render(); };
    $('trans').onchange = (e) => setTranslation(e.target.value);
    $('bRead').onclick = speak; $('bStop').onclick = stopSpeaking; $('autoRead').onchange = (e) => { S.autoRead = e.target.checked; if (!S.autoRead) stopSpeaking(); save(); };
    $('zOut').onclick = () => run('zoom_out'); $('zIn').onclick = () => run('zoom_in'); $('zoom').oninput = (e) => setZoom(+e.target.value);
    $('zpre').onchange = (e) => { if (e.target.value) setZoom(+e.target.value); e.target.value = ''; };
    $('bCmds').onclick = () => { renderCmds(''); $('dlgCmds').showModal(); };
    $('cmdq').oninput = (e) => renderCmds(e.target.value);
    $('bPlan').onclick = () => { renderPlan(); $('dlgPlan').showModal(); };
    $('bBrowser').onclick = () => { S.br.visible = !S.br.visible; save(); renderBrowser(); };
    $('autoApprove').onchange = (e) => { S.autoApprove = e.target.checked; save(); }; $('showAll').onchange = (e) => { S.showAll = e.target.checked; save(); renderCards(); };
    $('lang').onchange = (e) => { S.lang = e.target.value; save(); if (S.live) { stopListening(); setTimeout(startListening, 300); } };
    const q = $('q');
    q.oninput = () => { S.br.query = q.value; renderBrowser(); };
    q.onkeydown = (e) => {
      if (e.key === 'Escape') { q.value = ''; S.br.query = ''; renderBrowser(); q.blur(); }
      if (e.key === 'Enter') { const r = $('results')._first; if (!r) return; if (r.type === 'verse') { q.value = ''; S.br.query = ''; stagePassage(r, 'browser'); } else openBook(r.book, r.chapter || 1); }
    };
    $('qx').onclick = () => { q.value = ''; S.br.query = ''; renderBrowser(); };
    $('recover').onclick = () => { try { const d = JSON.parse(localStorage.getItem('rf.live')); const start = new Date(d.start), last = d.lines.length ? d.lines[d.lines.length - 1].ms : 0; $('dlgSettings').close(); showSaved(start, new Date(start.getTime() + last), last, null, d.lines, d.cites, d.title); } catch (e) { toast('nothing to recover'); } };
    document.addEventListener('keydown', (e) => {
      const tag = (e.target.tagName || '').toLowerCase(); const typing = tag === 'input' || tag === 'textarea' || tag === 'select';
      if (typing || e.metaKey || e.ctrlKey || e.altKey) return;
      const k = e.key;
      const map = { ' ': S.cards.some((c) => c.chapter > 0) ? 'approve' : 'plan_next', x: 'dismiss', 1: 'pick_1', 2: 'pick_2', 3: 'pick_3', 4: 'pick_4', 5: 'pick_5', ArrowRight: 'next_verse', n: 'next_verse', ArrowLeft: 'prev_verse', p: 'prev_verse', ArrowDown: 'next_chapter', ArrowUp: 'prev_chapter', m: 'next_chapter', b: 'blackout', c: 'clear', r: 'read', s: 'stop_reading', h: 'help' };
      if (k === '/') { e.preventDefault(); S.br.visible = true; renderBrowser(); $('q').focus(); return; }
      if (k === 'f' || k === 'F') { e.preventDefault(); (S.stageWin && !S.stageWin.closed ? closeStage : openStage)(); return; }
      const name = map[k] || map[k.toLowerCase()]; if (name) { e.preventDefault(); run(name); }
    });
  }

  // ------------------------------------------------------------- stage window mode
  function stageMode() {
    document.body.classList.add('stagemode'); $('stageonly').hidden = false; document.title = 'RhemaFlow stage';
    let st = { kind: 'blank' }, look = { style: 'classic', zoom: 1, blackout: false };
    const paint = () => drawStage($('stg'), st, look);
    if (chan) { chan.onmessage = (e) => { const m = e.data; if (m.t === 'state') { st = m.stage; look = { style: m.style, zoom: m.zoom, blackout: m.blackout }; paint(); } if (m.t === 'exitfs' && document.fullscreenElement) document.exitFullscreen(); }; chan.postMessage({ t: 'hello' }); }
    const fs = () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen().catch(() => {}));
    addEventListener('keydown', (e) => { if (e.key === 'f' || e.key === 'F') fs(); }); addEventListener('dblclick', fs); addEventListener('resize', paint);
    document.addEventListener('fullscreenchange', () => { $('fshint').style.opacity = document.fullscreenElement ? 0 : 1; });
    setTimeout(() => { $('fshint').style.opacity = 0; }, 6000);
  }

  // ------------------------------------------------------------- boot
  async function inflateKjv() {
    const bin = atob(__KJV_B64__), bytes = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
    return JSON.parse(await new Response(stream).text());
  }
  async function boot() {
    if (IS_STAGE) return stageMode();
    load(); wire();
    S.kjv = RF.makeBible(await inflateKjv()); S.idx = RF.buildBookIndex(S.kjv.names);
    for (const rec of await idbAll()) { try { S.versions[rec.name] = RF.makeBible({ names: S.kjv.names, books: rec.books }); } catch (e) { /* skip */ } }
    if (!S.versions[S.translation]) S.translation = 'KJV';
    fillTranslations(); $('style').value = S.style; $('autoApprove').checked = S.autoApprove; $('showAll').checked = S.showAll; $('autoRead').checked = S.autoRead; $('lang').value = S.lang;
    $('engineNote').textContent = SR ? '' : 'no speech recognition in this browser';
    if (location.protocol === 'file:') { const n = $('sttNote'); n.className = 'small warn'; n.textContent = 'Tip: opened as a file, Chrome asks for the microphone every time and may refuse it. For reliable listening run  python3 -m http.server 8000  in this folder and open http://localhost:8000/rhemaflow-app.html'; }
    try { if (localStorage.getItem('rf.live')) $('recover').hidden = false; } catch (e) { /* ignore */ }
    if (chan) chan.onmessage = (e) => { if (e.data.t === 'hello') render(); };
    render(); renderBrowser(); renderRecent(); renderPlan();
    addEventListener('resize', render);
    document.body.dataset.ready = '1';
  }
  boot();
})();
