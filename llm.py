"""
llm.py – Tầng LLM có degradation: Gemini (chuỗi model, retry, timeout) -> None (dùng mẫu dự phòng).
Quyết định tín dụng KHÔNG BAO GIỜ phụ thuộc vào LLM; LLM chỉ diễn giải.

    from llm import LLM, PrivacyGuard, kiem_tra_so
    llm = LLM(api_key=os.environ["GEMINI_API_KEY"])
    text, source = llm.ask(system_prompt, user_content)   # text=None nếu mọi model lỗi
"""
import os, re, time
from datetime import datetime

MODEL_CHAIN = ["gemini-3.5-flash", "gemini-3-flash-preview", "gemini-3.5-flash-lite", "gemini-flash-lite-latest"]
# Ghi chú 07/10/2026: gemini-2.5-flash/-lite đã bị gỡ (404); 3.6/3.7/3.8-flash quá tải (503/504). Dò lại bằng probe_models().


class LLM:
    def __init__(self, api_key=None, model_chain=None, timeout_ms=30_000):
        self.key = api_key or os.environ.get("GEMINI_API_KEY")
        self.chain = model_chain or MODEL_CHAIN
        self.client = None
        if self.key:
            from google import genai
            from google.genai import types
            self.types = types
            self.client = genai.Client(api_key=self.key, http_options=types.HttpOptions(timeout=timeout_ms))

    def probe_models(self):
        """Trả về danh sách model thật sự gọi được (dùng khi chuỗi mặc định hỏng)."""
        if not self.client: return []
        ok = []
        for m in self.client.models.list():
            name = m.name.replace("models/", "")
            if "gemini" not in name or any(k in name for k in ["tts", "image", "embedding", "audio", "live", "transcribe", "robotics"]):
                continue
            try:
                self.client.models.generate_content(model=name, contents="OK"); ok.append(name)
            except Exception:
                pass
        return ok

    def ask(self, system_prompt, user_content, retries=2, temperature=0.4):
        if not self.client:
            return None, "Mẫu dự phòng (chưa cấu hình GEMINI_API_KEY)"
        for mdl in self.chain:
            for lan in range(retries):
                try:
                    r = self.client.models.generate_content(
                        model=mdl, contents=user_content,
                        config=self.types.GenerateContentConfig(system_instruction=system_prompt, temperature=temperature))
                    if r.text:
                        return r.text, f"Gemini ({mdl})"
                    break
                except Exception as e:
                    s = str(e)
                    if any(k in s for k in ["503", "429", "504", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "DEADLINE", "imeout"]):
                        time.sleep(3)
                    else:
                        break
        return None, "Mẫu dự phòng (tất cả model đều lỗi)"


class PrivacyGuard:
    """Che PII trước khi dữ liệu rời hệ thống (Nghị định 13/2023/NĐ-CP) + audit log."""
    def __init__(self): self.audit_log = []
    def mask_phone(self, v):
        s = str(v or "").strip(); return f"{s[:3]}****{s[-3:]}" if len(s) >= 10 else "[MASKED_PHONE]"
    def mask_device_id(self, v):
        s = str(v or "").strip(); return f"{s[:3]}-***-MASKED" if s else "[NO_DEVICE]"
    def mask_gps(self, v):
        try:
            lat, lon = (float(p) for p in str(v).split(",")); return f"{round(lat,1)}xx, {round(lon,1)}xx (Geo-blurred)"
        except Exception:
            return "[MASKED_COORDINATES]"
    def mask_name(self, v):
        p = str(v or "").split(); return (p[0] + " " + " ".join(x[0] + "***" for x in p[1:])) if p else "[NO_NAME]"
    def sanitize(self, r: dict) -> dict:
        m = dict(r)
        for f, fn in [("full_name", self.mask_name), ("phone_number", self.mask_phone),
                      ("device_id", self.mask_device_id), ("last_gps_location", self.mask_gps)]:
            if f in m: m[f] = fn(r.get(f))
        self.audit_log.append({"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "customer_id": r.get("customer_id"),
                               "standard": "Nghị định 13/2023/NĐ-CP", "masked": [f for f in ["full_name", "phone_number", "device_id", "last_gps_location"] if f in m]})
        return m


def kiem_tra_so(text: str, facts: str):
    """Guardrail: liệt kê các số trong câu trả lời LLM không xuất hiện trong facts (cần người rà soát)."""
    so_facts = {round(float(x.replace(",", "")), 1) for x in re.findall(r"\d[\d,]*\.?\d*", facts)}
    la = set()
    for x in re.findall(r"\d[\d,]*\.?\d*", text or ""):
        v = round(float(x.replace(",", "")), 1)
        if v > 10 and v not in so_facts and not any(abs(v - a) < 0.15 or abs(v - (100 - a)) < 0.15 for a in so_facts):
            la.add(x)
    return sorted(la)


# ---------------------------------------------------------------- Prompt chuẩn (dùng lại trong chatbot)
COACH_SYSTEM = """Bạn là AURA Financial Coach – trợ lý tài chính cá nhân trên ứng dụng Ví Trả Sau.
Nhiệm vụ: giải thích minh bạch, lịch sự, mang tính xây dựng lý do một giao dịch tạm thời chưa được cấp vốn và gợi ý lộ trình cải thiện.
Quy tắc: đồng cảm, không phán xét; CHỈ dùng yếu tố và mô tả được cung cấp, không bịa; không nhắc tuổi, học vấn, nghề nghiệp, nơi làm việc;
không nêu xác suất hay giá trị số của mô hình; đưa 2–3 hành động cụ thể trong 30–90 ngày; dưới 200 từ; không dùng markdown;
xưng 'AURA', gọi khách là 'bạn'."""

ADVISOR_SYSTEM = """Bạn là Portfolio Strategy Advisor của AURA-DSS, tư vấn cho Giám đốc Nguồn vốn.
Phân tích kết quả tối ưu hóa MILP và đưa khuyến nghị điều hành. Quy tắc: CHỈ dùng số liệu được cung cấp, không bịa thêm con số;
nếu một con số cần thiết không có trong dữ liệu, ghi "(không có số liệu)" thay vì ước lượng; chỉ rõ ràng buộc nào đang quyết định
quy mô giải ngân; so sánh với phương án duyệt tất cả; ngắn gọn, có cấu trúc, dưới 250 từ; không dùng markdown."""

ANALYST_SYSTEM = """Bạn là trợ lý phân tích rủi ro tín dụng nội bộ của AURA-DSS, trả lời câu hỏi của cán bộ tín dụng.
Bạn được cung cấp: số liệu danh mục, kết quả chấm điểm và giải thích SHAP của khách hàng (nếu có), và kết quả truy vấn CSDL (nếu có).
Quy tắc: CHỈ dùng số liệu được cung cấp; không bịa; nếu không đủ dữ liệu hãy nói rõ và gợi ý truy vấn cần chạy; trả lời tiếng Việt, ngắn gọn."""
