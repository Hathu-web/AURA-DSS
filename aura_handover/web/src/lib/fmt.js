export const C = { low:'#16A34A', medium:'#F59E0B', high:'#EF4444', thick:'#2563EB', thin:'#8B5CF6', brand:'#5418E5', brand2:'#9690E9', teal:'#0D9488', amber:'#F59E0B', rose:'#EF4444', green:'#16A34A', cyan:'#06B6D4', pink:'#EC4899', indigo:'#6366F1', slate:'#94A3B8' }
export const PALETTE = ['#2563EB','#7C3AED','#0D9488','#F59E0B','#EC4899','#06B6D4','#84CC16','#F97316','#6366F1','#14B8A6']
export const TIER = { LOW:{ label:'Low', vi:'An toàn', c:C.low }, MEDIUM:{ label:'Medium', vi:'Thăm dò', c:C.medium }, HIGH:{ label:'High', vi:'Nguy cơ', c:C.high } }
export const tierCode = (t='') => /Low|LOW/.test(t) ? 'LOW' : /Medium|MEDIUM/.test(t) ? 'MEDIUM' : /High|HIGH/.test(t) ? 'HIGH' : 'NA'
// Clamp precision: table render callbacks may pass a row as their second argument.
const digits = (d, fallback=0) => Number.isInteger(d) ? Math.max(0, Math.min(10, d)) : fallback
export const isNumber = v => v !== null && v !== undefined && v !== '' && Number.isFinite(Number(v))
export const num = (v, d=0) => !isNumber(v) ? '–' : Number(v).toLocaleString('vi-VN', { maximumFractionDigits:digits(d), minimumFractionDigits:digits(d) })
export const pct = (v, d=1) => !isNumber(v) ? '–' : num(Number(v)*100, digits(d,1)) + '%'
export const vnd = v => !isNumber(v) ? '–' : Math.abs(v) >= 1e9 ? num(v/1e9,2)+' tỷ' : Math.abs(v) >= 1e6 ? num(v/1e6,1)+' tr' : num(v)
export const vndFull = v => !isNumber(v) ? '–' : num(v) + ' ₫'
export const ms = v => !isNumber(v) ? '–' : v < 1000 ? num(v)+' ms' : num(v/1000,1)+' s'
export const displayDate = v => /^\d{4}-\d{2}-\d{2}/.test(v || '') ? v.slice(0,10).split('-').reverse().join('/') : '—'
export const dateStr = (d) => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
export const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate()+n); return x }
export const baseGrid = { left: 8, right: 16, top: 28, bottom: 4, containLabel: true }
export const catAxis = { axisLine:{ show:false }, axisTick:{ show:false }, axisLabel:{ color:'#94A3B8', fontSize:11, interval:0, hideOverlap:true }, splitLine:{ show:false } }
export const axisStyle = { axisLine:{ show:false }, axisTick:{ show:false }, axisLabel:{ color:'#94A3B8', fontSize:11, hideOverlap:true }, splitLine:{ lineStyle:{ color:'#F1F5F9' } } }
export const tooltip = { trigger:'axis', backgroundColor:'#0F172A', borderWidth:0, textStyle:{ color:'#fff', fontSize:12 }, padding:[8,12], extraCssText:'border-radius:10px;box-shadow:0 10px 30px -10px rgba(0,0,0,.4)' }

export const legendTop = { top: 0, left: 'center', icon: 'roundRect', itemWidth: 10, itemHeight: 10, itemGap: 14, textStyle: { color: '#64748B', fontSize: 11 } }
export const gridLegend = { left: 8, right: 16, top: 40, bottom: 4, containLabel: true }
export const pieLegend = { bottom: 0, left: 'center', icon: 'circle', itemWidth: 8, itemHeight: 8, itemGap: 10, textStyle: { color: '#475569', fontSize: 11 } }
