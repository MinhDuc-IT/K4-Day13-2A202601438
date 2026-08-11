# Chạy dashboard local

Dashboard của nhóm nằm tại route `/dashboard` trong chính FastAPI app. Nó đọc trực tiếp `data/logs.jsonl`, dùng cửa sổ 60 phút và tự refresh mỗi 30 giây; không cần thêm package ngoài `requirements.txt`.

## Chạy và kiểm tra

1. Khởi động API: `uvicorn app.main:app --reload --env-file .env`.
2. Tạo dữ liệu baseline: `python scripts/load_test.py --concurrency 5`.
3. Mở `http://127.0.0.1:8000/dashboard` và chụp ảnh thấy đủ sáu panel, time range, đơn vị và threshold.
4. Kiểm tra contract: `python scripts/validate_dashboard.py`.

## Evidence incident practice

1. Lưu ảnh baseline.
2. Chạy `python scripts/inject_incident.py --scenario rag_slow`.
3. Chạy lại `python scripts/load_test.py --concurrency 5`.
4. Refresh dashboard; panel Latency phải cho thấy P95 tăng rõ ràng.
5. Dùng correlation ID từ log để phối hợp với người phụ trách trace, sau đó tắt incident bằng `python scripts/inject_incident.py --scenario rag_slow --disable`.

Không sửa `config/dashboard.yaml`: đây là contract chấm điểm chung.
