from datetime import date
from sqlite3 import IntegrityError
from flask import Blueprint, current_app, jsonify, request
from .models import AdditionalInfo, User, db
import pandas as pd
from .function import handle_postback
import redis
import re
from cryptography.fernet import Fernet
import pika
from .producer import send_to_rabbitmq

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

bp = Blueprint('api', __name__)

global_kcal_value = None
global_customer_id = None
global_global_user_id_line = None
global_exer_amount = None

@bp.route('/', methods=['GET'])
def hello():
    print("success")
    return jsonify({'message': 'Hello, World!fuck'})

@bp.route('/edit', methods=['GET'])
def edit():
    
    return jsonify({'message': 'Hello, World!22'})

@bp.route('/redis-keys', methods=['GET'])
def get_redis_keys():
    redis_client = current_app.redis_client
    keys = redis_client.keys('*')
    values = {key: redis_client.get(key) for key in keys}
    return jsonify(values)

@bp.route('/echo', methods=['POST'])
def echo():
    
    name = request.args.get('name')
    weigth = request.args.get('weigth')
    height = request.args.get('height')
    sex = request.args.get('sex')
    age = request.args.get('age')
    customer_id = request.args.get('customer_id')

    
    if not all([name, weigth, height, sex, age, customer_id]):
        return jsonify({'error': 'All parameters are required'}), 400

    try:
        weigth = int(weigth)
        height = int(height)
        age = int(age)
    except ValueError:
        return jsonify({'error': 'Weight, height, and age must be integers'}), 400

    if sex == 'M':
        bmr = 66 + (13.7 * weigth) + (5 * height) - (6.8 * age)
    elif sex == 'W':
        bmr = 665 + (9.6 * weigth) + (1.8 * height) - (4.7 * age)
    else:
        return jsonify({'status': 'Invalid sex value'}), 400

    bmr = int(bmr)

    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    encrypted_data = cipher_suite.encrypt(customer_id.encode())

    existing_user = User.query.filter_by(customer_id=customer_id).first()
    





    if existing_user:
        print("Duplicate entry detected for customer_id:", customer_id)
        return jsonify({'message': 'ผู้ใช้งานซ้ำหากต้องการลบข้อมูลผู้ใช้กรุณาพิมพ์ . แล้ว เริ่มต้นใช้งาน'}), 200  

 
    new_user = User(keyword=name, weigth=weigth, height=height, sex=sex, customer_id=customer_id, age=age, bmr=bmr, encrypcustomer_id=encrypted_data, keydecrypt=key)
    
    try:
        db.session.add(new_user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'An error occurred while adding the user'}), 500

    

    return jsonify({'message': 'บันทึกผู้ใช้งานสำเร็จ', 'bmr': bmr}), 201  # ใช้รหัสสถานะ 201 Created


@bp.route('/delete', methods=['POST'])
def delete_user():
    customer_id = request.args.get('customer_id')

    if not customer_id:
        return jsonify({'error': 'Customer ID is required'}), 400

    user = User.query.filter_by(customer_id=customer_id).first()

    plaintext=user.encrypcustomer_id
    key=user.keydecrypt
    cipher_suite = Fernet(key)
    decrypted_data = cipher_suite.decrypt(plaintext).decode()
    print("customer_id is :",decrypted_data)
    if user:
        # ลบข้อมูลในตาราง AdditionalInfo ที่เกี่ยวข้องกับ user_id
        additional_infos = AdditionalInfo.query.filter_by(user_id=user.id).all()
        for info in additional_infos:
            db.session.delete(info)
        
        # ลบข้อมูลในตาราง User
        db.session.delete(user)
        db.session.commit()
        return jsonify({f'message': 'decrypted_data{decrypted_data', 'customer_id': decrypted_data})
    else:
        return jsonify({'error': 'User not found'}), 404



