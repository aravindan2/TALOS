#!/bin/bash

# Wait for Kafka to be ready
sleep 10

# Create Kafka topic
kafka-topics --create \
    --topic raw \
    --bootstrap-server ed-kafka:29092 \
    --partitions 1 \
    --replication-factor 1
