import Icon from './Icon'
import { DetailPanel } from './workflow'

// Nhãn & màu công cụ trong trace của Agentic RAG (khớp agent_rag.py)
const TOOL_META = {
  phan_loi: { icon: 'spark', label: 'Phân loại' },
  bao_ve: { icon: 'shield', label: 'Rào chắn' },
  kpi_danh_muc: { icon: 'chart', label: 'KPI danh mục' },
  rag_search: { icon: 'file', label: 'Tra cứu tài liệu' },
  score_customer: { icon: 'user', label: 'Chấm điểm' },
  policy_rules: { icon: 'shield', label: 'Bộ quy tắc' },
  run_milp: { icon: 'chart', label: 'MILP tối ưu' },
  query_sql: { icon: 'file', label: 'Truy vấn SQL' },
  cong_cu: { icon: 'spark', label: 'Công cụ' },
}
const INTENT_LABEL = {
  ho_so: 'Hồ sơ khách hàng', toi_uu: 'Tối ưu vốn (MILP)', tai_lieu: 'Tài liệu Phase 2',
  truy_van: 'Truy vấn dữ liệu', danh_muc: 'Danh mục', tong_hop: 'Tổng hợp', ngoai_pham_vi: 'Ngoài phạm vi',
}
const STATUS_LABEL = { ok: '', loi: 'Lỗi', tu_choi: 'Từ chối', bo_qua: 'Bỏ qua', rong: 'Không khớp' }

export const AGENT_INTRO = { role: 'bot', text: 'Chế độ Agent đang bật: mình sẽ phân loại câu hỏi, gọi công cụ (chấm điểm, quy tắc, MILP, truy vấn, tra cứu tài liệu Phase 2) rồi mới trả lời từ số liệu thu về. Các bước hiện trong "Các bước Agent đã chạy".' }

export function AgentTrace({ trace = [], tongMs }) {
  if (!trace?.length) return null
  return <DetailPanel title={`Các bước Agent đã chạy (${trace.length}${tongMs ? ` · ${tongMs} ms` : ''})`} open>
    <ol className="agent-trace" aria-label="Trace các bước công cụ của Agent">
      {trace.map((s, i) => {
        const meta = TOOL_META[s.tool] || { icon: 'spark', label: s.tool }
        const st = STATUS_LABEL[s.trang_thai]
        return <li key={i} className={`agent-step ${s.trang_thai !== 'ok' ? 'warn' : ''}`}>
          <span className="agent-step-icon"><Icon name={meta.icon} size={14}/></span>
          <div className="agent-step-body">
            <b>{i + 1}. {meta.label}</b>
            <span className="agent-step-detail">{s.chi_tiet}</span>
          </div>
          <span className="agent-step-meta">{st && <em>{st}</em>}{s.ms} ms</span>
        </li>
      })}
    </ol>
  </DetailPanel>
}

export function AgentSources({ sources = [] }) {
  if (!sources?.length) return null
  return <div className="agent-sources">
    <span className="small muted">Nguồn tài liệu Phase 2:</span>
    <div className="facts-list">{sources.map(s => <span key={s.id} title={s.title}>{s.title}</span>)}</div>
  </div>
}

export function AgentIntentChip({ intent, offline }) {
  if (!intent) return null
  return <span className={`source-chip ${intent === 'ngoai_pham_vi' || offline ? 'warm' : ''}`}>{INTENT_LABEL[intent] || intent}</span>
}
