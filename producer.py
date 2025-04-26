from kafka import KafkaProducer
import json
import pandas as pd
import time

KAFKA_BROKER = "127.0.0.1:9092"  # use 9092 if accessing outside docker
TOPIC = "Raw_data"
CSV_PATH = "data.csv"  

# Load the CSV file using pandas
df = pd.read_csv(CSV_PATH)

# Initialize Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

# Iterate over each row and send to Kafka
for index, row in df.iterrows():
    data = row.to_dict()
    print(f"Producing: {data}")
    producer.send(TOPIC, data)
    time.sleep(2)  