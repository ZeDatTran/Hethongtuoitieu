import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import joblib

# 1. Đọc dữ liệu từ file CSV
try:
    data = pd.read_csv('irrigation_data.csv')
    print("Đã đọc file irrigation_data.csv thành công")
except FileNotFoundError:
    print("Không tìm thấy file irrigation_data.csv. Vui lòng tạo file dữ liệu!")
    exit()

# 2. Xử lý dữ liệu
# Loại bỏ hàng có giá trị thiếu
data = data.dropna()
print(f"Số dòng dữ liệu sau khi loại bỏ giá trị thiếu: {len(data)}")

# Loại bỏ giá trị bất thường (temperature > 100)
data = data[data['temperature'] < 100]
print(f"Số dòng dữ liệu sau khi loại bỏ bất thường: {len(data)}")

# Sửa tên cột 'soilmiosture' thành 'soilmoisture'
if 'soilmiosture' in data.columns and 'soilmoisture' not in data.columns:
    data = data.rename(columns={'soilmiosture': 'soilmoisture'})
    print("Đã sửa tên cột 'soilmiosture' thành 'soilmoisture'")

# Ánh xạ soilmoisture về phạm vi 0-100
data['soilmoisture'] = data['soilmoisture'].apply(lambda x: (x - 157) * 100 / (466 - 157)).clip(0, 100)
print("Đã ánh xạ soilmoisture về phạm vi 0-100")

# 3. Chọn đặc trưng và mục tiêu
features = ['temperature', 'pressure', 'altitude']
X = data[features]  # Dữ liệu đầu vào
y = data['soilmoisture']  # Dữ liệu đầu ra
print("Đặc trưng (X):", X.head().to_string())
print("Mục tiêu (y):", y.head().to_string())

# 4. Huấn luyện mô hình Random Forest
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)
print("Đã huấn luyện mô hình Random Forest thành công")

# 5. Lưu mô hình thành file .pkl
joblib.dump(model, 'rf_model.pkl')
print("Đã lưu mô hình thành rf_model.pkl")