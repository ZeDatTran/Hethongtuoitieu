#Hệ Thống Tưới Tiêu Thông Minh
Hệ thống quản lý và tự động hóa tưới tiêu thông minh, tích hợp IoT và học máy để tối ưu hóa việc tưới tiêu dựa trên dữ liệu cảm biến.
##Tính Năng
###Cho Người Dùng Thường

###Đăng ký tài khoản.
Đăng nhập vào hệ thống.
Theo dõi dữ liệu cảm biến (nhiệt độ, độ ẩm không khí, độ ẩm đất) theo thời gian thực.
Điều khiển bơm nước (bật/tắt thủ công hoặc tự động).
Thiết lập mục tiêu độ ẩm đất (min/max).
Lập lịch tưới tiêu với tùy chọn lặp lại hàng ngày.
Dự đoán lượng nước cần tưới bằng mô hình học máy.
Xem lịch sử dữ liệu cảm biến qua biểu đồ.

Cho Quản Trị Viên

Đăng ký tài khoản quản trị viên (yêu cầu mã xác thực).
Đăng nhập vào hệ thống.
Quản lý thông tin người dùng (xem, chỉnh sửa, xóa).
Theo dõi dữ liệu cảm biến của từng người dùng.
Hỗ trợ giao diện sáng/tối và đa ngôn ngữ (Tiếng Việt/Tiếng Anh).

Công Nghệ Sử Dụng
Backend

Python
Flask
SQLAlchemy (SQLite)
Bcrypt Password Hashing
Joblib
Scikit-learn
XGBoost

Frontend

HTML
CSS (TailwindCSS cho admin)
JavaScript
Chart.js
SweetAlert2

IoT

Adafruit IO

Cài Đặt và Chạy
Yêu Cầu Hệ Thống

Python 3.8 trở lên
SQLite
Trình duyệt web (Chrome, Firefox, v.v.)
Kết nối internet (để giao tiếp với Adafruit IO)

Cài Đặt
pip install flask flask-sqlalchemy flask-bcrypt requests joblib pandas scikit-learn xgboost numpy

Cấu Hình Môi Trường

Cập nhật thông tin Adafruit IO trong app.py:

AIO_USERNAME="your_username"
AIO_KEY="your_aio_key"


Đảm bảo các feed trên Adafruit IO đã được tạo: temperature, humidity, soilmoisture, relaycontrol, autoenable, soilmoisturetarget, water.

Tạo Mô Hình Học Máy

Đảm bảo tệp data_core.csv tồn tại (dữ liệu huấn luyện với các cột như Temparature, Humidity, Moisture, SoilType, CropType, WaterNeeded).
Chạy train_models.py để tạo mô hình con:

python train_models.py


Chạy run_ensemble.py để tạo mô hình tổng hợp:

python run_ensemble.py

Chạy Ứng Dụng

Khởi động ứng dụng:

python app.py


Truy cập giao diện web tại: http://localhost:5000/login

API Endpoints
Authentication

POST /register - Đăng ký tài khoản người dùng.
GET /create-admin/<secret> - Đăng ký tài khoản quản trị viên (yêu cầu mã xác thực).
POST /login - Đăng nhập.
GET /logout - Đăng xuất.

Quản Lý Cảm Biến và Điều Khiển

GET /sensor_data - Lấy dữ liệu cảm biến (nhiệt độ, độ ẩm không khí, độ ẩm đất).
POST /control - Điều khiển bơm hoặc chế độ tự động.
GET /pump_state - Lấy trạng thái bơm.
GET /auto_state - Lấy trạng thái chế độ tự động.
POST /update_soil_target - Cập nhật mục tiêu độ ẩm đất.
GET /sensor_history - Xem lịch sử dữ liệu cảm biến.

Lập Lịch Tưới

POST /schedule - Tạo lịch tưới mới.
GET /schedules - Xem danh sách lịch tưới.
DELETE /delete_schedule/<id> - Xóa lịch tưới.

Dự Đoán Lượng Nước

POST /predict - Dự đoán lượng nước cần tưới.

Quản Lý Người Dùng (Admin)

GET /admin/users - Lấy danh sách người dùng.
GET /admin/user/<id> - Xem chi tiết người dùng.
POST /admin/user/<id> - Cập nhật thông tin người dùng.
DELETE /admin/user/<id> - Xóa người dùng.
GET /admin/sensor_data/<user_id> - Xem dữ liệu cảm biến của người dùng.

Bảo Mật

Mật khẩu được mã hóa bằng Bcrypt.
Phân quyền người dùng (user/admin).
Kiểm tra quyền truy cập cho các endpoint admin.
Mã xác thực đặc biệt cho đăng ký quản trị viên.

Đóng Góp

Fork repository.
Tạo branch mới: git checkout -b feature/new-feature.
Commit thay đổi: git commit -m 'Add new feature'.
Push lên branch: git push origin feature/new-feature.
Tạo Pull Request.