@bp.route('/problem', methods=['POST'])
def problem():
    customer_id = request.args.get('customer_id')
    problem = request.args.get('problem')
    kg = request.args.get('kg')

    print("id =======", customer_id)
    print("problem ========", problem)
    print("kg =======", kg)
    
    if not customer_id or not problem or not kg:
        return jsonify({'error': 'กรุณาใส่พารามิเตอร์ที่จำเป็น'}), 400

    user = User.query.filter_by(customer_id=customer_id).first()

    if not user:
        return jsonify({'error': 'ไม่พบผู้ใช้'}), 404

    bmr = user.bmr
    print("bmr =======", bmr)
    
    try:
        kg = kg.replace('=', '')
        kg = int(kg)
    except ValueError:
        return jsonify({'error': 'ค่า kg ไม่ถูกต้อง'}), 400

    if problem == 'U':
        calday = bmr + kg
    elif problem == 'D':
        calday = bmr - kg
    else:
        return jsonify({'error': 'ค่า problem ไม่ถูกต้อง'}), 400

    # สร้าง record ใหม่ในตาราง AdditionalInfo
    additional_info = AdditionalInfo(user_id=user.id, problem=problem, calday=calday)
    
    db.session.add(additional_info)
    db.session.commit()

    return jsonify({'message': 'สำเร็จ', 'calday': calday}), 200

@bp.route('/delete_additional_info', methods=['POST'])
def delete_additional_info():
    customer_id = request.args.get('customer_id')

    if not customer_id:
        return jsonify({'error': 'Customer ID is required'}), 400

    user = User.query.filter_by(customer_id=customer_id).first()
    
    if user:
        # ลบข้อมูลในตาราง AdditionalInfo ที่เกี่ยวข้องกับ user_id
        additional_infos = AdditionalInfo.query.filter_by(user_id=user.id).all()
        if additional_infos:
            for info in additional_infos:
                db.session.delete(info)
            db.session.commit()
            return jsonify({'message': 'AdditionalInfo entries deleted successfully', 'customer_id': customer_id})
        else:
            return jsonify({'message': 'No AdditionalInfo entries found for this user', 'customer_id': customer_id})
    else:
        return jsonify({'error': 'User not found'}), 404


exercise_df = pd.read_csv('D:/botnoi/chatbot/app/exercise_data.csv', encoding='cp874')

@bp.route('/searchexercise', methods=['GET'])
def search_exercise():
    global global_customer_id
    global global_exer_amount
    exer_name = request.args.get('exercise')
    customer_id = request.args.get('customer_id')
    

    
    if not exer_name:
        return jsonify({'error': 'Exercise name is required'}), 400

    print('exercise name:', exer_name)

    amount_match = re.search(r'\d+', exer_name)
    if amount_match:
        exer_amount = int(amount_match.group())
        exer_name = re.split(r'\d+', exer_name)[0].strip()  
    else:
        exer_amount = 1

    print("จำนวนคือ :",exer_amount)
    
    results_ex = exercise_df[exercise_df['exercise'].str.contains(exer_name, case=False, na=False)]
    
    print(results_ex) 
    

    results_list = results_ex.to_dict(orient='records')
    
    user = User.query.filter_by(customer_id=customer_id).first()
    global_customer_id = user.id
    global_exer_amount = exer_amount
    additional_info = AdditionalInfo.query.filter_by(user_id=user.id).first()
    calday = additional_info.calday
    print("calday :",calday)
        
    if redis_client.setnx(user.id, calday):
        print(f"Data for customer_id {user.id} set in Redis with value {calday}")
    else:
        print(f"Data for customer_id {user.id} already exists in Redis, not set again")
    flex_message = format_room_flex_ex(results_list) 
    line_payload = botnoipayload(flex_message)

    return jsonify(line_payload)


menu_df = pd.read_csv('D:/botnoi/chatbot/app/menu_data.csv', encoding='cp874')
topping_df = pd.read_csv('D:/botnoi/chatbot/app/topping_data.csv', encoding='cp874')

