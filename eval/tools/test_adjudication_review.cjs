/* Synthetic checks only. These records are never human-review evidence. */
'use strict';
const assert = require('node:assert/strict');
const {ReviewState, validateSource} = require('./adjudication-review.js');
const packet = {
  documents: {
    'synthetic-a': {assignment_id: 'synthetic-a', canonical_text: 'A🩺pain.', text_sha256: 'a', entities: []},
    'synthetic-b': {assignment_id: 'synthetic-b', canonical_text: null, text_sha256: 'b', entities: []}
  },
  items: [
    {item_id: 'q-a', assignment_id: 'synthetic-a', recommendation: 'Synthetic proposal A', covers: ['q-a']},
    {item_id: 'q-b', assignment_id: 'synthetic-b', recommendation: 'Synthetic proposal B', covers: ['q-b']}
  ], previous_decision_pins: []
};
const state = new ReviewState(packet, 'synthetic-packet-hash');
assert.throws(() => state.exportComplete(true), /Complete every source/);
assert.throws(() => state.setDecision('q-b', 'accept_proposal'), /Verify the canonical/);
assert.throws(() => state.approve('synthetic-b', true), /source is missing/);
assert.throws(() => state.setDecision('unknown', 'accept_proposal'), /Unknown/);
state.setDecision('q-a', 'defer', 'Synthetic missing context');
assert.throws(() => state.approve('synthetic-a', true), /Resolve deferred/);
state.setDecision('q-a', 'revise');
assert.throws(() => state.approve('synthetic-a', true), /Resolve deferred/);
state.setDecision('q-a', '', 'Do not lose this synthetic correction');
assert.throws(() => state.approve('synthetic-a', true), /written correction/);
assert.equal(state.decisions['q-a'].notes, 'Do not lose this synthetic correction');
state.setDecision('q-a', 'revise', 'Use the synthetic corrected decision');
state.approve('synthetic-a', false, 'Synthetic reference correction');
assert.equal(state.approvals['synthetic-a'].human_reviewed, true);
state.setDecision('q-a', 'accept_proposal');
assert.equal(state.approvals['synthetic-a'], undefined);
state.approve('synthetic-a', false);
state.verified.add('synthetic-b');
state.approve('synthetic-b', true);
state.reviewer = 'Synthetic test reviewer';
assert.throws(() => state.exportComplete(false), /confirm your personal review/);
const result = state.exportComplete(true);
assert.equal(result.resolved_decisions.length, 2);
assert.equal(result.canonical_references_frozen, false);
assert.equal(result.resolved_decisions[0].decision_text, 'Synthetic proposal A');
const restored = new ReviewState(packet, 'synthetic-packet-hash');
restored.restore(state.progress());
assert.ok(restored.approvals['synthetic-b']);
assert.throws(() => restored.exportComplete(true), /Complete every source/);
restored.verified.add('synthetic-b');
assert.equal(restored.exportComplete(true).resolved_decisions.length, 2);
assert.throws(() => restored.restore({...state.progress(), packet_sha256: 'wrong'}), /different packet/);
assert.throws(() => restored.restore({...state.progress(), decisions: {'unexpected': {decision: 'accept_proposal', notes: ''}}}), /Invalid saved decision/);
const unicodeDocument = {entities: [{mention: {start: 2, end: 6, quote: 'pain'}, evidence: [{start: 0, end: 7, quote: 'A🩺pain.'}]}]};
assert.equal(validateSource(unicodeDocument, 'A🩺pain.'), 7);
assert.throws(() => validateSource(unicodeDocument, 'A🩺PAIN.'), /does not match/);
assert.throws(() => validateSource({entities: [{mention: {start: 3, end: 7, quote: 'pain'}, evidence: unicodeDocument.entities[0].evidence}]}, 'A🩺pain.'), /does not match/);
assert.throws(() => validateSource({entities: [{mention: {start: 2, end: 6, quote: 'pain'}, evidence: [{start: 0, end: 2, quote: 'A🩺'}]}]}, 'A🩺pain.'), /does not cover/);
process.stdout.write('Synthetic decision gating, recovery, corrections and Unicode source checks passed.\n');
