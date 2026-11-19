// Shared runtime semantics for generated TypeScript bindings. Wire shapes come from schema.json.
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import schema from './schema.json' with { type: 'json' };

const ajv = new Ajv2020({strict:false,strictNumbers:true,allErrors:true,validateFormats:true});
addFormats(ajv);
ajv.addSchema(schema);
const validators = new Map();
const labels = schema.$defs.ClassificationScore.properties.category.enum;
const noAnswer = 'The available sources do not support an answer.';
const noSummary = 'The available document evidence does not support a summary.';
const pointer = key => '/' + String(key).replaceAll('~','~0').replaceAll('/','~1');
const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const has = (value, keys) => keys.every(key => Object.hasOwn(value,key));
const equal = (left,right) => {
  if (Array.isArray(left) && Array.isArray(right)) return left.length===right.length && left.every((v,i)=>equal(v,right[i]));
  if (isObject(left) && isObject(right)) return Object.keys(left).length===Object.keys(right).length && Object.keys(left).every(k=>Object.hasOwn(right,k)&&equal(left[k],right[k]));
  return left===right;
};
const at = (value,path) => {
  if (path==='') return value;
  for (const part of path.slice(1).split('/')) {
    const key=part.replaceAll('~1','/').replaceAll('~0','~');
    if (value===null || typeof value!=='object' || !Object.hasOwn(value,key)) throw new Error('REFERENCE_POINTER: context pointer does not resolve');
    value=value[key];
  }
  return value;
};
const uniqueIssues = issues => [...new Map(issues.map(i=>[i.rule+'@'+i.path,i])).values()].sort((a,b)=>a.rule<b.rule?-1:a.rule>b.rule?1:a.path<b.path?-1:a.path>b.path?1:0);
function finiteIssues(value,path='',issues=[]) {
  if (typeof value==='number'&&!Number.isFinite(value)) issues.push({rule:'NUMBER_FINITE',path});
  else if (Array.isArray(value)) value.forEach((v,i)=>finiteIssues(v,path+pointer(i),issues));
  else if (isObject(value)) Object.entries(value).forEach(([k,v])=>finiteIssues(v,path+pointer(k),issues));
  return issues;
}
function structureIssues(errors) {
  const groups=errors.filter(e=>['anyOf','oneOf','contains'].includes(e.keyword));
  // Ajv emits branch diagnostics before aggregate errors; expose the aggregate location.
  return uniqueIssues(errors.filter(e=>e.keyword!=='if'&&!groups.some(g=>g!==e&&(e.schemaPath.startsWith(g.schemaPath+'/')||e.instancePath.startsWith(g.instancePath+'/')))).map(e=>({rule:'STRUCTURE',path:e.instancePath})));
}
async function sha256(text) {
  const digest=await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
  return [...new Uint8Array(digest)].map(v=>v.toString(16).padStart(2,'0')).join('');
}

