import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useStore, useApi } from '../lib/store'
import { Skeleton } from '../components/ui'
import Icon from '../components/Icon'
import MerchantMark from '../components/MerchantMark'
import { StatCard, ChartCard, ErrorState, EmptyState, NextLink, StrategyEvidence, LabeledChart } from '../components/executive'
import { pct, num, vnd, vndFull, isNumber } from '../lib/fmt'
import { deriveOverview, merchantName, merchantUrl, periodChange, baselineEvidence } from '../lib/overview'

const purple = '#6544E9'
const lavender = '#B9ABF2'
const tierColors = { LOW:'#16A36A', MEDIUM:'#C28B12', HIGH:'#DB5866' }
const axis = { axisLine:{ show:false }, axisTick:{ show:false }, axisLabel:{ color:'#88849C', fontSize:9 }, splitLine:{ lineStyle:{ color:'#EFEDF6' } } }
const tip = { trigger:'axis', renderMode:'richText', backgroundColor:'#fff', borderColor:'#EAE5F4', textStyle:{ color:'#39304F', fontSize:11 }, valueFormatter:v=>pct(v,2) }
const reviewFirst = (m,k) => isNumber(m.p_tb) && isNumber(k.p_tb) && isNumber(m.high) && isNumber(k.ty_le_high) && m.p_tb > k.p_tb && m.high > k.ty_le_high

function Priority({ number, title, children, to, action, tone='' }) {
  return <div className={`priority-item ${tone}`}><span className="priority-number">{number}</span><div className="priority-copy"><h4>{title}</h4><p>{children}</p></div><Link className="priority-action" to={to}><Icon name={number === '3' ? 'chart' : 'target'} size={14}/>{action}</Link></div>
}

