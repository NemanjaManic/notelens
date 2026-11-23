/* Offline source verification and explicit coordinator decisions. */
'use strict';

class ReviewState {
  constructor(packet, hash) {
    this.packet = packet;
    this.hash = hash;
    this.items = new Map(packet.items.map(row => [row.item_id, row]));
    this.decisions = {};
    this.approvals = {};
    this.documentNotes = {};
    this.imported = {};
    this.reviewer = 'Milica';
    this.verified = new Set(Object.values(packet.documents).filter(d => d.canonical_text !== null).map(d => d.assignment_id));
  }
  setDecision(id, decision, notes = '') {
    if (!this.items.has(id) || !['', 'accept_proposal', 'revise', 'defer'].includes(decision)) throw Error('Unknown item or decision.');
    const row = this.items.get(id);
    if (!this.verified.has(row.assignment_id)) throw Error('Verify the canonical source before deciding.');
    this.decisions[id] = {decision, notes: notes.trim()};
    delete this.approvals[row.assignment_id];
  }
  resolved(id) {
    const row = this.decisions[id];
    return Boolean(row && (row.decision === 'accept_proposal' || (row.decision === 'revise' && row.notes)));
  }
  documentItems(aid) { return this.packet.items.filter(row => row.assignment_id === aid); }
  documentReady(aid) {
    return this.verified.has(aid) && this.documentItems(aid).every(row => this.resolved(row.item_id));
  }
  approve(aid, acceptRemaining, note = '') {
    if (!this.packet.documents[aid] || !this.verified.has(aid)) throw Error('The canonical source is missing.');
    if (acceptRemaining) {
      if (this.documentItems(aid).some(row => {
        const saved = this.decisions[row.item_id];
        return saved && (saved.decision === 'defer' || (saved.decision === 'revise' && !saved.notes) || (!saved.decision && saved.notes));
      })) throw Error('Resolve deferred items and select a decision for every written correction.');
      for (const row of this.documentItems(aid)) {
        if (!this.decisions[row.item_id]?.decision) this.decisions[row.item_id] = {decision: 'accept_proposal', notes: ''};
      }
    }
    if (!this.documentReady(aid)) throw Error('Resolve deferred items and supply every revised decision.');
    this.documentNotes[aid] = note.trim();
    this.approvals[aid] = {human_reviewed: true, note: note.trim(), approved_at: new Date().toISOString()};
  }
  restore(data) {
    if (data.packet_sha256 !== this.hash) throw Error('This progress file belongs to a different packet.');
    if (!data.decisions || !data.document_approvals) throw Error('Invalid progress file.');
    const next = {};
    for (const [id, value] of Object.entries(data.decisions)) {
      if (!this.items.has(id) || !value || !['', 'accept_proposal', 'revise', 'defer'].includes(value.decision) || typeof value.notes !== 'string') throw Error('Invalid saved decision.');
      next[id] = {decision: value.decision, notes: value.notes};
    }
    const approvals = {};
    for (const [aid, value] of Object.entries(data.document_approvals)) {
      if (!this.packet.documents[aid] || value.human_reviewed !== true) throw Error('Invalid saved document approval.');
      approvals[aid] = value;
    }
    this.decisions = next;
    this.approvals = approvals;
    this.documentNotes = {};
    for (const [aid, note] of Object.entries(data.document_notes || {})) {
      if (!this.packet.documents[aid] || typeof note !== 'string') throw Error('Invalid saved document correction.');
      this.documentNotes[aid] = note;
    }
    this.reviewer = data.adjudicator || 'Milica';
    // Imported source text is never trusted from a progress file. Re-select it.
    for (const aid of Object.keys(approvals)) {
      if (!this.documentItems(aid).every(row => this.resolved(row.item_id))) delete this.approvals[aid];
    }
  }
  progress() {
    return {version: 'd013-complete-adjudication-progress-v1', packet_sha256: this.hash,
      adjudicator: this.reviewer, saved_at: new Date().toISOString(), decisions: this.decisions,
      document_approvals: this.approvals, document_notes: this.documentNotes,
      imported_source_hashes: Object.fromEntries(Object.entries(this.imported).map(([aid, value]) => [aid, value.sha256]))};
  }
  exportComplete(attested) {
    const aids = Object.keys(this.packet.documents);
    if (!this.reviewer.trim() || !attested) throw Error('Enter your name and confirm your personal review.');
    if (aids.some(aid => !this.documentReady(aid) || !this.approvals[aid])) throw Error('Complete every source check, decision and document approval. Save progress if resources are still missing.');
    return {...this.progress(), version: 'd013-complete-human-decisions-v1', human_reviewed: true,
      completed_at: new Date().toISOString(), canonical_source_sha256: Object.fromEntries(aids.map(aid => [aid, this.packet.documents[aid].text_sha256])),
      imported_source_files: Object.fromEntries(Object.entries(this.imported).map(([aid, value]) => [aid, {filename: value.filename, sha256: value.sha256}])),
      previous_decision_pins: this.packet.previous_decision_pins,
      resolved_decisions: this.packet.items.map(row => ({item_id: row.item_id, assignment_id: row.assignment_id,
        covers: row.covers, decision: this.decisions[row.item_id].decision,
        decision_text: this.decisions[row.item_id].decision === 'accept_proposal' ? row.recommendation : this.decisions[row.item_id].notes,
        notes: this.decisions[row.item_id].notes, human_reviewed: true})),
      canonical_references_frozen: false, original_submissions_modified: false};
  }
}

