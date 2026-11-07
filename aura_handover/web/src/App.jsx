import { useState } from 'react'
import { NavLink, Routes, Route, Navigate, useLocation, Link } from 'react-router-dom'
import { setApiToken } from './lib/api'
import { StoreProvider, useStore, PRESETS } from './lib/store'
import { displayDate } from './lib/fmt'
import Icon from './components/Icon'
import Overview from './pages/Overview'
import Portfolio from './pages/Portfolio'
import Appraisal from './pages/Appraisal'
import Optimize from './pages/Optimize'
import Evaluation from './pages/Evaluation'
import Logs from './pages/Logs'
import Assistant from './pages/Assistant'
import Ingest from './pages/Ingest'

const NAV = [
  { to: '/tong-quan', label: 'Tổng quan', icon: 'home' },
  { to: '/danh-muc', label: 'Danh mục rủi ro', icon: 'chart' },
  { to: '/tham-dinh', label: 'Thẩm định hồ sơ', icon: 'user' },
  { to: '/toi-uu', label: 'Tối ưu vốn', icon: 'wallet' },
  { to: '/tro-ly', label: 'Trợ lý AI', icon: 'spark' },
  { sec: 'Vận hành' },
  { to: '/danh-gia', label: 'Đánh giá mô hình', icon: 'shield' },
  { to: '/nhap-du-lieu', label: 'Nhập dữ liệu', icon: 'upload' },
  { to: '/nhat-ky', label: 'Nhật ký quyết định', icon: 'file' },
]
const PAGES = {
  '/tong-quan': ['Executive Risk Cockpit', 'Giám sát rủi ro tín dụng và hỗ trợ điều phối thanh khoản BNPL.'],
  '/danh-muc': ['Danh mục rủi ro', 'Rủi ro tập trung ở đâu, và phân khúc nào cần kiểm tra thêm?'],
  '/tham-dinh': ['Thẩm định hồ sơ', 'Hồ sơ này có mức rủi ro nào và những đặc trưng nào ảnh hưởng đến dự báo?'],
  '/toi-uu': ['Tối ưu vốn', 'Với nguồn vốn hữu hạn, phương án nào cân bằng lợi ích kỳ vọng và rủi ro?'],
  '/danh-gia': ['Đánh giá mô hình', 'Bằng chứng nào hỗ trợ quyết định, và mô hình có giới hạn gì?'],
  '/tro-ly': ['Trợ lý AI', 'Hỏi dữ liệu, kiểm tra bằng chứng và làm rõ cơ sở của đề xuất.'],
  '/nhap-du-lieu': ['Nhập dữ liệu', 'Đưa hồ sơ hoặc giao dịch vào quy trình phân tích hiện tại.'],
  '/nhat-ky': ['Nhật ký quyết định', 'Truy xuất các đề xuất đã ghi nhận và theo dõi kiểm soát dữ liệu.'],
}
const JOURNEY = [
  { to: '/tong-quan', title: 'Phát hiện vấn đề', page: 'Tổng quan' },
  { to: '/danh-muc', title: 'Phân tích rủi ro', page: 'Danh mục' },
  { to: '/toi-uu', title: 'Đề xuất phương án', page: 'Tối ưu vốn' },
  { to: '/danh-gia', title: 'Kiểm tra cơ sở', page: 'Đánh giá mô hình' },
  { to: '/tro-ly', title: 'Giải thích quyết định', page: 'Trợ lý AI' },
]
function DateRangeFilter() {
  const { preset, setPreset, custom, setCustom, range } = useStore()
  return <div className="date-control">
    <div className="date-control-top"><Icon name="calendar" size={16}/>
      <span>{range.d_from || range.d_to ? `${displayDate(range.d_from)} – ${displayDate(range.d_to)}` : 'Toàn bộ thời gian có dữ liệu'}</span>
      <select aria-label="Khoảng thời gian" value={preset} onChange={e => setPreset(e.target.value)}>
        {PRESETS.map(p => <option key={p.k} value={p.k}>{p.l}</option>)}<option value="custom">Tùy chọn</option>
      </select>
    </div>
    {preset === 'custom' && <div className="custom-dates">
      <label>Từ ngày<input type="date" value={custom.d_from} max={custom.d_to || undefined} onChange={e => setCustom({ ...custom, d_from: e.target.value })}/></label>
      <label>Đến ngày<input type="date" value={custom.d_to} min={custom.d_from || undefined} onChange={e => setCustom({ ...custom, d_to: e.target.value })}/></label>
    </div>}
  </div>
}
function Ribbon({ sidebar=false }) {
  return <svg className={sidebar ? 'sidebar-ribbon' : 'header-ribbon'} viewBox={sidebar ? '0 0 200 300' : '0 0 620 130'} preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id={sidebar ? 'side-ribbon' : 'top-ribbon'} x1="0" y1="0" x2="1" y2="1"><stop stopColor="#B48CFF" stopOpacity=".65"/><stop offset=".55" stopColor="#8679FA" stopOpacity=".17"/><stop offset="1" stopColor="#C9C7FF" stopOpacity=".04"/></linearGradient></defs>{sidebar ? <><path d="M-30 178 179 14Q218-10 225 25L242 290H-30Z" fill="#F0EDFF"/><path d="M-5 248Q26 91 90 145T214 173L220 300H0Z" fill="url(#side-ribbon)"/><path d="M-35 238 62 165 98 178 157 111 191 119 221 89" stroke="#C8B9FF" fill="none"/><circle cx="157" cy="111" r="3" fill="#B6A4FC"/><path d="M84 220Q52 89 114 144T198 189L202 290Z" fill="url(#side-ribbon)"/></> : <><path d="M0 130 99 47Q129 20 165 42L305 118 403 50Q433 31 462 51L620 130Z" fill="url(#top-ribbon)"/><path d="M123 130 269 45Q302 26 336 46L491 130Z" fill="#D5D8FF" opacity=".35"/><path d="M311 130 431 74Q455 61 481 78L578 130Z" fill="#BEB5FC" opacity=".26"/></>}</svg>
}
function Shell() {
  const { health } = useStore()
  const { pathname } = useLocation()
  const [title, subtitle] = PAGES[pathname] || PAGES['/tong-quan']
  const [presenting, setPresenting] = useState(false)
  const [accessToken, setAccessToken] = useState('')
  const step = JOURNEY.findIndex(s => s.to === pathname)
  const showRange = ['/tong-quan', '/danh-muc', '/toi-uu', '/tro-ly'].includes(pathname)
  return <div className={`app ${presenting ? 'presenting' : ''}`}>
    <a className="skip-link" href="#main-content">Đến nội dung chính</a>
    <aside className="sidebar">
      <Link to="/tong-quan" className="brand" aria-label="AURA DSS — Tổng quan">
        <svg className="brand-symbol" viewBox="0 0 38 42" aria-hidden="true"><path d="M4 35 18 7a3 3 0 0 1 5 0l13 28" fill="none" stroke="#5418E5" strokeWidth="7" strokeLinecap="round"/><path d="m13 24 9-17" stroke="#1814B4" strokeWidth="7" strokeLinecap="round"/><path d="m21 24 5 11" stroke="#B9A7F8" strokeWidth="7" strokeLinecap="round"/></svg>
        <div><b>Aura<span> DSS</span></b></div>
      </Link>
      <nav className="nav" aria-label="Điều hướng chính">{NAV.map((n, i) => n.sec ? <div className="nav-divider" key={i}/> : <NavLink key={n.to} to={n.to}><Icon name={n.icon} size={18}/>{n.label}</NavLink>)}</nav>
      <div className="sidebar-art"><Ribbon sidebar/><div className="sidebar-story"><p>Dữ liệu<br/>thông minh<br/><b>Quyết định<br/>vững vàng</b></p><Link to="/tro-ly" aria-label="Mở Trợ lý AI"><Icon name="arrow" size={16}/></Link></div></div>
      <div className="token-access"><details><summary>Mã truy cập</summary><div className="stack" style={{ marginTop: 8 }}><input aria-label="Mã truy cập API" type="password" autoComplete="off" placeholder="Nhập mã truy cập" value={accessToken} onChange={e => setAccessToken(e.target.value)}/><button className="btn" type="button" onClick={() => { setApiToken(accessToken); setAccessToken(''); window.location.reload() }}>Kết nối lại</button></div></details></div>
    </aside>
    <main className="main" id="main-content">
      <header className="topbar">
        <Ribbon/>
        <div className="page-heading"><span className="eyebrow">AURA-DSS</span><h1>{title}</h1><p>{subtitle}</p></div>
        <div className="header-tools"><div className="header-controls">{showRange && <DateRangeFilter/>}<details className="data-context"><summary className={`mode-badge ${health?.error ? 'offline' : health?.demo ? 'demo' : health ? 'live' : ''}`}>{health?.error ? 'MẤT KẾT NỐI' : health?.demo ? 'DEMO' : health ? 'LIVE' : 'KẾT NỐI…'}</summary><div role="status"><b>Nguồn dữ liệu</b><p>{health?.error ? 'Không lấy được trạng thái dữ liệu.' : health?.demo ? 'Dữ liệu minh họa từ backend.' : health ? 'Home Credit holdout + giao dịch BNPL mô phỏng.' : 'Đang kiểm tra nguồn dữ liệu…'}</p>{health?.data_to && <small>Giao dịch mới nhất: {displayDate(health.data_to)}</small>}</div></details><button className={`btn presentation-button ${presenting ? 'primary' : ''}`} onClick={() => setPresenting(v => !v)} aria-pressed={presenting} title={presenting ? 'Thoát trình chiếu' : 'Thuyết trình'} aria-label={presenting ? 'Thoát trình chiếu' : 'Thuyết trình'}><Icon name="presentation" size={17}/></button></div><span className="brand-signature">Smarter Credit<br/>Brighter Commerce</span></div>
      </header>
      {presenting && <nav className="decision-journey" aria-label="Mạch trình bày quyết định">{JOURNEY.map((item, i) => <NavLink to={item.to} key={item.to} className={`journey-step ${i === step ? 'active' : ''}`}><span className="journey-number">{i+1}</span><span>{item.page}</span></NavLink>)}</nav>}
      {presenting && <div className="presenter-guide"><span><Icon name="presentation" size={18}/><b>Câu hỏi dẫn dắt</b> {pathname === '/tong-quan' ? 'Danh mục đang có vấn đề gì và nên kiểm tra điều gì trước?' : subtitle}</span><div>{step > 0 && <Link className="btn" to={JOURNEY[step - 1].to}>← Trước</Link>}{step >= 0 && step < JOURNEY.length - 1 && <Link className="btn primary" to={JOURNEY[step + 1].to}>Tiếp theo <Icon name="arrow" size={15}/></Link>}</div></div>}
      <Routes>
        <Route path="/" element={<Navigate to="/tong-quan" replace/>}/>
        <Route path="/tong-quan" element={<Overview/>}/><Route path="/danh-muc" element={<Portfolio/>}/>
        <Route path="/tham-dinh" element={<Appraisal/>}/><Route path="/toi-uu" element={<Optimize/>}/>
        <Route path="/danh-gia" element={<Evaluation/>}/><Route path="/tro-ly" element={<Assistant/>}/>
        <Route path="/nhap-du-lieu" element={<Ingest/>}/><Route path="/nhat-ky" element={<Logs/>}/>
        <Route path="*" element={<Navigate to="/tong-quan" replace/>}/>
      </Routes>
      <footer className="app-disclaimer"><Icon name="info" size={14}/><span>AURA-DSS hỗ trợ đề xuất. Người có thẩm quyền xem xét và quyết định cuối cùng. TARGET lịch sử không phải nợ xấu BNPL thực tế.</span></footer>
    </main>
  </div>
}
export default function App() { return <StoreProvider><Shell/></StoreProvider> }
