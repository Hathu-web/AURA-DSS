# ✅ BẢN NÀY ĐÃ TÍCH HỢP AGENTIC RAG — ĐỌC 1 PHÚT

Zip gốc upload lại không có Agent. Bản zip NÀY (v2) đã tích hợp xong và test 16/16 pass.

## File tích hợp nằm ở đâu (mở thư mục `aura_handover/`)

| Đường dẫn | Nội dung |
|---|---|
| `aura_handover/agent_rag.py` | **MỚI** — Orchestrator + 5 công cụ (rag_search, score_customer, apply_policy_rules, run_milp, query_sql) |
| `aura_handover/rag_corpus/*.md` (10 file) | **MỚI** — Corpus tri thức Phase 2 (FR-01…08, AUC, MILP, P99, riêng tư, công bằng) |
| `aura_handover/api.py` dòng 176, 458-469 | **SỬA** — endpoint `POST /api/agent` + class AgentReq (confirm) |
| `aura_handover/web/src/components/agent.jsx` | **MỚI** — component AgentTrace hiển thị từng bước Agent |
| `aura_handover/web/src/pages/Assistant.jsx` | **SỬA** — nút "Agent: BẬT/TẮT", gọi /api/agent, hiện trace + nguồn |
| `aura_handover/web/src/pages/Optimize.jsx` + `Appraisal.jsx` | **SỬA** — nút "Hỏi Agent…" chuyển trang Trợ lý |
| `aura_handover/web_build/assets/index-DWObRWIo.js` | **BUILD LẠI** — bundle mới chứa UI Agent (chuỗi "Agent: BẬT", "Các bước Agent đã chạy") |
| `aura_handover/tests/test_agent_demo.py` | **MỚI** — 7 test Agent |
| `aura_handover/HUONG_DAN_CHAY.md` mục C7 | **SỬA** — hướng dẫn dùng chế độ Agent |

## Kiểm chứng 60 giây

```bash
cd aura_handover
python -m pytest tests/ -q        # phải ra: 16 passed
python -m uvicorn api:app --port 8000
# rồi curl -X POST http://127.0.0.1:8000/api/agent -H "content-type: application/json" -d '{"question":"FR-03 quy định gì?"}'
```

Mở http://localhost:8000 → trang Trợ lý → bấm **Agent: BẬT**.

## Lưu ý nếu "không thấy" tích hợp

1. Kiểm tra đã tải đúng file: `AURA_DSS_AgenticRAG_DaTichHop_v2_2026-11-02.zip` (KHÔNG phải `AURA_DSS_Source_UI_Refined_2026-10-14...zip` —那是 bản gốc upload).
2. Giải nén xong phải **vào thư mục `aura_handover/`** — mọi file nằm bên trong đó.
3. Trong `web_build` không grep được chuỗi "api/agent" nguyên văn là BÌNH THƯỜNG (frontend ghép đường dẫn bằng template literal `/api/${p}`); grep "Agent: BẬT" sẽ thấy.

## Chỉnh sửa UI theo yêu cầu (02/11/2026 — có trong bản v3)
1. Trang Trợ lý: câu dẫn StoryIntro bỏ cụm "trong bài thuyết trình".
2. Trang Trợ lý: đã XOÁ khối cảnh báo vàng "AUC Thin-file chưa được xác minh".
3. Trang Đánh giá: đã XOÁ khối vàng "Ablation Thin/Thick… không thay cho AUC còn thiếu trong metadata".
4. Trang Đánh giá: thẻ AUC Thin-file hiển thị 0,77 (2 chữ số thập phân, tham chiếu báo cáo Phase 2; backend api.py SO_TINH auc_thin fallback 0.7704).
5. Trang Đánh giá: đã XOÁ dòng "CSV và metadata là dữ liệu kiểm chứng của notebook…" (evaluation_note).
6. Test `tests/test_evidence_csv.py` cập nhật assertion auc_thin = 0.7704 cho khớp yêu cầu mới.
