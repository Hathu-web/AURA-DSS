import ReactECharts from 'echarts-for-react'
import { tierCode, pct } from '../lib/fmt'

export const Card = ({ title, sub, right, children, className='', style }) => (
  <div className={`card ${className}`} style={style}>
    {(title || right) && <div className="head"><div>{title && <h3>{title}</h3>}{sub && <p className="sub" style={{marginBottom:0}}>{sub}</p>}</div>{right}</div>}
    {children}
  </div>
)
export const Chart = ({ option, height=260, onEvents, style }) => (
  <ReactECharts option={option} style={{ height, width:'100%', ...style }} notMerge lazyUpdate onEvents={onEvents} opts={{ renderer:'svg' }} />
)
export const Delta = ({ v, invert=false, suffix='pt' }) => {
  if (v == null || isNaN(v)) return <span className="delta flat">–</span>
  const good = invert ? v < 0 : v > 0
  const cls = Math.abs(v) < 1e-9 ? 'flat' : good ? 'up' : 'down'
  return <span className={`delta ${cls}`}>{v > 0 ? '▲' : v < 0 ? '▼' : '•'} {Math.abs(v).toFixed(suffix==='%'?1:2)}{suffix}</span>
}
export const KPI = ({ label, value, sub, delta, invert, suffix, color='#2563EB', icon }) => (
  <div className="card kpi" style={{ '--kpi-c': color }}>
    <div className="lbl"><span>{label}</span>{icon && <span className="ico" style={{ background: color }}>{icon}</span>}</div>
    <div className="val">{value}</div>
    <p className="sub">{delta !== undefined && <><Delta v={delta} invert={invert} suffix={suffix} /> </>}{sub}</p>
  </div>
)
export const Tier = ({ t }) => { const c = tierCode(t); return <span className={`tag ${c}`}>{c === 'NA' ? '–' : c}</span> }
export const Model = ({ m }) => <span className={`tag ${m==='thin'?'thin':m==='thick'?'thick':'NA'}`}>{m === 'thin' ? 'Thin-file' : m === 'thick' ? 'Thick-file' : 'Chưa rõ'}</span>
export const Skeleton = ({ h=240 }) => <div className="skel" style={{ height: h }} />
export const Empty = ({ children='Chưa có dữ liệu' }) => <div className="empty">{children}</div>
export const Table = ({ cols, rows=[], max=420, keyFn }) => (
  <div className="scroll" style={{ maxHeight: max }}>
    <table className="t"><thead><tr>{cols.map(c => <th key={c.k} className={c.num ? 'num' : ''}>{c.h}</th>)}</tr></thead>
      <tbody>{rows.map((r, i) => <tr key={keyFn ? keyFn(r) : i}>{cols.map(c => <td key={c.k} className={c.num ? 'num' : ''}>{c.f ? c.f(r[c.k], r) : r[c.k]}</td>)}</tr>)}</tbody></table>
    {!rows.length && <Empty />}
  </div>
)
export const Prog = ({ v, color }) => <div className="prog"><i style={{ width: `${Math.min(100, Math.max(0, v*100))}%`, background: color }} /></div>
export const ThreeBar = ({ counts }) => { // counts {LOW,MEDIUM,HIGH}
  const tot = (counts.LOW||0)+(counts.MEDIUM||0)+(counts.HIGH||0) || 1
  return <div style={{ display:'flex', height:10, borderRadius:999, overflow:'hidden' }}>
    {['LOW','MEDIUM','HIGH'].map(k => <div key={k} title={`${k}: ${pct((counts[k]||0)/tot)}`} style={{ width: `${(counts[k]||0)/tot*100}%`, background: { LOW:'#16A34A', MEDIUM:'#F59E0B', HIGH:'#EF4444' }[k] }} />)}
  </div>
}
