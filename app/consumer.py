import pika
import threading
import time
from datetime import datetime, timedelta

# Dictionary เก็บเวลาล่าสุดของ customer_id
last_active = {}

def callback(ch, method, properties, body):
    user_id = body.decode()
    print(f"Received webhook for customer_id: {user_id}")
    
    # อัพเดตเวลาล่าสุดที่ได้รับ webhook สำหรับ customer_id นี้
    last_active[user_id] = datetime.now()

def check_inactivity():
    while True:
        now = datetime.now()
        for user_id, last_time in list(last_active.items()):
            if now - last_time > timedelta(minutes=1):
                print(f"คุณหายไปไหน customer_id: {user_id}")
                del last_active[user_id]
        time.sleep(10)  # ตรวจสอบทุกๆ 1 นาที

def start_consumer():
    # ตั้งค่า RabbitMQ connection
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='webhook_queue')

    channel.basic_consume(queue='webhook_queue', on_message_callback=callback, auto_ack=True)

    print('Waiting for messages. To exit press CTRL+C')

    # สร้าง thread สำหรับตรวจสอบ inactivity
    thread = threading.Thread(target=check_inactivity)
    thread.daemon = True
    thread.start()

    # เริ่มรับข้อความจาก RabbitMQ
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()

if __name__ == "__main__":
    start_consumer()
