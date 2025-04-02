import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib

# Load dữ liệu
df = pd.read_csv("data_core.csv")

# Xử lý dữ liệu thiếu
df.dropna(inplace=True)

# Mã hóa dữ liệu phân loại (SoilType, CropType)
encoder_soil = LabelEncoder()
encoder_crop = LabelEncoder()
df['SoilType'] = encoder_soil.fit_transform(df['SoilType'])
df['CropType'] = encoder_crop.fit_transform(df['CropType'])

# Lưu bộ mã hóa
joblib.dump(encoder_soil, "encoder_soil.pkl")
joblib.dump(encoder_crop, "encoder_crop.pkl")

# Chuẩn hóa dữ liệu số
scaler = StandardScaler()
df[['Temparature', 'Humidity', 'Moisture']] = scaler.fit_transform(
    df[['Temparature', 'Humidity', 'Moisture']]
)

# Lưu bộ chuẩn hóa
joblib.dump(scaler, "scaler.pkl")

# Chia dữ liệu thành input (X) và output (y)
X = df.drop(columns=['Nitrogen', 'Potassium', 'Phosphorous', 'WaterNeeded', 'FertilizerName'])  # Đầu vào
y = df['WaterNeeded']  # Nhãn cần dự đoán

# Chia dữ liệu train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Huấn luyện mô hình Random Forest
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Kiểm tra độ chính xác
score = model.score(X_test, y_test)
print(f"Regression Model Score: {score:.2f}")

# Lưu mô hình đã huấn luyện
joblib.dump(model, "water_model.pkl")


#  Author: Pham Gia Luong   Email: pham15032004@gmail.com