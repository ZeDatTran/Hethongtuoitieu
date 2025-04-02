from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import requests
import joblib
from datetime import datetime
import threading
import time
import pandas as pd
from skopt import gp_minimize
from skopt.space import Real

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///irrigation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here' 
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Thông tin Adafruit IO
AIO_USERNAME = "dadanganh"
AIO_KEY = "aio_utKK49NRcofbGeGjPDFTUB5P7fz0"
AIO_HEADERS = {'X-AIO-Key': AIO_KEY}

# Load mô hình và các tệp hỗ trợ
try:
    model = joblib.load("water_model.pkl")
    scaler = joblib.load("scaler.pkl")
    encoder_soil = joblib.load("encoder_soil.pkl")
    encoder_crop = joblib.load("encoder_crop.pkl")
    print("Đã tải mô hình và các tệp hỗ trợ thành công")
except FileNotFoundError as e:
    print(f"Không tìm thấy file: {e}. Vui lòng kiểm tra các file mô hình!")
    model = None
except Exception as e:
    print(f"Lỗi khi tải mô hình hoặc tệp hỗ trợ: {e}")
    model = None

# Tên cột đúng khi train mô hình
feature_columns = ["Temparature", "Humidity", "Moisture", "SoilType", "CropType"]

# Mô hình User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Mô hình Schedule
class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    off_time = db.Column(db.DateTime, nullable=False)
    executed = db.Column(db.Boolean, default=False)

def send_feed_data(feed, value):
    try:
        url = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/{feed}/data"
        payload = {'value': value}
        response = requests.post(url, headers=AIO_HEADERS, json=payload)
        response.raise_for_status()
        print(f"Đã gửi {value} tới feed {feed}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gửi dữ liệu tới {feed}: {str(e)}")
        return False

def check_schedules():
    while True:
        with app.app_context():
            now = datetime.now()
            schedules = Schedule.query.filter_by(executed=False).all()
            print(f"Tìm thấy {len(schedules)} lịch chưa thực hiện")
            for schedule in schedules:
                if now >= schedule.scheduled_time and now < schedule.off_time:
                    send_feed_data('relaycontrol', 'ON')
                    print(f"Bật bơm lúc {schedule.scheduled_time}")
                elif now >= schedule.off_time:
                    success = send_feed_data('relaycontrol', 'OFF')
                    if success:
                        schedule.executed = True
                        db.session.commit()
                        print(f"Đã tắt bơm lúc {schedule.off_time}")
                    else:
                        print(f"Thất bại khi tắt bơm lúc {schedule.off_time}")
        time.sleep(10)

