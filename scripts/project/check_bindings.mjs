// Exercise the same frozen payload cases through the generated TypeScript runtime.
import {readFileSync} from 'node:fs';
import assert from 'node:assert/strict';
import {validatePayload,validateJson,validateRecord,validateExchange,ContractValidationError} from '../../contracts/generated/typescript/v1.mjs';
const read=name=>JSON.parse(readFileSync(new URL('../../contracts/v1/fixtures/'+name,import.meta.url),'utf8'));
const {cases}=read('manifest.json'),payloads=read('payloads.json'),documents=read('documents.json'),references=read('references.json');
let total=0;
for(const c of cases) {
  if(c.kind!=='payload')continue;
  const actual=await validatePayload(c.definition,payloads[c.id],{document:documents[c.document],reference:references[c.reference]});
  assert.deepEqual(actual,c.expected,c.id);total++;
}
for(const fixture of ['classification-supported','classification-probability'])for(const number of [NaN,Infinity,-Infinity]) {
  const value=structuredClone(payloads[fixture]);value.scores[0].score=number;
  assert.deepEqual(await validatePayload('ClassificationResult',value),[{rule:'NUMBER_FINITE',path:'/scores/0/score'}]);
}
for(const text of ['{"a":1,"a":2}','{"score":NaN}','{"score":1e999}']) {
  await assert.rejects(()=>validateJson('ClassificationScore',text),e=>e instanceof ContractValidationError&&e.issues[0].rule==='JSON_INPUT');
}
for(const [fixture,numbers]of [['classification-supported',[-1e300,0,1e300]],['classification-probability',[0,1]]])for(const number of numbers){const value=structuredClone(payloads[fixture]);value.scores[0].score=number;await validateRecord('ClassificationResult',value);}
const text=documents.offset.text,chars=Array.from(text),start=chars.slice(0,47).join('').length,end=chars.slice(0,61).join('').length;
assert.equal(start,48);assert.equal(end,62);assert.equal(text.slice(start,end),'No chest pain.');
assert.equal((await validateRecord('ClassificationResult',payloads['classification-supported'])).status,'supported');
const transport=read('transport-cases.json').cases;
for(const c of transport)assert.deepEqual(await validateExchange(c),c.expected,c.id);
console.log(`PASS: TypeScript runtime, ${total}/${total} shared payload outcomes and ${transport.length}/${transport.length} correlation outcomes; native-number/JSON negatives and non-BMP offsets`);
