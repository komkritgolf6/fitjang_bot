from sqlite3 import IntegrityError
from .models import User, db
import requests
import redis

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

def send_message(message, user_id):
    LINE_ACCESS_TOKEN = "Q4+Wps9H1JpRw9BmMp1Yev59S+tZwFTVNvsNJBnEvFyPXC1oSMAkpMW9hJ1uwn4oJGuPf7v2i9KqRSjjdaBz8BRJ7gi34c4NuS8qgkPJUUiBdpqR3ue30E+UcEADvMYaTmz6yTZ7WBWohj8MW+EKLQdB04t89/1O/w1cDnyilFU="
    LINE_API_URL = "https://api.line.me/v2/bot/message/push"
    

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + LINE_ACCESS_TOKEN,
    }
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    response = requests.post(LINE_API_URL, headers=headers, json=payload)
    print(f"Message '{message}' sent. Response Status Code:", response.status_code)

def handle_postback(event, kcal_value, customer_id, user_id, exer_amount):
    data = event['postback']['data']
    if data.startswith("food_success_"):
        kcal_item = data[len("food_success_"):]
        kcal_item = int(kcal_item)
        totalcal = kcal_item + kcal_value
        print("id is :", customer_id)
        print("totalcal is : ", totalcal)
        print("Uer_idline issss:", user_id)
        calday = redis_client.get(customer_id)
        if calday is None:
            calday = 0
        else:
            calday = int(calday)

        print(f"calday redis is:", calday)
        caldayresult = calday - totalcal

        insertredis(caldayresult, customer_id, user_id)
    
    elif data.startswith("exercise_success_"):
        kcalburn_item = data[len("exercise_success_"):]
        kcalburn_item = float(kcalburn_item)
        kcalburn_item = int(kcalburn_item)
        
        print("customer_id:", customer_id)
        print("exer_amount issssss:",exer_amount)
        calday = redis_client.get(customer_id)
        if calday is None:
            calday = 0
        else:
            calday = int(calday)


        
        caldayresult = calday + (kcalburn_item*exer_amount)
        print("calorie burn is : ",caldayresult)
        insertredis(caldayresult, customer_id, user_id)
        

    elif data.startswith("delete_"):
        menu_item = data[len("delete_"):]
        print(f"Delete item: {menu_item}")

def insertredis(caldayresult , customer_id, user_id):
    print("caldayresult:", caldayresult)
    print("customer_id:", customer_id)
    print("user_id isssssss:", user_id)

    user = User.query.filter_by(id=customer_id).first()

    if user:
        try:
            # เพิ่มข้อมูล line_id ในคอลัมน์ line_id ของ user
            user.line_id = user_id
            db.session.commit()
            
        except IntegrityError:
            # กรณีเกิดข้อผิดพลาดในการ commit ข้อมูล
            db.session.rollback()
            print("An error occurred while adding line_id for user:", user)
    else:
        print("User with customer_id not found.")


    send_message(f"บันทึกเรียบร้อยคุณสามารถทานอาหารได้อีก {caldayresult} กิโลแคลอรี่", user_id)

    redis_client.set(customer_id, caldayresult)
    print(f"Data for customer_id {customer_id} set in Redis with value {caldayresult}")
    

def check_goal(redis_data):
    for key, value in redis_data.items():
        value_int = int(value)
        if value_int <= 350:
            print(f"รายการที่ {key} (ค่า: {value_int}): คุณทำสำเร็จเป้าหมายในวันนี้")
        else:
            print(f"รายการที่ {key} (ค่า: {value_int}): คุณทำเป้าหมายไม่สำเร็จ อยากให้พยายามอีกหน่อย คุณทำได้")



    


