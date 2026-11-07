import test from 'node:test'
import assert from 'node:assert/strict'
import { num, pct, vnd, displayDate } from '../src/lib/fmt.js'
import { deriveOverview, periodChange, baselineEvidence, merchantUrl } from '../src/lib/overview.js'

test('Missing metrics remain unavailable; zero remains a valid measurement', () => {
  for (const v of [null,undefined,NaN,Infinity,'']) assert.equal(pct(v),'–')
  assert.equal(pct(0,2),'0,00%')
  assert.equal(num(2016),'2.016')
  assert.equal(vnd(10739500000),'10,74 tỷ')
})
test('Table callback row cannot cause Intl precision RangeError', () => {
  assert.equal(num(1234567,{ amount:1234567 }),'1.234.567')
  assert.doesNotThrow(()=>num(5,-100))
  assert.doesNotThrow(()=>num(5,100000))
})
test('Dates do not invent an unavailable timestamp', () => {
  assert.equal(displayDate('2026-10-10'),'10/10/2026')
  assert.equal(displayDate(null),'—')
})
test('Selected weighted risk is compared only with selected weighted TARGET', () => {
  const d=deriveOverview({ kpi:{p_tb:.08,no_xau_du_doan_duyet:.0298,no_xau_that_duyet:.0401},funnel:[{},{},{so:100}] })
  assert.ok(Math.abs(d.gap*100 - 1.03)<1e-10)
})
test('No selected transactions cannot imply a safe portfolio', () => {
  assert.equal(deriveOverview({kpi:{no_xau_du_doan_duyet:0,no_xau_that_duyet:0},funnel:[{},{},{so:0}]}).gap,null)
  assert.equal(deriveOverview({kpi:{no_xau_du_doan_duyet:.03}}).gap,null)
})
test('Top merchant is ranked by risk, not original API order by value', () => {
  const merchants=[{merchant_id:'BIG',p_tb:.04,gia_tri:9e9},{merchant_id:'RISK',p_tb:.09,gia_tri:1e6},{merchant_id:'UNKNOWN',p_tb:null}]
  assert.equal(deriveOverview({merchants}).topMerchant.merchant_id,'RISK')
  assert.equal(merchants[0].merchant_id,'BIG')
})
test('Missing previous period produces no fabricated delta', () => {
  assert.equal(periodChange({p_tb:.1},null,'p_tb',true),null)
  assert.equal(deriveOverview({kpi_truoc:{so_giao_dich:0}}).previous,null)
  assert.equal(periodChange({gia_tri:3},{gia_tri:0},'gia_tri'),null)
})
test('Percentage-point differences and relative growth use different units', () => {
  assert.deepEqual(periodChange({p:.04},{p:.02},'p',true),{value:2,unit:'đpt'})
  assert.deepEqual(periodChange({amount:120},{amount:100},'amount'),{value:20,unit:'%'})
})
test('Backtest isolates fund and preserves adverse selection trade-off', () => {
  const data={baseline:[{quy_ty:2,phuong_an:'B2 Test',loi_nhuan_that_trieu:40,no_xau_that_gia_tri:.035,ty_le_duyet:.7},{quy_ty:2,phuong_an:'B3 Test',loi_nhuan_that_trieu:42,no_xau_that_gia_tri:.028,ty_le_duyet:.62},{quy_ty:1.5,phuong_an:'B3 Other',loi_nhuan_that_trieu:900}],baseline_seeds_per_fund:{'2.0':20}}
  const e=baselineEvidence(data,2)
  assert.equal(e.rows.length,2);assert.equal(e.seeds,20);assert.equal(e.gainPercent,5)
  assert.ok(e.selectionDelta<0);assert.ok(e.riskDelta<0);assert.equal(e.favorable,true)
})
test('Do not declare B3 favorable when risk worsens or evidence is missing', () => {
  const e=baselineEvidence({baseline:[{quy_ty:2,phuong_an:'B2',loi_nhuan_that_trieu:40,no_xau_that_gia_tri:.03},{quy_ty:2,phuong_an:'B3',loi_nhuan_that_trieu:42,no_xau_that_gia_tri:.04}]},2)
  assert.equal(e.favorable,false)
  assert.equal(baselineEvidence(undefined,2).profitDelta,null)
})
test('Merchant drilldown safely preserves arbitrary merchant IDs', () => {
  assert.equal(merchantUrl('A&B / 1'),'/danh-muc?merchant=A%26B%20%2F%201')
})
