const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const { resolve } = require('node:path');
const template = readFileSync(resolve(__dirname, '../../app/templates/pages/assistant.html'), 'utf8');
function setup(fetch) {
  const state = runInNewContext(`${template.match(/<script>([\s\S]*?)<\/script>/)[1]}; serviceAssistant()`, { fetch, Date });
  state.$nextTick = callback => callback();
  state.$refs = { chat: { scrollHeight: 100, scrollTop: 0 }, question: { focus() {} } };
  return state;
}
test('switches immediately, blocks duplicate sends, preserves draft and conversation', async () => {
  let finish;
  let calls = 0;
  const state = setup(() => { calls++; return new Promise(resolve => { finish = resolve; }); });
  state.message = '  น้ำมันรั่ว  ';
  const pending = state.submit();
  assert.equal(state.messages.length, 1);
  assert.equal(state.messages[0].text, 'น้ำมันรั่ว');
  assert.equal(state.messages[0].role, 'user');
  assert.equal(state.loading, true);
  assert.equal(state.message, '');
  const sent = state.messages[0].timestamp;
  state.message = 'next question';
  await state.submit();
  assert.equal(calls, 1);
  finish({ ok: true, json: async () => ({ data: { answer: 'Check seal', citations: [{ document: 'manual', section: '1' }] } }) });
  await pending;
  assert.equal(state.messages.length, 2);
  assert.equal(state.messages[1].role, 'assistant');
  assert.match(state.messages[1].citation, /manual/);
  assert.ok(state.messages[1].timestamp >= sent);
  assert.equal(state.message, 'next question');
  const next = state.submit();
  finish({ ok: true, json: async () => ({ data: { answer: 'Second answer', citations: [] } }) });
  await next;
  assert.equal(state.messages.length, 4);
  assert.equal(state.messages[0].timestamp, sent);
});
test('formats UTC date and milliseconds exactly as requested', () => {
  const state = setup();
  assert.equal(state.formatTimestamp('2026-01-02T13:04:05.006Z'), '02/01/2026/ 04:05.006Z');
});
test('rejects whitespace and recovers after failed requests with a timestamped reply', async () => {
  const state = setup(async () => { throw new Error('offline'); });
  state.message = '   ';
  await state.submit();
  assert.equal(state.messages.length, 0);
  state.language = 'th';
  state.message = 'คำถาม';
  await state.submit();
  assert.equal(state.messages.length, 2);
  assert.equal(state.messages[1].text, state.copy.requestError);
  assert.match(state.messages[1].timestamp, /\.\d{3}Z$/);
  assert.equal(state.loading, false);
});
test('HTTP errors and malformed responses become visible replies', async () => {
  for (const response of [{ ok: false }, { ok: true, json: async () => ({}) }]) {
    const state = setup(async () => response);
    state.message = 'Question';
    await state.submit();
    assert.equal(state.messages[1].text, state.copy.requestError);
    assert.equal(state.loading, false);
  }
});