export async function validatePayload(definition,payload,context={}) {
  const nonfinite=finiteIssues(payload);
  if (nonfinite.length) return uniqueIssues(nonfinite);
  if (!Object.hasOwn(schema.$defs,definition)) throw new Error('DEFINITION: unknown contract definition');
  if (!validators.has(definition)) validators.set(definition,ajv.compile({$ref:schema.$id+'#/$defs/'+definition}));
  const validate=validators.get(definition);
  if (!validate(payload)) return structureIssues(validate.errors);
  let document=context.document;
  let issues=[];
  const issue=(rule,path)=>issues.push({rule,path});
  if (definition==='PreparedDocument') document=payload;
  else if (isObject(payload)&&Object.hasOwn(payload,'document')) {
    const embedded=payload.document;
    const errors=await validatePayload('PreparedDocument',embedded);
    if (errors.length) return errors.map(e=>({rule:e.rule,path:'/document'+e.path}));
    if (document&&(embedded.doc_id!==document.doc_id||embedded.text_sha256!==document.text_sha256)) issue('DOCUMENT_IDENTITY','/document');
    document=embedded;
  }
  if (document&&definition!=='PreparedDocument'&&(await validatePayload('PreparedDocument',document)).length) throw new Error('DOCUMENT_CONTEXT: invalid prepared-document context');
  const unique=(values,key,path)=>{if(new Set(values.map(v=>v[key])).size!==values.length)issue('DUPLICATE_ID',path);};
  const modeMatches=(mode,records,path)=>{
    const modes=new Set(records.map(r=>r.mode));
    const expected=modes.size>1?'mixed':modes.values().next().value;
    if ((expected&&expected!==mode)||(!modes.size&&mode==='mixed')) issue('MODE_PROVENANCE',path+'/mode');
  };
  const graph=(value,records,path)=>{
    if(new Set(records.map(r=>r.component_id)).size!==records.length)issue('DUPLICATE_COMPONENT',path+'/components');
    const components=new Map(records.map(r=>[r.component_id,r]));
    const sources=new Map(value.sources.map(s=>[s.source_id,s]));
    value.sources.forEach((source,i)=>{
      const record=components.get(source.component_id);
      if(!record)issue('SOURCE_COMPONENT',path+`/sources/${i}/component_id`);
      else if((record.service==='rag')!==(source.kind==='literature'))issue('SOURCE_ORIGIN',path+`/sources/${i}/component_id`);
    });
    value.claims.forEach((claim,i)=>{
      const record=components.get(claim.component_id);
      if(!record){issue('CLAIM_COMPONENT',path+`/claims/${i}/component_id`);return;}
      if(claim.source_ids.some(id=>sources.get(id)?.component_id!==claim.component_id))issue('CLAIM_COMPONENT',path+`/claims/${i}/component_id`);
      if(claim.scope!==(record.service==='rag'?'general_information':'document_fact'))issue('COMPONENT_SCOPE',path+`/claims/${i}/scope`);
    });
  };
  async function baseWalk(value,path='') {
    if(Array.isArray(value)){for(let i=0;i<value.length;i++)await baseWalk(value[i],path+pointer(i));return;}
    if(!isObject(value))return;
    if(has(value,['canonicalization_version','text_sha256','text'])) {
      const text=value.text,validUnicode=!Array.from(text).some(c=>c.length===1&&c.charCodeAt(0)>=0xd800&&c.charCodeAt(0)<=0xdfff);
      const whitespace=/^[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]*$/u;
      if(!validUnicode)issue('TEXT_UNICODE',path+'/text');
      else if(whitespace.test(text)||text.includes('\r')||text.normalize('NFC')!==text)issue('TEXT_CANONICAL',path+'/text');
      if(validUnicode&&await sha256(text)!==value.text_sha256)issue('TEXT_DIGEST',path+'/text_sha256');
    }
    if(has(value,['doc_id','text_sha256'])&&document&&(value.doc_id!==document.doc_id||value.text_sha256!==document.text_sha256))issue('DOCUMENT_IDENTITY',path);
    if(has(value,['start','end','quote'])) {
      if(!document)throw new Error('DOCUMENT_CONTEXT: evidence requires document context');
      const chars=Array.from(document.text);
      if(!(0<=value.start&&value.start<value.end&&value.end<=chars.length))issue('SPAN_BOUNDS',path);
      else if(chars.slice(value.start,value.end).join('')!==value.quote)issue('SPAN_QUOTE',path);
    }
    if(has(value,['score_kind','scores'])&&new Set(value.scores.map(s=>s.category)).size!==value.scores.length)issue('CATEGORY_UNIQUE',path+'/scores');
    if(Array.isArray(value.items))unique(value.items,'entity_id',path+'/items');
    if(Object.hasOwn(value,'icd')) {
      const code=value.icd.code.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
      if(!new RegExp('(?<![\\w.])'+code+'(?!\\w|\\.\\w)','u').test(value.icd.evidence.quote))issue('ICD_SOURCE',path+'/icd/code');
    }
    if(has(value,['claims','sources'])) {
      unique(value.claims,'claim_id',path+'/claims');unique(value.sources,'source_id',path+'/sources');
      const sources=new Map(value.sources.map(s=>[s.source_id,s]));
      value.claims.forEach((claim,i)=>{
        if(claim.source_ids.some(id=>!sources.has(id)))issue('CITATION_MISSING',path+`/claims/${i}/source_ids`);
        else if(claim.scope==='document_fact'&&!claim.source_ids.some(id=>sources.get(id).kind==='document'))issue('CLAIM_PROVENANCE',path+`/claims/${i}/source_ids`);
      });
      if(value.evidence_state==='partial'&&!value.warnings.length)issue('PARTIAL_GAP',path+'/warnings');
    }
    if(Object.hasOwn(value,'passages'))unique(value.passages,'source_id',path+'/passages');
    for(const [key,child] of Object.entries(value))await baseWalk(child,path+pointer(key));
  }
  await baseWalk(payload);
  if(context.reference)for(const [name,rule]of [['attributes','REFERENCE_ATTRIBUTE'],['spans','REFERENCE_SPAN']])for(const [path,expected]of Object.entries(context.reference[name]??{}))if(!equal(at(payload,path),expected))issue(rule,path);
  if(issues.length)return uniqueIssues(issues);
  function extraWalk(value,path='') {
    if(Array.isArray(value)){value.forEach((v,i)=>extraWalk(v,path+pointer(i)));return;}
    if(!isObject(value))return;
    if(Object.hasOwn(value,'classification_execution')) {
      if(value.scores.length&&!equal(value.scores.map(s=>s.category),labels))issue('CATEGORY_ORDER',path+'/scores');
      if(value.status==='unsupported'&&value.mode!=='mock')issue('SCOPE_POLICY_UNAPPROVED',path+'/scope_policy_version');
    }
    if(value.mention&&!value.evidence.some(s=>s.start<=value.mention.start&&value.mention.start<value.mention.end&&value.mention.end<=s.end))issue('MENTION_EVIDENCE',path+'/mention');
    if(has(value,['claims','sources','text'])) {
      let expected;
      if(Object.hasOwn(value,'components')) {
        const records=value.components,retrieval=value.retrieval_provenance,rag=records.map((r,i)=>[i,r]).filter(([,r])=>r.service==='rag');
        graph(value,records,path);modeMatches(value.mode,[...records,...(retrieval?[retrieval]:[])],path);
        if(rag.length&&!retrieval)issue('RETRIEVAL_PROVENANCE',path+'/retrieval_provenance');
        if(retrieval) {
          if(!value.attempted_routes.includes('literature'))issue('RETRIEVAL_ATTEMPT',path+'/attempted_routes');
          if(retrieval.state==='insufficient'&&rag.length)issue('RETRIEVAL_GENERATION',path+'/components');
          for(const [i,r]of rag)for(const key of ['corpus_version','index_version','retriever_version'])if(r[key]!==retrieval[key])issue('RETRIEVAL_VERSION',path+`/components/${i}/${key}`);
        }
        expected=value.clarification?value.clarification.message:noAnswer;
        if(value.route!=='none'&&!value.claims.length)issue('ROUTE_SUPPORT',path+'/route');
        if(value.sources.some(s=>!value.attempted_routes.includes(s.kind)))issue('ATTEMPTED_ROUTE',path+'/attempted_routes');
        if(records.some(r=>!['document-answer','literature-answer'].includes(r.operation)))issue('ANSWER_OPERATION',path+'/components');
        if(value.route==='mixed') {
          if(value.prompt_version!==null)issue('ROOT_VERSION',path+'/prompt_version');
          if(value.answer_version!=='notelens-compose-v1')issue('ROOT_VERSION',path+'/answer_version');
          for(const r of records) {
            const prefix=r.service==='rag'?'a:':'d:',ids=[r.component_id,...value.sources.filter(s=>s.component_id===r.component_id).map(s=>s.source_id),...value.claims.filter(c=>c.component_id===r.component_id).map(c=>c.claim_id)];
            if(ids.some(id=>!id.startsWith(prefix)))issue('ID_NAMESPACE',path+'/components');
          }
        } else if(records.length===1) {
          if(value.answer_version!==records[0].output_version)issue('ROOT_VERSION',path+'/answer_version');
          if(value.prompt_version!==records[0].prompt_version)issue('ROOT_VERSION',path+'/prompt_version');
        } else if(!records.length&&value.prompt_version!==null)issue('ROOT_VERSION',path+'/prompt_version');
      } else {
        const records=value.provenance?[value.provenance]:[];graph(value,records,path);expected=noSummary;
        if(records.length&&(records[0].service!=='extraction'||records[0].operation!=='summarize'))issue('SUMMARY_OPERATION',path+'/provenance');
      }
      if(value.text!==(value.claims.length?value.claims.map(c=>c.text).join('\n\n'):expected))issue('TEXT_CLAIMS',path+'/text');
    }
    if(Object.hasOwn(value,'extraction_status')) {
      const r=value.extraction_provenance;
      if(value.items.length&&(!r||value.items.some(i=>i.component_id!==r.component_id)))issue('ITEM_COMPONENT',path+'/extraction_provenance');
      if(r&&(r.service!=='extraction'||r.operation!=='extract'))issue('EXTRACTION_OPERATION',path+'/extraction_provenance');
      if(r&&r.output_version!==value.extractor_version)issue('ROOT_VERSION',path+'/extractor_version');
      if((r&&r.prompt_version!==value.prompt_version)||(!r&&value.prompt_version!==null))issue('ROOT_VERSION',path+'/prompt_version');
      const summary=value.summary.result?.provenance;modeMatches(value.mode,[r,summary].filter(Boolean),path);
    }
    for(const [key,child]of Object.entries(value))extraWalk(child,path+pointer(key));
  }
  extraWalk(payload);
  return uniqueIssues(issues);
}