export default function Overview() {
  const { range, setPreset } = useStore()
  const [reload, setReload] = useState(0)
  const [evidenceReload, setEvidenceReload] = useState(0)
  const [sort, setSort] = useState('p_tb')
  const [fund, setFund] = useState(2)
  const navigate = useNavigate()
  const resource = useApi('summary', range, [range.d_from, range.d_to, reload])
  const evidence = useApi('evaluation', {}, [evidenceReload])
  const retry = () => setReload(x=>x+1)
  if (resource.loading) return <div className="overview-story" aria-label="Đang tải Tổng quan" aria-busy="true"><div className="overview-kpis">{Array.from({length:6},(_,i)=><Skeleton key={i} h={90}/>)}</div><div className="overview-charts">{[0,1,2].map(i=><Skeleton key={i} h={250}/>)}</div><Skeleton h={230}/></div>
  if (resource.error) return <ErrorState message={resource.error} onRetry={retry}/>
  if (!resource.data?.kpi) return <ErrorState title="Chưa có dữ liệu KPI" message="Nguồn hiện tại chưa cung cấp cấu trúc dữ liệu Tổng quan." onRetry={retry}/>
  const { kpi:k, previous, merchants, tiers, topMerchant, tierGap, selected, gap } = deriveOverview(resource.data)
  if (!k.so_giao_dich) return <EmptyState title="Không có giao dịch trong khoảng thời gian này" action={<button className="btn primary" onClick={()=>setPreset('all')}>Xem toàn bộ thời gian</button>}>Chọn một khoảng ngày có dữ liệu. Các tỷ lệ rủi ro chưa được xác định khi không có giao dịch.</EmptyState>
  const top = merchants.slice(0,6)
  const ranked = [...merchants].sort((a,b)=>(isNumber(b[sort])?Number(b[sort]):-Infinity)-(isNumber(a[sort])?Number(a[sort]):-Infinity))
  const e = baselineEvidence(evidence.data, fund)
  const verified = evidence.data?.baseline_source === 'csv' && !evidence.error && !evidence.loading
  const merchantChart = {
    tooltip:tip, grid:{ top:22, right:9, left:32, bottom:3 },
    xAxis:{ type:'category', ...axis, data:top.map(m=>merchantName(m.merchant_id)), axisLabel:{show:false} },
    yAxis:{ type:'value', ...axis, min:0, max:v=>v.max>0?Math.min(1,Math.ceil(v.max/0.02+1)*0.02):.1, splitNumber:3, axisLabel:{ ...axis.axisLabel, formatter:v=>pct(v,0) } },
    series:[{ name:'Rủi ro dự báo TB', type:'bar', barMaxWidth:43, barCategoryGap:'30%', data:top.map((m,i)=>({ value:isNumber(m.p_tb)?Number(m.p_tb):null, itemStyle:{ color:i===0 && reviewFirst(m,k) ? '#E96672' : ['#6847ED','#7859EC','#8C73ED','#9D88EF','#AD9BF0','#BDAEF3'][i], borderRadius:[3,3,0,0] } })), label:{ show:true, position:'top', fontSize:10, fontWeight:650, color:'#443767', formatter:p=>pct(p.value,2) } }],
  }
  const tierChart = {
    tooltip:tip,
    legend:{ top:0, left:'center', itemWidth:7, itemHeight:7, itemGap:10, textStyle:{ fontSize:9, color:'#7B7390' } },
    grid:{ top:46, right:34, left:32, bottom:23 },
    xAxis:{ type:'category', ...axis, data:tiers.map(t=>t.tier), axisLabel:{ fontSize:10, fontWeight:650, color:t=>tierColors[t], margin:9 } },
    yAxis:[{ type:'value', ...axis, name:'Rủi ro (%)', nameGap:10, nameTextStyle:{fontSize:8,color:'#91889F'}, axisLabel:{ ...axis.axisLabel, formatter:v=>pct(v,0) } }, { type:'value', ...axis, min:0, max:1, interval:.25, name:'Chọn (%)', nameGap:10, nameTextStyle:{fontSize:8,color:'#91889F'}, splitLine:{show:false}, axisLabel:{...axis.axisLabel,formatter:v=>pct(v,0)} }],
    series:[{ name:'Dự báo', type:'bar', barMaxWidth:27, itemStyle:{color:purple,borderRadius:[3,3,0,0]}, data:tiers.map(t=>t.p_tb), label:{show:true,position:'top',fontSize:9,color:'#4D3B79',formatter:p=>pct(p.value,1)} }, { name:'TARGET lịch sử', type:'bar', barMaxWidth:27, itemStyle:{color:lavender,borderRadius:[3,3,0,0]}, data:tiers.map(t=>t.bad), label:{show:true,position:'top',fontSize:9,color:'#7E6D9D',formatter:p=>pct(p.value,1)} }, {name:'Tỷ lệ chọn',type:'line',yAxisIndex:1,symbolSize:7,itemStyle:{color:'#9F94DE',borderColor:'#fff',borderWidth:1.5},lineStyle:{width:1.7},data:tiers.map(t=>t.duyet)}],
  }
  const metricCards = [
    {label:'Tổng giao dịch',value:num(k.so_giao_dich),note:'Giao dịch trong kỳ',icon:'swap',key:'so_giao_dich'},
    {label:'Tổng giá trị',value:vnd(k.gia_tri),note:'Tổng giá trị giao dịch · VNĐ',full:vndFull(k.gia_tri),icon:'coins',key:'gia_tri'},
    {label:'Tỷ lệ đề xuất chọn',value:pct(k.ty_le_duyet,1),note:`${num(selected)} giao dịch được chọn`,icon:'check',tone:'green',key:'ty_le_duyet',rate:true},
    {label:'Rủi ro dự báo',value:pct(k.no_xau_du_doan_duyet,2),note:'Xác suất dự báo · theo vốn được chọn',icon:'shield',tone:'red',key:'no_xau_du_doan_duyet',rate:true,invert:true},
    {label:'TARGET hậu kiểm',value:pct(k.no_xau_that_duyet,2),note:'TARGET lịch sử · theo vốn được chọn',icon:'target',key:'no_xau_that_duyet',rate:true,invert:true},
    {label:'Vốn được đề xuất',value:vnd(k.von_duyet),note:'Tổng số tiền được chọn · VNĐ',full:vndFull(k.von_duyet),icon:'chart',tone:'green',key:'von_duyet'},
  ]
  return <div className="overview-story">
    <section className="overview-kpis" aria-label="Hiện trạng doanh nghiệp">{metricCards.map(({key,...m})=><StatCard key={key} {...m} change={periodChange(k,previous,key,m.rate)}/>)}</section>
    <div className="overview-charts">
      <ChartCard title="Rủi ro trung bình theo Merchant" icon="chart" sub="Xác suất dự báo · giao dịch trong kỳ" className="merchant-chart-card">
        {!top.length ? <EmptyState title="Chưa có dữ liệu merchant"/> : <><LabeledChart option={merchantChart} label={top.map(m=>`${merchantName(m.merchant_id)}: ${pct(m.p_tb,2)}`).join('; ')} onEvents={{click:p=>navigate(merchantUrl(top[p.dataIndex]?.merchant_id))}}/>
          <div className="merchant-chart-labels" style={{gridTemplateColumns:`repeat(${top.length},minmax(0,1fr))`}}>{top.map(m=><Link to={merchantUrl(m.merchant_id)} key={m.merchant_id} title={`Phân tích ${merchantName(m.merchant_id)}`}><MerchantMark id={m.merchant_id}/><span>{merchantName(m.merchant_id)}</span></Link>)}</div>
          <div className="chart-caption">Toàn danh mục <b>{pct(k.p_tb,2)}</b><NextLink to={merchantUrl(topMerchant?.merchant_id)}>Phân tích</NextLink></div></>}
      </ChartCard>
      <ChartCard title="Hiệu suất theo phân tầng" sub="Dự báo, TARGET và tỷ lệ đề xuất chọn" icon="shield" className="tier-chart-card">
        {!tiers.length ? <EmptyState title="Chưa có dữ liệu phân tầng"/> : <><LabeledChart option={tierChart} label={tiers.map(t=>`${t.tier}: dự báo ${pct(t.p_tb,2)}, TARGET ${pct(t.bad,2)}, chọn ${pct(t.duyet,1)}`).join('; ')}/><div className="chart-caption">Dự báo & TARGET theo giao dịch<NextLink to="/danh-muc">Chi tiết</NextLink></div></>}
      </ChartCard>
      <StrategyEvidence resource={evidence} retry={()=>setEvidenceReload(x=>x+1)} fund={fund} onFundChange={setFund}/>
    </div>
    <div className="overview-actions">
      <ChartCard title="Insight & hành động đề xuất" icon="spark" className="priorities-card" action={<Link className="ai-pill" to="/tro-ly"><Icon name="spark" size={12}/>AURA AI</Link>}>
        <div className="priorities-list">
          <Priority number="1" tone="attention" title={tierGap ? `Tầng ${tierGap.tier} có độ lệch lớn nhất` : 'Đối chiếu dự báo với hậu kiểm'} to="/danh-gia" action="Đối chiếu">{tierGap ? `Dự báo ${pct(tierGap.p_tb,2)}; TARGET ${pct(tierGap.bad,2)}. Kiểm tra tập đánh giá và hiệu chuẩn trước khi chỉnh chính sách.` : 'Cần thêm nhãn hậu kiểm để đối chiếu chất lượng dự báo.'}</Priority>
          <Priority number="2" title={topMerchant ? `${merchantName(topMerchant.merchant_id)} có rủi ro TB cao nhất` : 'Kiểm tra mức tập trung rủi ro'} to={merchantUrl(topMerchant?.merchant_id)} action="Rà soát">{topMerchant ? `${pct(topMerchant.p_tb,2)} rủi ro dự báo; ${pct(topMerchant.high,1)} thuộc HIGH. Xem cơ cấu ${num(topMerchant.so)} giao dịch để tìm yếu tố liên quan.` : 'Chưa có dữ liệu merchant để xác định ưu tiên.'}</Priority>
          <Priority number="3" title={verified && e.favorable ? 'B3 cải thiện lợi ích trong backtest' : 'Mô phỏng phương án phân bổ vốn'} to="/toi-uu" action="Mô phỏng">{verified && e.profitDelta !== null && e.riskDelta !== null && e.selectionDelta !== null ? `So B2: lợi ích ${e.profitDelta >= 0 ? '+' : '−'}${num(Math.abs(e.profitDelta),2)} triệu; TARGET ${e.riskDelta >= 0 ? '+' : '−'}${num(Math.abs(e.riskDelta)*100,2)} đpt. Tỷ lệ chọn ${e.selectionDelta >= 0 ? 'tăng' : 'giảm'} ${num(Math.abs(e.selectionDelta)*100,2)} đpt.` : 'Thử quỹ vốn và trần rủi ro để so sánh lợi ích, rủi ro và tỷ lệ chọn.'}</Priority>
        </div>
        <div className="insight-scope">Tổng hợp theo quy tắc · B3 là thí nghiệm lịch sử</div>
      </ChartCard>
      <ChartCard title="Top merchant theo mức độ ưu tiên" icon="file" className="merchant-leaderboard" action={<select className="compact-select" aria-label="Sắp xếp merchant" value={sort} onChange={event=>setSort(event.target.value)}><option value="p_tb">Rủi ro TB ↓</option><option value="high">HIGH ↓</option><option value="gia_tri">Giá trị ↓</option><option value="so">Số GD ↓</option></select>}>
        <div className="merchant-table-wrap"><table className="merchant-table"><thead><tr><th>#</th><th>Merchant</th><th>Số GD</th><th>Tổng giá trị</th><th>Rủi ro TB</th><th>Tỷ trọng HIGH</th><th>Ưu tiên xem xét</th></tr></thead><tbody>{ranked.map((m,i)=>{
          const first=reviewFirst(m,k)
          return <tr key={m.merchant_id}><td>{i+1}</td><td><Link to={merchantUrl(m.merchant_id)}><MerchantMark id={m.merchant_id}/>{merchantName(m.merchant_id)}</Link></td><td>{num(m.so)}</td><td title={vndFull(m.gia_tri)}>{vnd(m.gia_tri)}</td><td><b className={first?'risk-emphasis':''}>{pct(m.p_tb,2)}</b></td><td><span className={`high-share ${first?'elevated':''}`} title={`Tỷ trọng HIGH: ${pct(m.high,1)}`}><i><span style={{width:`${isNumber(m.high)?Math.min(100,Math.max(0,Number(m.high)*100)):0}%`}}/></i><span>{pct(m.high,1)}</span></span></td><td><Link className={`review-pill ${first?'review-priority':''}`} to={merchantUrl(m.merchant_id)} title={first ? 'Rủi ro TB và tỷ trọng HIGH đều cao hơn toàn danh mục' : 'Mở giao dịch để phân tích thêm'}><Icon name={first?'target':'file'} size={11}/>{first?'Rà soát trước':'Phân tích'}</Link></td></tr>
        })}</tbody></table></div>
        {!ranked.length && <EmptyState title="Chưa có dữ liệu merchant"/>}
        <div className="leaderboard-footer"><span>Ưu tiên khi rủi ro TB & HIGH vượt mức chung</span><NextLink to="/danh-muc">Xem tất cả</NextLink></div>
      </ChartCard>
    </div>
    <details className="daily-details"><summary><span>Nguồn & đối chiếu số liệu</span><span>Phần được chọn: hậu kiểm − dự báo <b>{gap !== null ? `${gap>0?'+':''}${num(gap*100,2)} đpt` : '—'}</b></span></summary><div className="data-explanation"><p>Rủi ro dự báo và TARGET trên thẻ KPI được tính theo vốn được chọn. Biểu đồ merchant và phân tầng dùng trung bình theo giao dịch. TARGET là nhãn lịch sử Home Credit; DEMO dùng nhãn mô phỏng.</p><p>Bảng B0–B3 là lợi ích ròng hậu kiểm mô phỏng, độc lập với bộ lọc ngày. Các insight mô tả dữ liệu, chưa xác nhận nguyên nhân hoặc chất lượng hiệu chuẩn.</p></div><div className="merchant-table-wrap"><table className="merchant-table"><thead><tr><th>Ngày</th><th>Giao dịch</th><th>Giá trị (VNĐ)</th><th>Rủi ro TB</th><th>HIGH</th><th>Đề xuất chọn</th></tr></thead><tbody>{(resource.data.daily || []).map(d=><tr key={d.ngay}><td>{d.ngay}</td><td>{num(d.so_gd)}</td><td>{vndFull(d.gia_tri)}</td><td>{pct(d.p_tb,2)}</td><td>{pct(d.high,1)}</td><td>{pct(d.ty_le_duyet,1)}</td></tr>)}</tbody></table></div></details>
  </div>
}
