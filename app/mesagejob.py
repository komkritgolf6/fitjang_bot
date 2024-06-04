import requests
import schedule
import time
import threading
import redis


LINE_ACCESS_TOKEN = "Q4+Wps9H1JpRw9BmMp1Yev59S+tZwFTVNvsNJBnEvFyPXC1oSMAkpMW9hJ1uwn4oJGuPf7v2i9KqRSjjdaBz8BRJ7gi34c4NuS8qgkPJUUiBdpqR3ue30E+UcEADvMYaTmz6yTZ7WBWohj8MW+EKLQdB04t89/1O/w1cDnyilFU="
LINE_API_URL = "https://api.line.me/v2/bot/message/broadcast"

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + LINE_ACCESS_TOKEN,
}

def send_message(message_text):
    payload = {
        "messages": [
            {
                "type": "text",
                "text": message_text
            }
        ]
    }
    response = requests.post(LINE_API_URL, headers=headers, json=payload)
    print(f"Message '{message_text}' sent. Response Status Code:", response.status_code)

def flush_all_redis(host='localhost', port=6379, password=None):
    try:
        client = redis.StrictRedis(host=host, port=port, password=password, decode_responses=True)
        response = client.flushall()
        if response:
            print("All keys in all databases have been flushed.")
        else:
            print("Failed to flush all keys.")
    except Exception as e:
        print(f"An error occurred: {e}")

def schedule_messages():
    schedule.clear()

    schedule.every().day.at("05:08").do(send_message, "สวัสดีคุณคุณรับประทานอาหารมื้อเช้าหรือยัง")
    schedule.every().day.at("12:09").do(send_message, "สวัสดีคุณคุณรับประทานอาหารมื้อกลางวันหรือยัง")
    schedule.every().day.at("00:50").do(send_message, "สวัสดีคุณคุณรับประทานอาหารมื้อเย็นหรือยัง?")
    
    schedule.every().day.at("23:00").do(flush_all_redis)
    

    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler():
    scheduler_thread = threading.Thread(target=schedule_messages)
    scheduler_thread.daemon = True
    scheduler_thread.start()