export class ContractValidationError extends Error {
  constructor(issues){super('Contract validation failed: '+issues.map(i=>i.rule+'@'+(i.path||'/')).join(', '));this.issues=issues;}
}
export async function validateRecord(definition,payload,context) {
  const issues=await validatePayload(definition,payload,context);
  if(issues.length)throw new ContractValidationError(issues);
  return payload;
}
export async function validateJson(definition,text,context) {
  let payload;
  try {
    payload=JSON.parse(text);
    if(finiteIssues(payload).length)throw new Error();
    const stack=[];
    for(const token of text.matchAll(/"(?:\\.|[^"\\])*"|[{}\[\],:]|[^{}\[\],:\s]+/g)) {
      const t=token[0],top=stack.at(-1);
      if(t==='{')stack.push({object:true,key:true,keys:new Set()});
      else if(t==='[')stack.push({object:false});
      else if(t==='}'||t===']')stack.pop();
      else if(t===','&&top?.object)top.key=true;
      else if(t.startsWith('"')&&top?.object&&top.key){const key=JSON.parse(t);if(top.keys.has(key))throw new Error();top.keys.add(key);top.key=false;}
    }
  }catch{throw new ContractValidationError([{rule:'JSON_INPUT',path:''}]);}
  return validateRecord(definition,payload,context);
}

