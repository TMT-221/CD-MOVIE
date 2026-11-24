# Movie CD Store Management System

Hệ thống quản lý cửa hàng bán đĩa CD phim, được xây dựng trong môn **INT1313 – Hệ cơ sở dữ liệu**, phục vụ bài thực hành Lab 01 và Lab 02.

[![Kiểm thử MySQL](https://github.com/TMT-221/CD-MOVIE/actions/workflows/mysql-lab.yml/badge.svg)](https://github.com/TMT-221/CD-MOVIE/actions/workflows/mysql-lab.yml)
[![Kiểm thử Python](https://github.com/TMT-221/CD-MOVIE/actions/workflows/python-lab.yml/badge.svg)](https://github.com/TMT-221/CD-MOVIE/actions/workflows/python-lab.yml)
[![Kiểm thử API](https://github.com/TMT-221/CD-MOVIE/actions/workflows/api-lab.yml/badge.svg)](https://github.com/TMT-221/CD-MOVIE/actions/workflows/api-lab.yml)

## 1. Giới thiệu dự án

Hệ thống hỗ trợ quản lý danh mục phim, thể loại, phiên bản đĩa CD, giá bán, tồn kho, khách hàng, nhân viên, quản lý và hóa đơn. Dữ liệu được lưu trữ trong MySQL, xử lý thông qua Python và cung cấp cho giao diện web bằng REST API.

| Thành phần | Công nghệ |
|---|---|
| Cơ sở dữ liệu | MySQL 8.4 – `MovieCDStore` |
| Ngôn ngữ lập trình | Python 3.12 (môi trường kiểm thử CI) |
| Kết nối CSDL | MySQL Connector/Python |
| Backend | FastAPI, Uvicorn |
| Frontend | HTML, CSS, JavaScript thuần |
| Tài liệu API | Swagger UI, OpenAPI |
| Kiểm thử và triển khai demo | GitHub Actions, Docker, GitHub Codespaces |

## 2. Thiết kế cơ sở dữ liệu – Lab 01

- 12 bảng quan hệ, 12 khóa chính (gồm 2 khóa chính tổ hợp), 13 khóa ngoại.
- 17 quy tắc nghiệp vụ (BR01–BR18, không có BR08), 5 ràng buộc CHECK, 1 ràng buộc UNIQUE và 3 chỉ mục bổ sung.
- 4 Stored Procedures và 1 Stored Function.
- Mô hình EER và lược đồ quan hệ được trình bày trong báo cáo `Thực hành lab1,2.docx`.

Mô hình chuyên môn hóa (Specialization):

- `PERSON` → `KHACH_HANG`, `NHAN_VIEN`: Partial, Overlapping.
- `NHAN_VIEN` → `NHAN_VIEN_FULL_TIME`, `NHAN_VIEN_PART_TIME`: Total, Disjoint theo thiết kế EER.
- `NHAN_VIEN_FULL_TIME` → `QUAN_LY`: Partial.

Các quan hệ nhiều–nhiều được chuyển thành bảng trung gian `PHIM_THE_LOAI` và `CHI_TIET_HOA_DON`.

## 3. Triển khai và lập trình – Lab 02

| Phần | Nội dung đã xây dựng |
|---|---|
| A. Triển khai CSDL | 455 bản ghi mẫu mới trên 12 bảng, 18 truy vấn SQL, 4 tài khoản, 4 role, 1 view giới hạn thông tin khách hàng và 21 ca kiểm thử phân quyền. |
| B. Lập trình CSDL | Kết nối và đóng kết nối, đọc dữ liệu, INSERT/UPDATE/DELETE, COMMIT/ROLLBACK, gọi Stored Procedures và Function; 6 ca kiểm thử ghi và 8 ca kiểm thử bán hàng. |
| C. Xây dựng API | 15 endpoint REST, xác thực HTTP Basic, phân quyền Sales/Manager, kiểm tra đầu vào và 39 ca kiểm thử tích hợp API. |
| D. Nguồn dữ liệu | Dữ liệu phim tham khảo Database Star; thông tin nghiệp vụ và giao dịch được giả lập. |
| Giao diện bổ sung | Trang `/ui` sử dụng API thật để trình diễn chức năng Lab 02. |

### Chức năng chính

| Chức năng | Khách truy cập | Sales | Manager |
|---|:---:|:---:|:---:|
| Tổng quan, tra cứu phim, thể loại và kho CD | Có | Có | Có |
| Xem mã và họ tên khách hàng | — | Có | Có |
| Xem danh sách và phân loại nhân viên | — | — | Có |
| Tạo hóa đơn, thêm chi tiết, tính tiền và hoàn tất | — | Có | — |
| Cập nhật giá bán và tồn kho | — | — | Có |
| Thống kê doanh thu theo khoảng ngày | — | — | Có |

MySQL sử dụng các tài khoản `cd_admin`, `cd_manager`, `cd_sales`, `cd_viewer` và role tương ứng. Nhân viên bán hàng gọi Stored Procedures thay vì ghi trực tiếp vào bảng hóa đơn. Mật khẩu API và mật khẩu MySQL được quản lý riêng bằng biến môi trường.

## 4. Cấu trúc repository

```text
CD-MOVIE/
├── .github/workflows/
│   ├── mysql-lab.yml
│   ├── python-lab.yml
│   └── api-lab.yml
├── SQL/
│   ├── MovieCDStore_schema.sql
│   ├── MovieCDStore_indexes.sql
│   ├── MovieCDStore_routines.sql
│   ├── MovieCDStore_routines_demo.sql
│   ├── MovieCDStore_sample_data.sql
│   ├── MovieCDStore_queries.sql
│   ├── MovieCDStore_security.sql
│   └── MovieCDStore_security_tests.sql
├── app/
│   ├── database.py
│   ├── test_connection.py
│   ├── read_data.py
│   ├── write_data.py
│   ├── sales_data.py
│   ├── api.py
│   ├── test_api_catalog.py
│   ├── test_api_operations.py
│   └── ui.html
├── requirements.txt
├── Thực hành lab1,2.docx
└── README.md
```

## 5. Hướng dẫn chạy

### 5.1. Triển khai MySQL

Trên MySQL 8.4 với cơ sở dữ liệu thử nghiệm mới, sử dụng tài khoản quản trị để chạy các file trong thư mục `SQL/` theo thứ tự:

1. `MovieCDStore_schema.sql` – Tạo bảng và ràng buộc.
2. `MovieCDStore_indexes.sql` – Tạo chỉ mục bổ sung.
3. `MovieCDStore_routines.sql` – Tạo thủ tục và hàm.
4. `MovieCDStore_routines_demo.sql` – Tạo dữ liệu demo và kiểm thử bán hàng.
5. `MovieCDStore_sample_data.sql` – Nhập 455 bản ghi mẫu.
6. `MovieCDStore_queries.sql` – Thực hiện các truy vấn đọc dữ liệu.
7. `MovieCDStore_security.sql` – Tạo tài khoản, role, view và cấp quyền. Lưu mật khẩu được sinh ra ở nơi riêng tư.
8. `MovieCDStore_security_tests.sql` – Chạy từng ca bằng đúng tài khoản tương ứng; một số lỗi từ chối truy cập là kết quả mong đợi.

Không chạy lại các script tạo bảng hoặc nhập dữ liệu có mã cố định trên CSDL đã triển khai. Tồn kho mẫu đã được tính sau các giao dịch lịch sử.

### 5.2. Khởi động ứng dụng

Từ thư mục gốc repository, với Python và MySQL đã sẵn sàng:

```bash
python -m pip install -r requirements.txt
```

Thiết lập các biến môi trường trước khi chạy FastAPI:

| Biến | Giá trị hoặc mục đích |
|---|---|
| `DB_HOST` | `127.0.0.1` |
| `DB_PORT` | `3307` (điều chỉnh theo cổng MySQL đang sử dụng) |
| `DB_NAME` | `MovieCDStore` |
| `DB_USER` | `cd_viewer` |
| `DB_PASSWORD` | Mật khẩu MySQL của `cd_viewer` |
| `DB_SALES_PASSWORD` | Mật khẩu MySQL của `cd_sales` |
| `DB_MANAGER_PASSWORD` | Mật khẩu MySQL của `cd_manager` |
| `API_SALES_PASSWORD` | Mật khẩu API do người triển khai đặt cho `sales` |
| `API_MANAGER_PASSWORD` | Mật khẩu API do người triển khai đặt cho `manager` |
| `API_SALES_EMPLOYEE_ID` | `90102` nếu đã nhập dữ liệu demo và nhân viên này đang làm việc |

Kiểm tra kết nối và khởi động:

```bash
python app/test_connection.py
python -m uvicorn api:app --app-dir app --host 127.0.0.1 --port 8000
```

| Địa chỉ | Chức năng |
|---|---|
| [localhost:8000/ui](http://127.0.0.1:8000/ui) | Giao diện quản lý cửa hàng |
| [localhost:8000/docs](http://127.0.0.1:8000/docs) | Swagger UI để kiểm thử API |
| [localhost:8000/redoc](http://127.0.0.1:8000/redoc) | Tài liệu API |
| [localhost:8000/health](http://127.0.0.1:8000/health) | Kiểm tra kết nối CSDL |

### 5.3. Chạy trên GitHub Codespaces

Chọn **Code → Codespaces** trên GitHub và mở Codespace. Cần có MySQL (ví dụ container Docker ánh xạ cổng 3307), dữ liệu đã nhập, các tài khoản phù hợp với host kết nối và các biến môi trường ở mục 5.2.

Trong Codespaces, chạy Uvicorn với `--host 0.0.0.0` thay cho `127.0.0.1`. Mở tab **PORTS → 8000 → Open in Browser**, sau đó thêm `/ui` hoặc `/docs` vào cuối URL. Giữ cổng ở chế độ **Private**. Nếu đã tạo script `~/start-moviecd.sh` riêng trong Codespace cũ, có thể sử dụng lại script đó để khởi động MySQL và FastAPI.

Không cần nhập lại dữ liệu nếu container và CSDL cũ vẫn còn. Codespaces không phải dịch vụ hosting hoạt động 24/7; khi môi trường dừng, cần mở lại và khởi động ứng dụng.

## 6. Kiểm thử tự động và tiến độ

Mở tab [GitHub Actions](https://github.com/TMT-221/CD-MOVIE/actions), chọn workflow tương ứng rồi chọn **Run workflow** nếu muốn kiểm thử thủ công. Mỗi workflow tạo một môi trường MySQL tạm thời và tự thực thi các phép thử.

Kết quả gần nhất được đối chiếu ngày **24/11/2026**:

| Workflow | Kết quả | Minh chứng |
|---|---|---|
| MySQL Lab Tests | Thành công – 21 ca phân quyền | [Log](https://github.com/TMT-221/CD-MOVIE/actions/runs/45355742491) – `ec08e06` |
| Python Lab Tests | Thành công – kết nối, đọc, ghi, nghiệp vụ | [Log](https://github.com/TMT-221/CD-MOVIE/actions/runs/45426240830) – `34db601` |
| API Lab Tests | Thành công – 39 ca kiểm thử API | [Log](https://github.com/TMT-221/CD-MOVIE/actions/runs/45426240592) – `34db601` |

- [x] Lab 01: Thiết kế EER, mô hình quan hệ, DDL, Stored Procedures và Function.
- [x] Lab 02 A: Triển khai CSDL, dữ liệu mẫu, truy vấn SQL, phân quyền và kiểm thử.
- [x] Lab 02 B: Lập trình kết nối, đọc, ghi dữ liệu và xử lý nghiệp vụ bằng Python.
- [x] Lab 02 C: Xây dựng và kiểm thử REST API.
- [x] Lab 02 D: Xác định và ghi nguồn trong SQL dữ liệu mẫu.
- [x] Bổ sung mã nguồn giao diện web `/ui` phục vụ trình diễn.
- [ ] Kiểm thử thao tác giao diện trực tiếp trên trình duyệt và chốt minh chứng trong báo cáo.

Ba workflow đã chạy thành công tại các commit ghi trong bảng; kiểm thử API không đồng nghĩa với kiểm thử toàn bộ giao diện web. Nội dung báo cáo Word cuối cùng cần được kiểm tra riêng trước khi nộp.

## 7. Nguồn dữ liệu

Nguồn tham khảo: [Database Star – Sample Database: Movies](https://www.databasestar.com/sample-database-movies/).

Tên phim, năm phát hành và thời lượng của 20 phim được lấy từ kết quả truy vấn mẫu của nguồn trên. Tên đạo diễn và phân loại thể loại tiếng Việt được bổ sung thủ công. Dữ liệu khách hàng, nhân viên, giá bán, tồn kho và hóa đơn là dữ liệu giả lập phục vụ học tập. Thông tin nguồn được ghi trong `SQL/MovieCDStore_sample_data.sql`.

## 8. Giới hạn hiện tại

- BR01 (Total Disjoint) và BR06 (mỗi phim có ít nhất một thể loại) chưa được bảo đảm hoàn toàn bằng ràng buộc CSDL; BR06 được hỗ trợ trong luồng thêm phim bằng Transaction tại Python.
- Các quy tắc lập hóa đơn, tồn kho và đơn giá lịch sử được kiểm soát qua Stored Procedures và phân quyền, không phải bất biến được cưỡng chế trên mọi thao tác SQL của quản trị viên.
- Giao diện dành cho mục đích thực hành, chưa có chức năng hủy hóa đơn, xem đầy đủ lịch sử hóa đơn hoặc quản lý tài khoản riêng cho từng nhân viên. API sử dụng tài khoản đại diện và cần bảo vệ bằng HTTPS nếu triển khai ngoài môi trường cục bộ.
- Không đưa mật khẩu, token hoặc thông tin kết nối bí mật lên repository.

**Dự án phục vụ mục đích học tập và trình diễn môn INT1313.**
