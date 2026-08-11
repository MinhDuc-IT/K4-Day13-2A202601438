# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`:
- Tổng số traces:
- Số PII leak còn lại:
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction:
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: HỢP LỆ: 6/6 panel có trong dashboard contract.
- Evidence dashboard: Dashboard dùng nguồn `data/logs.jsonl` và có 6 panel: Latency percentiles, Request traffic, Error rate and breakdown, Cost over time, Input and output tokens, Quality proxy. Cần lưu ảnh runtime (thấy rõ time range 60 phút, refresh 30 giây, đơn vị và threshold) vào `submission/evidence/` trước khi nộp.
- SLO đã chọn và lý do: P95 latency ≤ 3000 ms để bảo vệ trải nghiệm của đa số người dùng; error rate ≤ 2% để duy trì độ tin cậy API; daily cost ≤ USD 2.50 để kiểm soát ngân sách; quality score trung bình ≥ 0.75 để theo dõi chất lượng phản hồi.
- Alert rules và runbook: Gửi cảnh báo khi P95 latency > 3000 ms, error rate > 2%, daily cost > USD 2.50 hoặc quality trung bình < 0.75. Khi có alert: (1) kiểm tra panel và time range; (2) mở trace có latency/error bất thường; (3) đối chiếu log theo correlation ID; (4) xác định incident hoặc dependency gây lỗi; (5) tắt incident/rollback hoặc triển khai fix; (6) chạy lại load test và xác nhận chỉ số trở về ngưỡng.

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| | | | |
| Role 3 | Dashboard, SLO & Alert: kiểm tra dashboard contract 6/6 panel; cấu hình/đối chiếu các SLO và quy trình alert–runbook. | Chưa cập nhật | Dùng metrics từ log JSON để phát hiện bất thường, sau đó điều tra trace và log theo correlation ID. |
