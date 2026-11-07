import { isNumber } from './fmt.js'

export const MERCHANT_NAMES = { SHOPEE:'Shopee', LAZADA:'Lazada', TIKTOK_SHOP:'TikTok Shop', TIKI:'Tiki', GRAB:'Grab', HIGHLANDS:'Highlands' }
export const merchantName = id => MERCHANT_NAMES[id] || id || 'Chưa rõ merchant'
export const merchantUrl = id => '/danh-muc' + (id ? '?merchant=' + encodeURIComponent(id) : '')
export const numeric = v => isNumber(v) ? Number(v) : null
export const difference = (a, b) => isNumber(a) && isNumber(b) ? Number(a) - Number(b) : null

export function deriveOverview(data = {}) {
  const kpi = data.kpi || {}
  const previous = data.kpi_truoc?.so_giao_dich > 0 ? data.kpi_truoc : null
  const merchants = [...(data.merchants || [])].sort((a, b) => (numeric(b.p_tb) ?? -Infinity) - (numeric(a.p_tb) ?? -Infinity))
  const tiers = ['LOW','MEDIUM','HIGH'].map(t => (data.tiers || []).find(x => x.tier === t)).filter(Boolean)
  const selected = data.funnel?.find(x => x.buoc === 'Đề xuất phân bổ')?.so ?? data.funnel?.[2]?.so ?? null
  const gap = selected !== 0 ? difference(kpi.no_xau_that_duyet, kpi.no_xau_du_doan_duyet) : null
  const tierGap = tiers.filter(t => isNumber(t.p_tb) && isNumber(t.bad)).sort((a,b) => Math.abs(b.bad-b.p_tb) - Math.abs(a.bad-a.p_tb))[0]
  return { kpi, previous, merchants, tiers, selected, gap, tierGap, topMerchant: merchants.find(m => isNumber(m.p_tb)) }
}

export function periodChange(current, previous, key, rate=false) {
  if (!previous || !isNumber(current?.[key]) || !isNumber(previous[key])) return null
  if (rate) return { value:(current[key] - previous[key])*100, unit:'đpt' }
  if (previous[key] <= 0) return null
  return { value:(current[key] - previous[key]) / previous[key]*100, unit:'%' }
}

export function baselineEvidence(data, requestedFund) {
  const funds = [...new Set((data?.baseline || []).map(r => numeric(r.quy_ty)).filter(v => v !== null))].sort((a,b) => a-b)
  const fund = funds.includes(Number(requestedFund)) ? Number(requestedFund) : funds.includes(2) ? 2 : funds[0]
  const rows = (data?.baseline || []).filter(r => numeric(r.quy_ty) === fund).sort((a,b) => a.phuong_an.localeCompare(b.phuong_an))
  const b2 = rows.find(r => /^B2\b/.test(r.phuong_an))
  const b3 = rows.find(r => /^B3\b/.test(r.phuong_an))
  const profitDelta = difference(b3?.loi_nhuan_that_trieu, b2?.loi_nhuan_that_trieu)
  const riskDelta = difference(b3?.no_xau_that_gia_tri, b2?.no_xau_that_gia_tri)
  const selectionDelta = difference(b3?.ty_le_duyet, b2?.ty_le_duyet)
  const seeds = Object.entries(data?.baseline_seeds_per_fund || {}).find(([key]) => Number(key) === fund)?.[1]
  return { funds, fund, rows, b2, b3, profitDelta, riskDelta, selectionDelta, seeds,
    gainPercent: isNumber(b2?.loi_nhuan_that_trieu) && b2.loi_nhuan_that_trieu > 0 && profitDelta !== null ? profitDelta/b2.loi_nhuan_that_trieu*100 : null,
    favorable: profitDelta !== null && riskDelta !== null && profitDelta > 0 && riskDelta <= 0 }
}
