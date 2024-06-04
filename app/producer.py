import pika

def send_to_rabbitmq(user_id):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='webhook_queue')
    
    # ส่งข้อมูลไปยัง queue
    channel.basic_publish(exchange='',
                          routing_key='webhook_queue',
                          body=user_id)
    connection.close()

    print(f"Message sent to RabbitMQ for user_id: {user_id}")