# Hàm bảo vệ tuyến đường
def login_required(f):
    def wrap(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form.get('confirm_password')
        if password != confirm_password:
            return render_template('auth.html', message="Mật khẩu không khớp", container_active=False)
        if User.query.filter_by(username=username).first():
            return render_template('auth.html', message="Tên người dùng đã tồn tại", container_active=False)
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('auth.html', container_active=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('index'))
        return render_template('auth.html', message="Tên người dùng hoặc mật khẩu không đúng", container_active=True)
    return render_template('auth.html', container_active=True)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/sensor_data')
@login_required
def sensor_data():
    feeds = ['temperature', 'humidity', 'soilmoisture']
    data = {}
    try:
        for feed in feeds:
            url = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/{feed}/data/last"
            response = requests.get(url, headers=AIO_HEADERS)
            response.raise_for_status()
            value = response.json()['value']
            data[feed] = value
        print("Dữ liệu cảm biến:", data)
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        print("Lỗi lấy dữ liệu cảm biến:", str(e))
        return jsonify({'error': 'Không lấy được dữ liệu từ Adafruit IO: ' + str(e)})

@app.route('/control', methods=['POST'])
@login_required
def control():
    feed = request.form['feed']
    value = request.form['value']
    success = send_feed_data(feed, value)
    print(f"Control request: feed={feed}, value={value}, success={success}")
    return jsonify({'success': success})

@app.route('/pump_state')
@login_required
def pump_state():
    try:
        url = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/relaycontrol/data/last"
        response = requests.get(url, headers=AIO_HEADERS)
        response.raise_for_status()
        state = response.json()['value']
        print("Trạng thái bơm từ Adafruit IO:", state)
        return jsonify({'state': state})
    except requests.exceptions.RequestException as e:
        print("Lỗi lấy trạng thái bơm:", str(e))
        return jsonify({'state': 'OFF', 'error': str(e)})

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    if model is None:
        print("Mô hình học máy không khả dụng trong predict")
        return jsonify({'error': 'Mô hình học máy không khả dụng. Vui lòng kiểm tra water_model.pkl'})
    try:
        # Lấy dữ liệu JSON từ yêu cầu POST
        data = request.get_json()
        print(f"Received data: {data}")

        # Chuyển đổi dữ liệu sang DataFrame
        input_data = pd.DataFrame([data])

        # Mã hóa loại đất và loại cây
        input_data["SoilType"] = encoder_soil.transform(input_data["SoilType"])
        input_data["CropType"] = encoder_crop.transform(input_data["CropType"])

        # Chuẩn hóa dữ liệu số
        input_data[["Temparature", "Humidity", "Moisture"]] = \
            scaler.transform(input_data[["Temparature", "Humidity", "Moisture"]])

        # Đảm bảo đúng thứ tự cột
        input_water = input_data[feature_columns]

        # Dự đoán bằng mô hình
        predicted_water = model.predict(input_water)[0]      

        # Tối ưu lượng nước bằng Bayesian Optimization
        space = [Real(0.5 * predicted_water, 1.5 * predicted_water, name="WaterAmount")]

        def water_usage_objective(water_amount):
            return abs(water_amount[0] - predicted_water)

        result = gp_minimize(water_usage_objective, space, n_calls=10, random_state=42)
        optimized_water = result.x[0]

        print(f"Predicted Water Usage: {predicted_water} ml/m2")
        print(f"Optimized Water Usage: {optimized_water} ml/m2")

        # Gửi dữ liệu tới Adafruit IO
        send_feed_data('relaycontrol', str(optimized_water))

        # Tạo phản hồi JSON
        response_data = {
            "PredictedWaterUsage": predicted_water,
            "OptimizedWaterUsage": optimized_water
        }
        return jsonify(response_data)

    except Exception as e:
        print(f"Error in predict: {e}")
        return jsonify({'error': str(e)}), 400

@app.route('/schedule', methods=['POST'])
@login_required
def schedule():
    try:
        scheduled_time_str = request.form['scheduled_time']
        off_time_str = request.form['off_time']
        scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%dT%H:%M')
        off_time = datetime.strptime(off_time_str, '%Y-%m-%dT%H:%M')
        
        if off_time <= scheduled_time:
            print("Lỗi: Thời gian tắt phải sau thời gian bật")
            return jsonify({'error': 'Thời gian tắt phải sau thời gian bật'})
        
        new_schedule = Schedule(scheduled_time=scheduled_time, off_time=off_time)
        db.session.add(new_schedule)
        db.session.commit()
        print(f"Đã lập lịch: Bật lúc {scheduled_time}, Tắt lúc {off_time}")
        return jsonify({'success': True})
    except ValueError as e:
        print("Lỗi dữ liệu lịch trong schedule:", str(e))
        return jsonify({'error': 'Dữ liệu lịch không hợp lệ'})
    except Exception as e:
        print("Lỗi trong schedule:", str(e))
        return jsonify({'error': str(e)})

@app.route('/schedules')
@login_required
def get_schedules():
    schedules = Schedule.query.filter_by(executed=False).all()
    print(f"Lấy danh sách lịch: {len(schedules)} mục")
    return jsonify([{'id': s.id, 'scheduled_time': s.scheduled_time.isoformat(), 'off_time': s.off_time.isoformat()} for s in schedules])

@app.route('/delete_schedule/<int:id>', methods=['DELETE'])
@login_required
def delete_schedule(id):
    try:
        schedule = Schedule.query.get(id)
        if not schedule:
            print(f"Không tìm thấy lịch với ID {id}")
            return jsonify({'error': 'Không tìm thấy lịch'}), 404
        
        db.session.delete(schedule)
        db.session.commit()
        print(f"Đã xóa lịch với ID {id}")
        return jsonify({'success': True})
    except Exception as e:
        print("Lỗi khi xóa lịch:", str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/check_connection')
@login_required
def check_connection():
    try:
        url = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds/temperature/data/last"
        response = requests.get(url, headers=AIO_HEADERS)
        response.raise_for_status()
        value = response.json()['value']
        print("Kiểm tra kết nối thành công:", value)
        return jsonify({'status': 'connected', 'message': f'Đã kết nối, giá trị mẫu: {value}'})
    except requests.exceptions.RequestException as e:
        print("Lỗi kiểm tra kết nối:", str(e))
        return jsonify({'status': 'disconnected', 'message': str(e)})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    threading.Thread(target=check_schedules, daemon=True).start()
    app.run(debug=True, host='0.0.0.0', port=5000)