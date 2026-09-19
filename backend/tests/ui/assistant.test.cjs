const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const { resolve } = require('node:path');
const template = readFileSync(resolve(__dirname, '../../app/templates/pages/assistant.html'), 'utf8');
function setup(fetch) {
  const state = runInNewContext(`${template.match(/<script>([\s\S]*?)<\/script>/)[1]}; serviceAssistant()`, { fetch, Date, TextDecoder, Uint8Array });
  state.$nextTick = callback => callback();
  state.$refs = { chat: { scrollHeight: 100, scrollTop: 0 }, question: { focus() {} } };
  return state;
}
function streamResponse(events) {
  const chunks = events.map(event => new TextEncoder().encode(`${JSON.stringify(event)}\n`));
  let index = 0;
  return {
    ok: true,
    body: { getReader: () => ({ read: async () => index < chunks.length ? { value: chunks[index++], done: false } : { done: true } }) }
  };
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
  finish(streamResponse([
    { type: 'delta', text: 'Check ' },
    { type: 'delta', text: 'seal' },
    { type: 'done', data: { answer: 'Check seal', citations: [{ document: 'manual', section: '1' }] } }
  ]));
  await pending;
  assert.equal(state.messages.length, 2);
  assert.equal(state.messages[1].role, 'assistant');
  assert.match(state.messages[1].citation, /manual/);
  assert.ok(state.messages[1].timestamp >= sent);
  assert.equal(state.message, 'next question');
  const next = state.submit();
  finish(streamResponse([{ type: 'done', data: { answer: 'Second answer', citations: [] } }]));
  await next;
  assert.equal(state.messages.length, 4);
  assert.equal(state.messages[0].timestamp, sent);
});
test('formats Thailand time with Gregorian dates and seconds in both languages', () => {
  const state = setup();
  for (const language of ['en', 'th']) {
    state.language = language;
    for (const [timestamp, expected] of [
      ['2026-01-02T13:04:05.006Z', '02/01/2026/ 20:04:05'],
      ['2026-12-31T17:00:00.999Z', '01/01/2027/ 00:00:00'],
      ['2026-01-31T18:02:03Z', '01/02/2026/ 01:02:03'],
      ['2024-02-28T17:00:00Z', '29/02/2024/ 00:00:00'],
      ['2026-07-02T13:04:05Z', '02/07/2026/ 20:04:05']
    ]) {
      assert.equal(state.formatTimestamp(timestamp), expected);
    }
  }
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
  for (const response of [{ ok: false }, streamResponse([{ type: 'unexpected' }])]) {
    const state = setup(async () => response);
    state.message = 'Question';
    await state.submit();
    assert.equal(state.messages[1].text, state.copy.requestError);
    assert.equal(state.loading, false);
  }
});

test('renders streamed deltas before replacing them with the authoritative result', async () => {
  const state = setup(async () => streamResponse([
    { type: 'delta', text: 'ตรวจ' },
    { type: 'delta', text: 'สอบซีล' },
    { type: 'done', data: { answer: 'ตรวจสอบซีล', citations: [] } }
  ]));
  state.message = 'น้ำมันรั่ว';
  await state.submit();
  assert.equal(state.messages[1].text, 'ตรวจสอบซีล');
  assert.equal(state.loading, false);
});

test('replaces stored messages so Alpine reacts to streamed answer updates', () => {
  const state = setup();
  const replyId = state.addMessage('assistant', '');
  const initiallyRenderedEntry = state.messages[0];

  state.applyStreamEvent({ type: 'delta', text: 'ตรวจ' }, replyId, state.copy);

  assert.notEqual(state.messages[0], initiallyRenderedEntry);
  assert.equal(state.messages[0].text, 'ตรวจ');
  const streamedEntry = state.messages[0];

  state.applyStreamEvent({ type: 'done', data: { answer: 'ตรวจสอบซีล', citations: [] } }, replyId, state.copy);

  assert.notEqual(state.messages[0], streamedEntry);
  assert.equal(state.messages[0].text, 'ตรวจสอบซีล');
});
