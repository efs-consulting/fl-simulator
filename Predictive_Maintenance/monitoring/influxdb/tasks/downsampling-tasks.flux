// InfluxDB Downsampling Tasks for FL Simulator
// Created: 2025-11-29
// These tasks automatically aggregate and downsample FL metrics

// ============================================
// Task 1: Hourly Aggregation (Raw -> Hourly)
// Runs every hour, processes last 2 hours
// ============================================

option task_hourly = {
  name: "fl_downsample_hourly",
  every: 1h,
  offset: 5m
}

// Server metrics hourly aggregation
from(bucket: "fl-metrics")
  |> range(start: -2h, stop: -1h)
  |> filter(fn: (r) => r["_measurement"] =~ /fl_server_.*/)
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> set(key: "_measurement", value: "fl_server_hourly")
  |> to(bucket: "fl-metrics-hourly", org: "flower")

// Client metrics hourly aggregation
from(bucket: "fl-metrics")
  |> range(start: -2h, stop: -1h)
  |> filter(fn: (r) => r["_measurement"] =~ /fl_client_.*/)
  |> group(columns: ["client_id", "_measurement", "_field"])
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> set(key: "_measurement", value: "fl_client_hourly")
  |> to(bucket: "fl-metrics-hourly", org: "flower")


// ============================================
// Task 2: Daily Archive (Hourly -> Archive)
// Runs daily at 1 AM, processes last 2 days
// ============================================

option task_daily = {
  name: "fl_archive_daily",
  every: 1d,
  offset: 1h
}

// Server metrics daily archive
from(bucket: "fl-metrics-hourly")
  |> range(start: -48h, stop: -24h)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_hourly")
  |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({r with _measurement: "fl_server_daily"}))
  |> to(bucket: "fl-metrics-archive", org: "flower")

// Client metrics daily archive (aggregate across clients)
from(bucket: "fl-metrics-hourly")
  |> range(start: -48h, stop: -24h)
  |> filter(fn: (r) => r["_measurement"] == "fl_client_hourly")
  |> group(columns: ["_measurement", "_field"])
  |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({r with _measurement: "fl_client_daily_avg"}))
  |> to(bucket: "fl-metrics-archive", org: "flower")


// ============================================
// Task 3: Round Summary (After each round)
// Runs every 5 minutes, captures round completions
// ============================================

option task_round_summary = {
  name: "fl_round_summary",
  every: 5m,
  offset: 0m
}

// Capture round-level statistics
from(bucket: "fl-metrics")
  |> range(start: -10m)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_round")
  |> difference()
  |> filter(fn: (r) => r["_value"] > 0)  // New round detected
  |> map(fn: (r) => ({
      _time: r._time,
      _measurement: "fl_round_event",
      _field: "round_completed",
      _value: r._value,
      round: string(v: int(v: r._value))
  }))
  |> to(bucket: "fl-metrics-archive", org: "flower")


// ============================================
// Task 4: Performance Statistics (Weekly)
// Runs weekly, generates summary statistics
// ============================================

option task_weekly_stats = {
  name: "fl_weekly_statistics",
  every: 1w,
  offset: 2h
}

// Calculate weekly performance percentiles
from(bucket: "fl-metrics-hourly")
  |> range(start: -1w)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_hourly")
  |> filter(fn: (r) => r["_field"] == "fl_server_aggregated_train_r2")
  |> group()
  |> reduce(
      identity: {
        min: 1.0,
        max: 0.0,
        sum: 0.0,
        count: 0.0
      },
      fn: (r, accumulator) => ({
        min: if r._value < accumulator.min then r._value else accumulator.min,
        max: if r._value > accumulator.max then r._value else accumulator.max,
        sum: accumulator.sum + r._value,
        count: accumulator.count + 1.0
      })
  )
  |> map(fn: (r) => ({
      _time: now(),
      _measurement: "fl_weekly_stats",
      _field: "train_r2_stats",
      min_r2: r.min,
      max_r2: r.max,
      avg_r2: r.sum / r.count,
      sample_count: r.count
  }))
  |> to(bucket: "fl-metrics-archive", org: "flower")


// ============================================
// Task 5: Anomaly Log (Continuous)
// Runs every minute, logs anomalies
// ============================================

option task_anomaly_log = {
  name: "fl_anomaly_detection",
  every: 1m,
  offset: 0m
}

// Detect and log loss spikes
loss_current = from(bucket: "fl-metrics")
  |> range(start: -2m, stop: -1m)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_aggregated_loss")
  |> mean()
  |> findRecord(fn: (key) => true, idx: 0)

loss_previous = from(bucket: "fl-metrics")
  |> range(start: -5m, stop: -2m)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_aggregated_loss")
  |> mean()
  |> findRecord(fn: (key) => true, idx: 0)

// Log if loss increased by >50%
spike_detected = if loss_previous._value > 0.0 and (loss_current._value - loss_previous._value) / loss_previous._value > 0.5
  then 1.0
  else 0.0

array.from(rows: [{
  _time: now(),
  _measurement: "fl_anomaly_log",
  _field: "loss_spike",
  _value: spike_detected,
  current_loss: loss_current._value,
  previous_loss: loss_previous._value
}])
  |> filter(fn: (r) => r._value > 0.0)
  |> to(bucket: "fl-metrics-archive", org: "flower")
