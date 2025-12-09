#!/bin/bash
# InfluxDB Initialization Script for FL Simulator
# Created: 2025-11-29
# This script runs on container startup to create additional buckets and retention policies

set -e

echo "Initializing InfluxDB for FL Simulator..."

# Wait for InfluxDB to be ready
sleep 5

# Create additional buckets for data lifecycle management
influx bucket create \
  --name fl-metrics-hourly \
  --org flower \
  --retention 90d \
  --token "${DOCKER_INFLUXDB_INIT_ADMIN_TOKEN}" \
  2>/dev/null || echo "Bucket fl-metrics-hourly already exists"

influx bucket create \
  --name fl-metrics-archive \
  --org flower \
  --retention 365d \
  --token "${DOCKER_INFLUXDB_INIT_ADMIN_TOKEN}" \
  2>/dev/null || echo "Bucket fl-metrics-archive already exists"

# Create a bucket for Prometheus remote write
influx bucket create \
  --name prometheus \
  --org flower \
  --retention 7d \
  --token "${DOCKER_INFLUXDB_INIT_ADMIN_TOKEN}" \
  2>/dev/null || echo "Bucket prometheus already exists"

echo "InfluxDB initialization complete!"
echo "Available buckets:"
influx bucket list --org flower --token "${DOCKER_INFLUXDB_INIT_ADMIN_TOKEN}"
