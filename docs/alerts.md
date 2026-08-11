# Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: `api_tail_latency_slo_breach`
- Severity: Critical.
- SLI/SLO liên quan: Latency P95 <= 3000 ms.
- Điều kiện và thời gian duy trì: P95 `response_sent.latency_ms` > 3000 ms trong 5 phút liên tiếp.
- Ảnh hưởng tới người dùng: Câu trả lời chậm rõ rệt; request có thể hết timeout ở client.
- Ba bước kiểm tra đầu tiên:
  1. Xác nhận panel Latency và Traffic trong cùng time range để loại trừ thay đổi tải bình thường.
  2. Mở một trace có latency cao trong Langfuse và so sánh thời gian retrieval/generation.
  3. Tìm `correlation_id` của trace trong `data/logs.jsonl` để xác nhận event và feature bị ảnh hưởng.
- Mitigation tạm thời: Tắt incident nếu đang practice; giảm concurrency hoặc tạm bypass retrieval sau khi được owner ứng dụng chấp thuận.
- Owner: Dashboard, SLO & Alert owner.

## Alert 2

- Tên: `api_error_rate_slo_breach`
- Severity: Critical.
- SLI/SLO liên quan: Error rate <= 2%.
- Điều kiện và thời gian duy trì: `request_failed / request_received * 100` > 2% trong 5 phút liên tiếp.
- Ảnh hưởng tới người dùng: Người dùng nhận HTTP 500 hoặc không có câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel Errors để xem `error_type` nào tăng.
  2. Mở trace gần thời điểm bắt đầu lỗi và xác định span cuối cùng thành công.
  3. Tra log cùng `correlation_id`, đọc `request_failed.error_type` và payload đã redact.
- Mitigation tạm thời: Tắt incident hoặc dependency lỗi nếu có thể; trả lời fallback an toàn cho feature bị ảnh hưởng.
- Owner: Dashboard, SLO & Alert owner.

## Alert 3

- Tên: `answer_quality_degradation`
- Severity: Warning.
- SLI/SLO liên quan: Mean quality proxy >= 0.75.
- Điều kiện và thời gian duy trì: Mean `response_sent.quality_score` < 0.75 trong 15 phút, với ít nhất 10 request.
- Ảnh hưởng tới người dùng: Câu trả lời có thể ngắn, không dùng context hoặc ít liên quan đến câu hỏi.
- Ba bước kiểm tra đầu tiên:
  1. Xác nhận panel Quality giảm trong khi Traffic không thay đổi bất thường.
  2. So sánh trace/prompt version trước và sau thời điểm giảm.
  3. Đối chiếu answer preview đã redact và metadata retrieval trong trace của cùng request.
- Mitigation tạm thời: Rollback label `production` về prompt version ổn định và chạy lại input kiểm chứng.
- Owner: Dashboard, SLO & Alert owner.