export async function validateExchange(exchange) {
  const requestId=headers=>{
    const values=headers.filter(([name])=>name.toLowerCase()==='x-request-id').map(([,value])=>value);
    return values.length===1&&typeof values[0]==='string'&&new RegExp(schema.$defs.RequestId.pattern).test(values[0])?values[0]:null;
  };
  const incoming=requestId(exchange.request_headers),outgoing=requestId(exchange.response_headers);
  if(!outgoing)return ['RESPONSE_ID'];
  const body=exchange.body;
  if(['/health/live','/health/ready'].includes(exchange.path)) {
    if(exchange.status!==401)return ['HEALTH_AUTH_STATUS'];
    const challenges=exchange.response_headers.filter(([name])=>name.toLowerCase()==='www-authenticate').map(([,value])=>value);
    if(!equal(challenges,['Bearer']))return ['AUTH_CHALLENGE'];
    if((await validatePayload('ErrorEnvelope',body)).length)return ['ERROR_ENVELOPE'];
    if(body.request_id!==outgoing)return ['ERROR_CORRELATION'];
    if(body.error.code!=='unauthorized'||body.error.retryable)return ['HEALTH_AUTH_ERROR'];
    if(exchange.request_headers.some(([name,value])=>name.toLowerCase()==='x-request-id'&&value===outgoing))return ['HEALTH_AUTH_ID_REUSED'];
    return exchange.disposition==='failed_call'?[]:['CALL_DISPOSITION'];
  }
  if(!incoming) {
    if(exchange.status===200)return ['INVALID_REQUEST_SUCCESS'];
    if(exchange.status!==400)return ['INVALID_REQUEST_STATUS'];
  } else if(incoming!==outgoing)return ['CORRELATION_MISMATCH'];
  if(exchange.status!==200) {
    if((await validatePayload('ErrorEnvelope',body)).length)return ['ERROR_ENVELOPE'];
    if(body.request_id!==outgoing)return ['ERROR_CORRELATION'];
    if(!incoming&&body.error.code!=='validation_failure')return ['INVALID_REQUEST_ERROR'];
  }
  return exchange.disposition===(exchange.status===200?'accepted_result':'failed_call')?[]:['CALL_DISPOSITION'];
}
