Hệ Thống Tưới Tiêu Thông Minh
Tổng quan
Hệ thống tưới tiêu thông minh là một ứng dụng web được xây dựng để quản lý và tự động hóa quá trình tưới tiêu dựa trên dữ liệu cảm biến (nhiệt độ, độ ẩm không khí, độ ẩm đất). Hệ thống tích hợp với Adafruit IO để giao tiếp với phần cứng IoT, sử dụng mô hình học máy để dự đoán lượng nước cần tưới, và cung cấp giao diện quản lý cho cả người dùng thường và admin.
Tính năng chính

Người dùng thường:
Theo dõi dữ liệu cảm biến (nhiệt độ, độ ẩm không khí, độ ẩm đất) theo thời gian thực.
Điều khiển bơm nước (bật/tắt thủ công hoặc tự động).
Thiết lập mục tiêu độ ẩm đất (min/max).
Lập lịch tưới tiêu với tùy chọn lặp lại hàng ngày.
Dự đoán lượng nước cần tưới dựa trên mô hình học máy.
Xem lịch sử dữ liệu cảm biến qua biểu đồ.


Admin:
Quản lý người dùng (xem, chỉnh sửa, xóa).
Xem dữ liệu cảm biến của từng người dùng.
Hỗ trợ giao diện sáng/tối và đa ngôn ngữ (Tiếng Việt/Tiếng Anh).


Tích hợp IoT:
Gửi và nhận dữ liệu từ Adafruit IO (cảm biến, relay).
Chế độ tự động: Bật/tắt bơm dựa trên độ ẩm đất mục tiêu.


Dự đoán thông minh:
Sử dụng mô hình học máy tổng hợp (RandomForest, LinearRegression, XGBoost, MLP) để dự đoán lượng nước cần tưới.



Công nghệ sử dụng

Backend: Flask, SQLAlchemy (SQLite), Bcrypt, Joblib, Scikit-learn, XGBoost.
Frontend: HTML, CSS (TailwindCSS cho admin), JavaScript, Chart.js, SweetAlert2.
IoT: Adafruit IO.
Machine Learning: Mô hình tổng hợp (ensemble_model.pkl) được huấn luyện từ dữ liệu (data_core.csv).

Cấu trúc thư mục
project/
├── app.py                  # File chính của ứng dụng Flask
├── ensemble_model.py       # Định nghĩa mô hình tổng hợp (ModelEnsemble)
├── train_models.py         # Huấn luyện các mô hình con
├── run_ensemble.py         # Tạo mô hình tổng hợp (ensemble_model.pkl)
├── server.py               # WebSocket server (chưa sử dụng trong triển khai chính)
├── templates/              # Thư mục chứa các file giao diện HTML
│   ├── index.html          # Giao diện chính cho người dùng
│   ├── auth.html           # Giao diện đăng nhập/đăng ký
│   ├── admin.html          # Giao diện quản lý cho admin
├── static/                 # Thư mục chứa file tĩnh (CSS, JS)
│   ├── style.css           # CSS cho index.html
│   ├── styles.css          # CSS cho auth.html
├── models/                 # Thư mục chứa các mô hình con
│   ├── model_rf.pkl        # Mô hình RandomForest
│   ├── model_lr.pkl        # Mô hình LinearRegression
│   ├── model_xgb.pkl       # Mô hình XGBoost
│   ├── model_mlp.pkl       # Mô hình MLP
├── ensemble_model.pkl      # Mô hình tổng hợp
├── scaler.pkl              # Bộ chuẩn hóa dữ liệu
├── encoder_soil.pkl        # Bộ mã hóa loại đất
├── encoder_crop.pkl        # Bộ mã hóa loại cây
├── data_core.csv           # Dữ liệu huấn luyện (cần có để chạy train_models.py)
├── irrigation.db           # Cơ sở dữ liệu SQLite

Yêu cầu cài đặt
Yêu cầu phần mềm

Python 3.8 trở lên
Trình duyệt web (Chrome, Firefox, v.v.)
Kết nối internet (để giao tiếp với Adafruit IO)

