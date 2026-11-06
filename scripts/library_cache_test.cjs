// Compile frontend/lib/api.ts to artifacts/library-cache-test before running.
const assert = require('node:assert/strict');
const api = require('../artifacts/library-cache-test/api.js');
const response = (value, ok = true) => ({ok, status: ok ? 200 : 500, json: async () => value});
async function main() {
  let count = 0;
  global.fetch = async () => { count++; return response({version: count}); };
  api.invalidateLibraryCache();
  const [a, b] = await Promise.all([api.cachedLibrary('topics'), api.cachedLibrary('topics')]);
  assert.equal(count, 1); assert.deepEqual(a, b);
  await api.cachedLibrary('topics'); assert.equal(count, 1);
  await assert.rejects(api.cachedLibrary('admin/library'));
  await assert.rejects(api.cachedLibrary('progress'));
  assert.equal(count, 1);
  await api.request('answers', {method: 'POST'});
  await api.cachedLibrary('topics'); assert.equal(count, 2); // Answer did not invalidate.
  await api.request('admin/word-laboratory/preview', {method: 'POST'});
  await api.cachedLibrary('topics'); assert.equal(count, 3); // Preview did not invalidate.
  await api.request('admin/content/example/validate', {method: 'POST'});
  await api.cachedLibrary('topics'); assert.equal(count, 5); // Mutation did invalidate.

  const originalNow = Date.now;
  let clock = 1000;
  Date.now = () => clock;
  api.invalidateLibraryCache(); count = 0;
  await api.cachedLibrary('topics'); clock += 300001;
  await api.cachedLibrary('topics'); assert.equal(count, 2);
  Date.now = originalNow;

  api.invalidateLibraryCache();
  let fail = true; count = 0;
  global.fetch = async () => { count++; return response(fail ? {detail:'Synthetic error'} : {ok:true}, !fail); };
  await assert.rejects(api.cachedLibrary('topics'));
  fail = false; await api.cachedLibrary('topics'); assert.equal(count, 2);

  api.invalidateLibraryCache();
  const waiting = []; count = 0;
  global.fetch = () => { count++; return new Promise(resolve => waiting.push(resolve)); };
  const old = api.cachedLibrary('topics');
  api.invalidateLibraryCache();
  const fresh = api.cachedLibrary('topics');
  waiting[0](response({version:'old'})); await old;
  const sameFresh = api.cachedLibrary('topics'); assert.equal(count, 2);
  waiting[1](response({version:'fresh'})); await Promise.all([fresh, sameFresh]);
  assert.deepEqual(api.peekLibrary('topics'), {version:'fresh'});

  api.invalidateLibraryCache(); count = 0;
  global.fetch = async () => { count++; return response({}); };
  for (let i=0;i<121;i++) await api.cachedLibrary(`topics/test-${i}/words`);
  assert.equal(api.peekLibrary('topics/test-0/words'), undefined);
  assert.ok(api.peekLibrary('topics/test-120/words'));
  console.log('Library cache: deduplication, TTL, mutation invalidation, no progress/preview invalidation, retry, stale in-flight protection and size limit: PASS');
}
main().catch(error => { console.error(error); process.exitCode=1; });