@bp.route('/search', methods=['GET'])
def search_food():
    global global_kcal_value
    global global_customer_id
    
    food_name = request.args.get('foodname')
    customer_id = request.args.get('customer_id')

    

    if not food_name:
        return jsonify({"error": "Please provide a food name to search for"}), 400

   
    user = User.query.filter_by(customer_id=customer_id).first()

    if ' ' in food_name:
        food_name, topping_name = food_name.split(' ', 1)
        
        # หาเลขจาก topping_name ถ้ามี
        amount_match = re.search(r'\d+', topping_name)
        if amount_match:
            amount = int(amount_match.group())
            topping_name = topping_name.split(amount_match.group())[0].strip()  # ตัดคำที่ต่อจากตัวเลข
        else:
            amount = 1

        results = menu_df[menu_df['menu'].str.contains(food_name, case=False, na=False)]
        resultst = topping_df[topping_df['menu'].str.contains(topping_name, case=False, na=False)]
        
        if not resultst.empty:
            kcal_value = resultst['kcal'].iloc[0] * amount
            print("จำนวน",amount)
        else:
            kcal_value = 0
        
        additional_info = AdditionalInfo.query.filter_by(user_id=user.id).first()
        calday = additional_info.calday
        
        kcal_value = kcal_value.item()
        
        global_customer_id = user.id
        global_kcal_value = kcal_value

        if redis_client.setnx(user.id, calday):
            print(f"Data for customer_id {user.id} set in Redis with value {calday}")
        else:
            print(f"Data for customer_id {user.id} already exists in Redis, not set again")


    else:
        results= menu_df[menu_df['menu'].str.contains(food_name, case=False, na=False)]
        resultst = pd.DataFrame()
        
        additional_info = AdditionalInfo.query.filter_by(user_id=user.id).first()
        calday = additional_info.calday

        kcal_value = 0
        global_customer_id = user.id
        global_kcal_value = kcal_value

        if redis_client.setnx(user.id, calday):
            print(f"Data for customer_id {user.id} set in Redis with value {calday}")
        else:
            print(f"Data for customer_id {user.id} already exists in Redis, not set again")
    

    print(results)
    print(resultst)

    results_list = results.to_dict(orient='records')
    
    flex_message = format_room_flex(results_list) 
    line_payload = botnoipayload(flex_message)

    return jsonify(line_payload)



@bp.route('/webhook', methods=['POST'])
def webhook():
    global global_kcal_value  
    global global_customer_id
    global global_user_id_line
    global global_exer_amount
    data = request.get_json()
    events = data.get('events', [])
    user_id = None
    for event in events:
        if 'source' in event and 'userId' in event['source']:
            user_id = event['source']['userId']
            global_user_id_line = user_id
            break  # หยุดเมื่อเจอ userId ครั้งแรก

    if not user_id:
        return jsonify({'message': 'No userId found in events'})

    
    send_to_rabbitmq(user_id)
    print("event",events)
    for event in events:
        if event['type'] == 'postback':
            user_id = event['source']['userId']
            global_user_id_line = user_id
            print("sending")
            
            handle_postback(event, global_kcal_value, global_customer_id, global_user_id_line, global_exer_amount)
    return jsonify({'message': 'ok'})


def format_room_flex(data):
    bubble_list = []
    for item in data:
        bubble = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "กรุณาเลือกอาหารจานหลัก",
                        "weight": "bold",
                        "size": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                             {
                                "type": "text",
                                "text": f"เมนู : {item['menu']}",
                                "wrap": True,
                                "size": "sm"
                            },
                            {
                                "type": "text",
                                "text": f"จำนวน : {item['amount']}",
                                "wrap": True,
                                "size": "sm"
                            },
                            {
                                "type": "text",
                                "text": f"แคลอรี่: {item['kcal']}",
                                "wrap": True,
                                "size": "sm"
                            },
                        ]
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "Success",
                            "data": f"food_success_{item['kcal']}"
                            
                            
                        },
                        "style": "primary",
                        "margin": "sm"
                    },
                ]
            }
        }
        bubble_list.append(bubble)
    carousel = {
        "type": "carousel",
        "contents": bubble_list
    }
    return carousel

def format_room_flex_ex(data):
    bubble_list = []
    for item in data:
        bubble = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "กรุณาเลือกกิจกรรมของคุณ",
                        "weight": "bold",
                        "size": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "margin": "lg",
                        "spacing": "sm",
                        "contents": [
                             {
                                "type": "text",
                                "text": f"กิจกรรม : {item['exercise']}",
                                "wrap": True,
                                "size": "sm"
                            },
                            {
                                "type": "text",
                                "text": f"อัตราการเผาผลาญ: {int(item['kcalburn'])}",
                                "wrap": True,
                                "size": "sm"
                            },
                        ]
                    },
                    {
                        "type": "button",
                        "action": {
                            "type": "postback",
                            "label": "Success",
                            "data": f"exercise_success_{item['kcalburn']}"
                        },
                        "style": "primary",
                        "margin": "sm"
                    },
                ]
            }
        }
        bubble_list.append(bubble)
    carousel = {
        "type": "carousel",
        "contents": bubble_list
    }
    return carousel

def botnoipayload(flexdata):
    out = {
        "response_type": "object",
        "line_payload": [{
            "type": "flex",
            "altText": "Upcoming Events",
            "contents": flexdata
        }]
    }
    return out
