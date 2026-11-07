import { Link } from 'react-router-dom'
import Icon from './Icon'
import { Chart, Skeleton } from './ui'
import { num, pct } from '../lib/fmt'
import { baselineEvidence } from '../lib/overview'

export function StatCard({ label, value, note, icon, tone='purple', change, full, invert=false }) {
  const direction = change && invert ? (change.value < 0 ? 'good' : change.value > 0 ? 'bad' : '') : ''
  return <div className={`stat-card tone-${tone}`} title={note}>
    <span className="stat-icon"><Icon name={icon} size={20}/></span>
    <div className="stat-copy"><span className="stat-label">{label}</span><strong className="stat-value" title={full || note}>{value}</strong>
      {change ? <span className={`period-change ${direction}`} title="So sánh hai kỳ có cùng độ dài">{change.value > 0 ? '↑' : change.value < 0 ? '↓' : '→'} {Math.abs(change.value)>0 && Math.abs(change.value)<.1 ? '<0,1' : num(Math.abs(change.value),1)}{change.unit === '%' ? '%' : ' đpt'} <span>so với kỳ trước</span></span> : <small>{note}</small>}
    </div>
  </div>
}
export function ChartCard({ title, sub, icon='chart', action, children, className='' }) {
  return <section className={`card executive-card ${className}`}><div className="executive-card-header"><span className="section-icon"><Icon name={icon} size={17}/></span><div><h3>{title}</h3>{sub && <p>{sub}</p>}</div>{action && <div className="card-action">{action}</div>}</div>{children}</section>
}
export function ErrorState({ message, onRetry, title='Không tải được dữ liệu' }) {
  return <div className="state-box error-state" role="alert"><span className="state-icon"><Icon name="info" size={22}/></span><b>{title}</b><p>{message}</p>{onRetry && <button className="btn" onClick={onRetry}>Thử lại</button>}</div>
}
export function EmptyState({ title='Chưa có dữ liệu', children, action }) {
  return <div className="state-box"><span className="state-icon"><Icon name="chart" size={24}/></span><b>{title}</b>{children && <p>{children}</p>}{action}</div>
}
export function NextLink({ to, children, className='' }) { return <Link className={`text-link ${className}`} to={to}>{children}<Icon name="arrow" size={13}/></Link> }
export function SourceNote({ children }) { return <p className="executive-source"><Icon name="info" size={12}/><span>{children}</span></p> }
export function StrategyEvidence({ resource, retry, fund, onFundChange }) {
  const e = baselineEvidence(resource.data, fund)
  const verified = resource.data?.baseline_source === 'csv'
  return <ChartCard className="strategy-card" title="So sánh chiến lược B0 – B3" icon="wallet">
    {resource.loading ? <Skeleton h={180}/> : resource.error ? <ErrorState title="Chưa tải được minh chứng" message={resource.error} onRetry={retry}/> : !e.rows.length ? <EmptyState title="Chưa có so sánh phương án"/> : <>
      <div className="evidence-controls"><span className={`evidence-tag ${verified ? '' : 'unverified'}`}>{verified ? 'BACKTEST · CSV' : 'CHỈ THAM KHẢO'}</span><label>Quỹ <select aria-label="Quỹ vốn thí nghiệm" value={e.fund} onChange={event=>onFundChange(Number(event.target.value))}>{e.funds.map(f=><option key={f} value={f}>{num(f,1)} tỷ ₫</option>)}</select></label></div>
      <div className="strategy-table-wrap"><table className="strategy-table"><thead><tr><th>Chiến lược</th><th>Lợi ích ròng<br/><small>triệu ₫</small></th><th>TARGET<br/><small>theo vốn</small></th><th>KH tốt<br/><small>bị từ chối</small></th></tr></thead><tbody>{e.rows.map(r=><tr key={r.phuong_an} className={verified && e.favorable && /^B3\b/.test(r.phuong_an) ? 'strategy-highlight' : ''}><td title={r.phuong_an}><b>{r.phuong_an.slice(0,2)}</b><span>{/^B0/.test(r.phuong_an)?'FIFO':/^B1/.test(r.phuong_an)?'Quy tắc':/^B2/.test(r.phuong_an)?'ML + FIFO':'Aura + MILP'}</span></td><td>{num(r.loi_nhuan_that_trieu,2)}</td><td>{pct(r.no_xau_that_gia_tri,2)}</td><td>{pct(r.khach_tot_bi_tu_choi,1)}</td></tr>)}</tbody></table></div>
      <div className="evidence-footer"><span>{verified ? `${e.seeds != null ? `${num(e.seeds)} seed · ` : ''}Độc lập với kỳ lọc` : 'Chưa có CSV kiểm chứng'}</span><NextLink to="/danh-gia">Cơ sở</NextLink></div>
    </>}
  </ChartCard>
}
export function LabeledChart({ option, height='100%', label, onEvents }) {
  return <div className="labeled-chart" role="img" aria-label={label}><Chart option={{ ...option, animationDuration:250, textStyle:{ fontFamily:'Inter, Segoe UI, Arial, sans-serif', ...option.textStyle } }} height={height} onEvents={onEvents}/></div>
}
