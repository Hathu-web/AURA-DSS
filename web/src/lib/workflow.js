import { isNumber } from './fmt.js'
export function optimizationRequest(p,range={}) {
  return {liquidity:Number(p.liquidity)*1e9,risk_ceiling:Number(p.risk_ceiling),lgd:Number(p.lgd),n:Number(p.n),seed:Number(p.seed),...(p.useRange?{d_from:range.d_from||'',d_to:range.d_to||''}:{})}
}
export const requestKey=r=>JSON.stringify(Object.entries(r).sort(([a],[b])=>a.localeCompare(b)))
export function optimizationFacts(k) {
  const hasSelection=isNumber(k?.so_don_duyet)&&Number(k.so_don_duyet)>0
  const risk=hasSelection&&isNumber(k?.no_xau_du_doan)?Number(k.no_xau_du_doan):null
  const target=hasSelection&&isNumber(k?.no_xau_that)?Number(k.no_xau_that):null
  const budget=isNumber(k?.tham_so?.liquidity)?Number(k.tham_so.liquidity):null
  const ceiling=isNumber(k?.tham_so?.risk_ceiling)?Number(k.tham_so.risk_ceiling):null
  return {hasSelection,risk,target,unused:budget!==null&&isNumber(k?.von)?budget-Number(k.von):null,headroom:risk!==null&&ceiling!==null?ceiling-risk:null}
}
export function csvText(rows,columns) {
  const escape=value=>{let t=value==null?'':String(value);if(typeof value==='string'&&/^[\s]*[=+\-@]/.test(t))t="'"+t;return '"'+t.replaceAll('"','""')+'"'}
  return '\ufeff'+[columns.map(c=>escape(c.label||c.key)).join(','),...rows.map(r=>columns.map(c=>escape(r[c.key])).join(','))].join('\r\n')
}
export const csvHref=(rows,cols)=>'data:text/csv;charset=utf-8,'+encodeURIComponent(csvText(rows,cols))
export function groupDecisionLog(rows=[]) {
  return Object.values(rows.reduce((a,r)=>{const id=r.batch_id||'Chưa rõ batch',b=a[id]||(a[id]={batch:id,n:0,selected:0,other:0,unknown:0,fees:0});b.n++;if(r.decision===true||r.decision===1)b.selected++;else if(r.decision===false||r.decision===0)b.other++;else b.unknown++;if(isNumber(r.fee_amount))b.fees+=Number(r.fee_amount);return a},{}))
}