Thư viện Python cần thiết
Cài đặt các thư viện bằng lệnh:
pip install flask flask-sqlalchemy flask-bcrypt requests joblib pandas scikit-learn xgboost numpy

Tài khoản Adafruit IO

Đăng ký tài khoản tại Adafruit IO.
Tạo các feed cần thiết: temperature, humidity, soilmoisture, relaycontrol, autoenable, soilmoisturetarget, water.
Cập nhật thông tin tài khoản trong app.py:AIO_USERNAME = "your_username"
AIO_KEY = "your_aio_key"



Cách chạy hệ thống
Bước 1: Tạo mô hình học máy

Đảm bảo tệp data_core.csv tồn tại trong thư mục dự án (chứa dữ liệu huấn luyện với các cột như Temparature, Humidity, Moisture, SoilType, CropType, WaterNeeded, v.v.).
Chạy train_models.py để tạo các mô hình con và tệp hỗ trợ:python train_models.py


Kết quả: Tạo scaler.pkl, encoder_soil.pkl, encoder_crop.pkl, và các mô hình con trong thư mục models/.


Chạy run_ensemble.py để tạo mô hình tổng hợp:python run_ensemble.py


Kết quả: Tạo ensemble_model.pkl.



Bước 2: Chuẩn bị cơ sở dữ liệu

Cơ sở dữ liệu irrigation.db sẽ được tự động tạo khi chạy app.py.
Nếu gặp lỗi liên quan đến cột auto_mode, mở SQLite và thêm cột:sqlite3 irrigation.db
ALTER TABLE configuration ADD COLUMN auto_mode TEXT DEFAULT 'OFF';
UPDATE configuration SET auto_mode = 'OFF' WHERE auto_mode IS NULL;



Bước 3: Chạy ứng dụng

Đảm bảo tất cả tệp cần thiết (mô hình, giao diện) đã có trong thư mục dự án.
Chạy app.py:python app.py


Mở trình duyệt và truy cập: http://localhost:5000/login

Bước 4: Sử dụng hệ thống

Đăng nhập/Đăng ký:
Sử dụng tài khoản admin mặc định: admin / admin123 (nếu đã tạo).
Hoặc đăng ký tài khoản mới.


Người dùng thường:
Theo dõi dữ liệu cảm biến và điều khiển bơm.
Bật chế độ tự động để hệ thống tự động bật/tắt bơm dựa trên độ ẩm đất (mục tiêu mặc định: 40% - 60%).
Dự đoán lượng nước và lập lịch tưới.


Admin:
Truy cập http://localhost:5000/admin để quản lý người dùng.



Một số lưu ý

Kết nối Adafruit IO:
Đảm bảo kết nối internet ổn định để giao tiếp với Adafruit IO.
Kiểm tra trạng thái kết nối trên giao diện (phần "Trạng thái kết nối").


Tệp data_core.csv:
Nếu không có tệp này, bạn cần tạo dữ liệu huấn luyện với các cột phù hợp. Ví dụ:Temparature,Humidity,Moisture,SoilType,CropType,Nitrogen,Potassium,Phosphorous,WaterNeeded,FertilizerName
25,60,50,Loamy,Paddy,30,20,10,500,FertilizerA




Chế độ tự động:
Relay sẽ phản ứng ngay lập tức khi bật chế độ tự động nếu độ ẩm đất không nằm trong khoảng mục tiêu.
Hệ thống kiểm tra định kỳ mỗi 10 giây để điều chỉnh relay khi độ ẩm thay đổi.



Khắc phục sự cố

Lỗi kết nối Adafruit IO:
Kiểm tra AIO_USERNAME và AIO_KEY trong app.py.
Đảm bảo feed tồn tại và có quyền truy cập.


Lỗi mô hình học máy:
Đảm bảo các tệp mô hình (ensemble_model.pkl, v.v.) tồn tại.
Chạy lại train_models.py và run_ensemble.py nếu cần.


Lỗi cơ sở dữ liệu:
Kiểm tra irrigation.db và đảm bảo bảng configuration có cột auto_mode.