function validateSource(document, text) {
  const points = Array.from(text);
  for (const entity of document.entities) {
    for (const span of [entity.mention, ...entity.evidence]) {
      if (!Number.isInteger(span.start) || !Number.isInteger(span.end) || span.start < 0 || span.start >= span.end || span.end > points.length || points.slice(span.start, span.end).join('') !== span.quote) throw Error('A mention or evidence span does not match the canonical file.');
    }
    if (!entity.evidence.some(span => span.start <= entity.mention.start && span.end >= entity.mention.end)) throw Error('Evidence does not cover a mention.');
  }
  return points.length;
}

if (typeof module !== 'undefined') module.exports = {ReviewState, validateSource};

if (typeof document !== 'undefined') {
  const packet = JSON.parse(document.getElementById('packet').textContent);
  const state = new ReviewState(packet, PACKET_HASH);
  const storageKey = 'notelens-d013-' + PACKET_HASH;
  const el = id => document.getElementById(id);
  function node(tag, text, parent, cls) {
    const value = document.createElement(tag);
    if (text !== undefined && text !== null) value.textContent = text;
    if (cls) value.className = cls;
    if (parent) parent.append(value);
    return value;
  }
  function persist() {
    state.reviewer = el('reviewer').value.trim();
    try { localStorage.setItem(storageKey, JSON.stringify(state.progress())); }
    catch (_) { el('status').textContent = 'Browser autosave is unavailable. Use Save progress JSON.'; }
    refreshProgress();
  }
  function refreshProgress() {
    const approvedCount = Object.keys(state.approvals).filter(aid => state.documentReady(aid)).length;
    el('progress').textContent = `${state.verified.size}/40 sources verified · ${approvedCount}/40 documents approved · ${packet.items.filter(row => state.resolved(row.item_id)).length}/${packet.items.length} decisions recorded`;
    for (const aid of Object.keys(packet.documents)) {
      const panel = el(aid);
      if (!panel) continue;
      const approved = Boolean(state.approvals[aid] && state.documentReady(aid));
      panel.hidden = (el('filter').value === 'pending' && approved) || (el('filter').value === 'blocked' && state.verified.has(aid));
      const status = el('approval-' + aid);
      if (status) status.textContent = approved ? 'Document approved, subject to application and verification of your recorded corrections.' : 'Document approval pending.';
    }
  }
  function entityTable(entities, parent) {
    const table = node('table', null, parent);
    const head = node('tr', null, table);
    for (const label of ['Mention [start, end)', 'Type', 'Assertion / time / subject', 'Procedure state']) node('th', label, head);
    for (const e of entities) {
      const row = node('tr', null, table);
      node('td', `${e.mention.quote} [${e.mention.start}, ${e.mention.end})`, row);
      node('td', e.type, row);
      node('td', `${e.assertion} / ${e.temporality} / ${e.subject}`, row);
      node('td', e.procedure_status || '—', row);
    }
  }
  function renderItem(row, parent) {
    const article = node('article', null, parent, 'item');
    node('h3', row.item_id, article);
    node('span', row.category.replaceAll('_', ' '), article, 'tag');
    node('p', row.question, article);
    const source = packet.documents[row.assignment_id].canonical_text;
    if (source === null) node('p', 'Source verification pending. Submitted labels below are not a substitute for the full canonical text.', article, 'blocked');
    const anchors = source === null ? [] : (row.source_anchors.length ? row.source_anchors : (row.source_range ? [{start: row.source_range[0], end: row.source_range[1], quote: Array.from(source).slice(...row.source_range).join('')}] : []));
    for (const span of anchors) {
      node('small', `Canonical source [${span.start}, ${span.end})`, article);
      node('blockquote', span.quote, article);
    }
    node('h4', 'Recommendation for your decision', article);
    node('p', row.recommendation, article);
    if (row.rationale) node('p', row.rationale, article);
    if (row.details) {
      const details = node('details', null, article);
      node('summary', 'Submitted alternatives and exact attributes', details);
      node('pre', JSON.stringify(row.details, null, 2), details);
    }
    const label = node('label', 'Your decision ', article);
    const select = node('select', null, label);
    for (const [value, name] of [['', 'Choose after review'], ['accept_proposal', 'Accept recommendation'], ['revise', 'Use my revised decision'], ['defer', 'Keep unresolved']]) {
      const option = node('option', name, select); option.value = value;
    }
    const notesLabel = node('label', 'Correction or explanation (required for a revision or unresolved item)', article);
    const notes = node('textarea', null, notesLabel);
    select.disabled = notes.disabled = !state.verified.has(row.assignment_id);
    select.value = state.decisions[row.item_id]?.decision || '';
    notes.value = state.decisions[row.item_id]?.notes || '';
    const update = () => { state.setDecision(row.item_id, select.value, notes.value); persist(); };
    select.addEventListener('change', update); notes.addEventListener('input', update);
  }
  function render() {
    el('documents').replaceChildren(); el('navigation').replaceChildren();
    for (const [aid, doc] of Object.entries(packet.documents)) {
      const link = node('a', aid.slice(-3), el('navigation')); link.href = '#' + aid;
      const panel = node('section', null, el('documents'), 'document'); panel.id = aid;
      node('h2', `${aid} · ${state.documentItems(aid).length} remaining decisions`, panel);
      node('small', `Frozen SHA-256: ${doc.text_sha256}`, panel);
      if (!state.verified.has(aid)) node('p', 'Blocked: load the exact canonical source file above.', panel, 'blocked');
      if (doc.canonical_text !== null) {
        const full = node('details', null, panel);
        node('summary', 'Read full canonical source', full); node('pre', doc.canonical_text, full);
      }
      if (doc.previously_decided.length) {
        const previous = node('details', null, panel);
        node('summary', 'Earlier decisions already recorded — no repeat required', previous); node('pre', JSON.stringify(doc.previously_decided, null, 2), previous);
      }
      if (doc.paired_comparison) {
        const comparison = node('details', null, panel);
        node('summary', 'Complete independent-review comparison', comparison); node('pre', JSON.stringify(doc.paired_comparison, null, 2), comparison);
      }
      const inventory = node('details', null, panel);
      node('summary', `Working reference: ${doc.entities.length} proposed mentions and evidence`, inventory);
      node('p', 'Pending source-linked recommendations are shown below. Apply their accepted changes and your corrections before reference freeze. Original submissions remain unchanged.', inventory);
      entityTable(doc.entities, inventory);
      const raw = node('details', null, inventory); node('summary', 'Evidence and full provenance', raw); node('pre', JSON.stringify(doc, null, 2), raw);
      for (const row of state.documentItems(aid)) renderItem(row, panel);
      const controls = node('div', null, panel, 'document-controls');
      const attestLabel = node('label', null, controls);
      const attest = node('input', null, attestLabel); attest.type = 'checkbox';
      attestLabel.append(document.createTextNode(' I reviewed this document, its working reference, all remaining questions and submitted alternatives.'));
      const noteLabel = node('label', 'Additional reference correction (optional; describe the exact wording and attributes)', controls);
      const note = node('textarea', null, noteLabel); note.value = state.documentNotes[aid] || state.approvals[aid]?.note || '';
      note.addEventListener('input', () => { state.documentNotes[aid] = note.value; delete state.approvals[aid]; persist(); });
      const accept = node('button', 'Accept remaining recommendations and approve document', controls);
      const approve = node('button', 'Approve using my recorded decisions', controls);
      accept.disabled = approve.disabled = !state.verified.has(aid);
      const status = node('p', '', controls); status.id = 'approval-' + aid;
      function approveDocument(all) {
        try {
          if (!attest.checked) throw Error('Confirm that you reviewed this document first.');
          state.approve(aid, all, note.value); persist(); render();
          const next = Object.keys(packet.documents).find(value => !state.approvals[value]);
          if (next) el(next).scrollIntoView();
        } catch (error) { status.textContent = error.message; }
      }
      accept.addEventListener('click', () => approveDocument(true)); approve.addEventListener('click', () => approveDocument(false));
    }
    refreshProgress();
  }
  function download(value, filename) {
    const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2) + '\n'], {type: 'application/json'}));
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  el('request').textContent = packet.resource_request;
  el('filter').addEventListener('change', refreshProgress);
  el('reviewer').addEventListener('input', persist);
  el('save').addEventListener('click', () => { persist(); download(state.progress(), 'd013-complete-review-progress-v1.json'); });
  el('restore').addEventListener('change', async event => {
    try { state.restore(JSON.parse(await event.target.files[0].text())); el('reviewer').value = state.reviewer; persist(); render(); el('status').textContent = 'Progress restored. Re-select externally supplied source files if required.'; }
    catch (error) { el('status').textContent = error.message; }
  });
  el('sources').addEventListener('change', async event => {
    const messages = [];
    for (const file of event.target.files) {
      try {
        const bytes = await file.arrayBuffer();
        const hash = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))).map(n => n.toString(16).padStart(2, '0')).join('');
        const doc = Object.values(packet.documents).find(value => value.text_sha256 === hash);
        if (!doc) throw Error('SHA-256 matches no frozen assignment. Obtain the exact original file.');
        const text = new TextDecoder('utf-8', {fatal: true, ignoreBOM: true}).decode(bytes);
        const count = validateSource(doc, text);
        for (const row of state.documentItems(doc.assignment_id)) {
          if (row.source_range && row.source_range[1] > count) throw Error('A question interval exceeds this source.');
        }
        doc.canonical_text = text; state.verified.add(doc.assignment_id);
        state.imported[doc.assignment_id] = {filename: file.name, sha256: hash};
        messages.push(`${doc.assignment_id}: hash and ${doc.entities.length} mention/evidence records verified.`);
      } catch (error) { messages.push(`${file.name}: ${error.message}`); }
    }
    el('source-log').textContent = messages.join('\n'); persist(); render();
  });
  el('export').addEventListener('click', () => {
    try {
      persist(); const result = state.exportComplete(el('attestation').checked);
      download(result, 'd013-complete-human-decisions-v1.json');
      el('status').textContent = 'Completed decisions exported. Return this JSON; keep any newly received canonical files available for independent source re-verification and the final merge.';
    } catch (error) { el('status').textContent = error.message; }
  });
  try { const saved = localStorage.getItem(storageKey); if (saved) state.restore(JSON.parse(saved)); }
  catch (_) { el('status').textContent = 'Use Save progress JSON to preserve your work.'; }
  el('reviewer').value = state.reviewer; render();
}
