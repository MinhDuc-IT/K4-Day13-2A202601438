# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: Tứ Khuyển
- Repository URL: [https://github.com/MinhDuc-IT/K4-Day13-2A202601438](https://github.com/MinhDuc-IT/K4-Day13-2A202601438)
- Commit SHA cuối: `06ebe359accbf3059cf2d0f53c569a2f1bdf7189`
- Thành viên và vai trò:
  - Phạm Văn Vinh (01988) — P1: Logging & PII
  - Ngô Huy Hoàn (01925) — P2: Tracing & Prompt Version
  - Ngô Văn Kiệt (01524) — P3: Dashboard, SLO & Alert
  - Nguyễn Minh Đức (01438) — P4: Incident, Report & Demo *(leader)*

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: **100/100** (40 bản ghi, 20 correlation ID, 0 PII leak — sau khi regenerate `data/logs.jsonl` với code P1)
- Tổng số traces: **≥ 10** trên Langfuse *(P2: prompt v1/v2 + load test; mỗi request `/chat` tạo một trace khi `tracing_enabled=true`)*
- Số PII leak còn lại: **0**
- Link/đường dẫn dashboard: [http://127.0.0.1:8092/dashboard](http://127.0.0.1:8092/dashboard) *(hoặc port 8000 nếu chạy theo SETUP.md — route `/dashboard`, nguồn `data/logs.jsonl`, time range 60 phút, refresh 30 giây)*

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/checkpoint1_correlation_id.png`
- Evidence PII redaction: `submission/evidence/checkpoint1_pii_redaction.png`
- Evidence trace waterfall: `submission/evidence/media__1786437533571.png` *(P2 — trace waterfall trên Langfuse)*
- Giải thích một span đáng chú ý: Span `LabAgent.run` bao trọn toàn bộ pipeline RAG → prompt resolve → LLM generate. Trong CP3, span này kéo dài ~2650–3593 ms khi incident `rag_slow` bật (RAG `retrieve()` sleep 2.5 s), trong khi baseline chỉ ~150 ms — giúp khoanh vùng bottleneck ở bước retrieval trước khi đọc log chi tiết.

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: **v1** — labels `baseline`, `production`
- Version/label candidate: **v2** — label `candidate`
- Trace ID của mỗi version:
  - Baseline (`LANGFUSE_PROMPT_LABEL=baseline`): xem evidence `submission/evidence/media__1786437281608.png`
  - Candidate (`LANGFUSE_PROMPT_LABEL=candidate`): xem evidence `submission/evidence/media__1786438229316.png`
- Bằng chứng đổi label hoặc rollback: `submission/evidence/media__1786438305655.png`, `submission/evidence/media__1786438644639.png` *(chuyển label `production` sang v2 rồi rollback về v1)*

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: **HỢP LỆ: 6/6 panel** có trong dashboard contract.
- Evidence dashboard: Route `/dashboard` đọc `data/logs.jsonl`, hiển thị 6 panel: Latency percentiles (P50/P95/P99), Request traffic, Error rate and breakdown, Cost over time, Input and output tokens, Quality proxy. Ảnh runtime: `submission/evidence/media__1786438644639.png` *(hoặc ảnh dashboard baseline do P3 chụp — thấy time range 60 phút, refresh 30 giây, đơn vị và threshold)*.
- SLO đã chọn và lý do:
  - P95 latency ≤ **3000 ms** — bảo vệ trải nghiệm đa số người dùng
  - Error rate ≤ **2%** — duy trì độ tin cậy API
  - Daily cost ≤ **USD 2.50** — kiểm soát ngân sách
  - Quality score trung bình ≥ **0.75** — theo dõi chất lượng phản hồi
- Alert rules và runbook: Cấu hình trong `config/alert_rules.yaml` — cảnh báo khi P95 > 3000 ms, error rate > 2%, quality < 0.75. Runbook: (1) kiểm tra panel và time range; (2) mở trace latency/error bất thường; (3) đối chiếu log theo correlation ID; (4) xác định incident hoặc dependency; (5) tắt incident / rollback / deploy fix; (6) chạy lại load test và xác nhận chỉ số về ngưỡng. Chi tiết: `docs/alerts.md`.

## 6. Điều tra challenge

- Challenge ID: `day13-k4-observability-v1` (cohort K4, incident `rag_slow`, `affected_feature=monitoring`, `latency_threshold_ms=2000`)
- Triệu chứng từ metrics: Sau khi bật incident, `/metrics` ghi `latency_p95=3593 ms` và `latency_p50=2651 ms` trên 5 request challenge (vượt ngưỡng challenge 2000 ms và SLO P95 3000 ms). Error rate = 0%, `quality_avg=0.84` — sự cố tail latency, không phải lỗi HTTP.
- Trace ID liên quan: Tìm trên Langfuse theo `session_id=k4-challenge-s03` hoặc metadata `feature=monitoring` — span `LabAgent.run` ~3593 ms. *(P2 bổ sung trace ID cụ thể từ Langfuse UI nếu cần)*
- Log line/correlation ID liên quan:
  - `incident_enabled` → `correlation_id=req-22af4a4d`, `payload.name=rag_slow`
  - Request chậm nhất → `correlation_id=req-339eacae`, `session_id=k4-challenge-s03`, `feature=monitoring`, `latency_ms=3593` (`response_sent`)
  - Các request còn lại: `req-e3de9439`, `req-5b432677`, `req-1a6a738a`, `req-91031db3` — đều `feature=monitoring`, `latency_ms` 2650–3593 ms
- Root cause: Incident `rag_slow` inject qua `POST /incidents/rag_slow/enable` (theo `config/challenge.json`). Trong `app/mock_rag.py`, khi `STATE["rag_slow"]=True`, hàm `retrieve()` gọi `time.sleep(2.5)` trước khi trả document. Toàn bộ 5 query challenge dùng `feature=monitoring` và message chứa từ khóa `monitoring` → mọi request đi qua RAG chậm → latency agent tăng ~2500 ms so với baseline ~150 ms.
- Fix action: `python scripts/inject_incident.py --disable` (hoặc `POST /incidents/rag_slow/disable`). Xác nhận: load test challenge sau fix trả latency HTTP ~157–174 ms/request. Evidence: `submission/evidence/cp3_challenge_metrics.txt`
- Preventive measure:
  1. Alert `api_tail_latency_slo_breach` (P95 > 3000 ms) — runbook: kiểm tra `/health` → `incidents.rag_slow` → tắt incident nếu là drill.
  2. Thêm timeout/circuit breaker cho RAG retrieve; tách span `retrieve` để localize nhanh hơn trace tổng.
  3. Dashboard panel Latency: so sánh P95 theo `feature` để thấy chỉ `monitoring` bị ảnh hưởng.

## 7. Đóng góp cá nhân


| Thành viên                   | Phần việc                                                                                                                                  | Commit/PR                                                                                            | Điều đã học                                                                                                                                 |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Phạm Văn Vinh (01988) — P1   | Correlation ID middleware, log enrichment (`user_id_hash`, `session_id`, `feature`, `model`, `env`), PII scrubbing processor, evidence CP1 | `eec29ec`, `d8a99b2`, `3647678` — [PR #1](https://github.com/MinhDuc-IT/K4-Day13-2A202601438/pull/1) | Correlation ID phải propagate xuyên suốt request và xuất hiện trong log JSON; PII phải redact trước khi ghi file, không chỉ che ở response. |
| Ngô Huy Hoàn (01925) — P2    | Langfuse tracing, prompt `day13-chat` v1/v2, label baseline/candidate/production, rollback, ≥10 traces                                     | `ae2d15b`, `d787877` — [PR #2](https://github.com/MinhDuc-IT/K4-Day13-2A202601438/pull/2)            | Prompt versioning giúp truy xuất version đã dùng trong trace; đổi label/rollback an toàn mà không cần deploy lại code.                      |
| Ngô Văn Kiệt (01524) — P3    | Dashboard 6 panel từ `data/logs.jsonl`, SLO, alert rules, validator 6/6                                                                    | `c250939`, `4dade61` — [PR #3](https://github.com/MinhDuc-IT/K4-Day13-2A202601438/pull/3)            | Metrics từ log JSON là nguồn chuẩn cho dashboard contract; SLO và alert nối symptom → điều tra trace → log.                                 |
| Nguyễn Minh Đức (01438) — P4 | Điều tra challenge CP3 (inject incident, metrics → log → root cause), fix/verify, hoàn thiện REPORT và evidence                            | `06ebe359accbf3059cf2d0f53c569a2f1bdf7189` — [commit](https://github.com/MinhDuc-IT/K4-Day13-2A202601438/commit/06ebe359accbf3059cf2d0f53c569a2f1bdf7189) | Luồng observability thực tế: phát hiện triệu chứng từ metrics, khoanh vùng bằng trace, chứng minh root cause bằng log có correlation ID.    |


## 8. Demo cuối (Metrics → Traces → Logs → Root cause)

1. **Metrics:** `/metrics` hoặc dashboard panel Latency — P95 tăng lên 3593 ms sau inject `rag_slow`.
2. **Traces:** Mở Langfuse, trace request `session_id=k4-challenge-s03` — span `LabAgent.run` kéo dài bất thường.
3. **Logs:** `data/logs.jsonl` — `incident_enabled` (`req-22af4a4d`) rồi `response_sent` (`req-339eacae`, 3593 ms).
4. **Root cause:** `mock_rag.retrieve()` sleep 2.5 s khi `rag_slow=true`.
5. **Fix:** `python scripts/inject_incident.py --disable` → latency về ~150 ms.

## Checklist nộp bài

- `python -m pytest -q` — 22 passed
- `python scripts/validate_logs.py` — 100/100
- `python scripts/validate_dashboard.py` — 6/6 panel
- `submission/REPORT.md` đầy đủ
- Evidence trong `submission/evidence/`
- Push commit cuối và cập nhật Commit SHA mục 1 — `06ebe359accbf3059cf2d0f53c569a2f1bdf7189`
- Không commit `.env`, secret, PII nguyên văn

