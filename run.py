from app import create_app
from app.mesagejob import start_scheduler
import threading
import requests
import pika
import time
from datetime import datetime, timedelta

# Dictionary to store the last active time of customer_id
last_active = {}

def send_message_mq(message, user_id):
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
def callback(ch, method, properties, body):
    user_id = body.decode()
    print(f"Received webhook for customer_id: {user_id}")
    
    # Update the last active time for this customer_id
    last_active[user_id] = datetime.now()

def check_inactivity():
    while True:
        now = datetime.now()
        for user_id, last_time in list(last_active.items()):
            if now - last_time > timedelta(minutes=2):
                send_message_mq("คุณหายไปไหนลืมฉันรึเปล่า", user_id)
                del last_active[user_id]
        time.sleep(30)  # Check every 1 minute

def start_consumer():
    # Set up RabbitMQ connection
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='webhook_queue')

    channel.basic_consume(queue='webhook_queue', on_message_callback=callback, auto_ack=True)

    print('Waiting for messages. To exit press CTRL+C')

    # Create a thread for checking inactivity
    thread = threading.Thread(target=check_inactivity)
    thread.daemon = True
    thread.start()

    # Start consuming messages from RabbitMQ
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()

app = create_app()

def start_consumer_thread():
    consumer_thread = threading.Thread(target=start_consumer)
    consumer_thread.start()

if __name__ == "__main__":
    start_consumer_thread()
    start_scheduler()
    app.run(debug=True, host='0.0.0.0')
