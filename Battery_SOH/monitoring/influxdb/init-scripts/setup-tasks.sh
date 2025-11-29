#!/bin/bash
# InfluxDB Task Setup Script for FL Simulator
# Created: 2025-11-29
# This script creates downsampling tasks after InfluxDB initialization

set -e

echo "Setting up InfluxDB tasks for FL Simulator..."

# Wait for InfluxDB to be fully ready
sleep 10

TOKEN="${DOCKER_INFLUXDB_INIT_ADMIN_TOKEN}"
ORG="flower"

# Create hourly downsampling task
influx task create \
  --org "$ORG" \
  --token "$TOKEN" \
  --name "fl_downsample_hourly" \
  --every "1h" \
  --offset "5m" \
  --flux '
from(bucket: "fl-metrics")
  |> range(start: -2h, stop: -1h)
  |> filter(fn: (r) => r["_measurement"] =~ /fl_server_.*/ or r["_measurement"] =~ /fl_client_.*/)
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> to(bucket: "fl-metrics-hourly", org: "flower")
' 2>/dev/null || echo "Task fl_downsample_hourly may already exist"

# Create daily archive task
influx task create \
  --org "$ORG" \
  --token "$TOKEN" \
  --name "fl_archive_daily" \
  --every "1d" \
  --offset "1h" \
  --flux '
from(bucket: "fl-metrics-hourly")
  |> range(start: -48h, stop: -24h)
  |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
  |> to(bucket: "fl-metrics-archive", org: "flower")
' 2>/dev/null || echo "Task fl_archive_daily may already exist"

echo "InfluxDB tasks setup complete!"
echo "Active tasks:"
influx task list --org "$ORG" --token "$TOKEN" 2>/dev/null || echo "Could not list tasks"
