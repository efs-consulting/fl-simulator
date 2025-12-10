// FL Simulator Flux Queries for InfluxDB
// Created: 2025-11-29
// These queries can be used in Grafana or directly in InfluxDB

// ============================================
// 1. GLOBAL TRAINING PROGRESS QUERIES
// ============================================

// Query: Current Round and Aggregated Metrics
// Use: Real-time dashboard stat panels
currentRoundMetrics = from(bucket: "fl-metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] =~ /fl_server_.*/)
  |> last()
  |> pivot(rowKey: ["_time"], columnKey: ["_measurement"], valueColumn: "_value")

// Query: Convergence Curve - Aggregated R² Over Time
// Use: Time series panel showing training progress
convergenceR2 = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_aggregated_train_r2")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "train_r2")

// Query: Convergence Curve - Aggregated Loss Over Time
// Use: Time series panel showing loss reduction
convergenceLoss = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_aggregated_loss")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "loss")

// Query: Central Evaluation Progress
// Use: Separate panel for server-side evaluation
centralEvaluation = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] =~ /fl_server_cetral_evaluation_.*/)
  |> pivot(rowKey: ["_time"], columnKey: ["_measurement"], valueColumn: "_value")
  |> yield(name: "central_eval")


// ============================================
// 2. PER-CLIENT PERFORMANCE QUERIES
// ============================================

// Query: All Clients R² Comparison
// Use: Multi-line chart comparing client performance
clientR2Comparison = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_client_train_r2")
  |> group(columns: ["client_id"])
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "client_r2")

// Query: Single Client Detailed Metrics
// Use: Detailed view when filtering by client_id variable
// Replace ${client_id} with Grafana variable
singleClientMetrics = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["client_id"] == "${client_id}")
  |> filter(fn: (r) => r["_measurement"] =~ /fl_client_.*/)
  |> pivot(rowKey: ["_time"], columnKey: ["_measurement"], valueColumn: "_value")

// Query: Client Resource Usage Heatmap
// Use: Heatmap panel showing CPU/memory across clients
clientResourceHeatmap = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) =>
      r["_measurement"] == "fl_client_cpu_fit_percent" or
      r["_measurement"] == "fl_client_memory_fit_mb"
  )
  |> group(columns: ["client_id", "_measurement"])
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)

// Query: Straggler Detection - Clients Above 2x Mean Latency
// Use: Table or alert panel
stragglerDetection = from(bucket: "fl-metrics")
  |> range(start: -10m)
  |> filter(fn: (r) => r["_measurement"] == "fl_client_cpu_time_usage")
  |> group(columns: ["client_id"])
  |> mean()
  |> map(fn: (r) => ({
      r with
      is_straggler: r._value > 2.0 * (
        from(bucket: "fl-metrics")
          |> range(start: -10m)
          |> filter(fn: (r) => r["_measurement"] == "fl_client_cpu_time_usage")
          |> mean()
          |> findRecord(fn: (key) => true, idx: 0)
      )._value
  }))


// ============================================
// 3. ROUND-BY-ROUND ANALYSIS QUERIES
// ============================================

// Query: Metrics by Round Number
// Use: Table showing progression across rounds
metricsByRound = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_round")
  |> group()
  |> sort(columns: ["_time"])
  |> map(fn: (r) => ({
      _time: r._time,
      round: r._value
  }))

// Query: Round Duration Analysis
// Use: Bar chart showing time per round
roundDuration = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_round")
  |> elapsed(unit: 1s)
  |> filter(fn: (r) => r.elapsed > 0)
  |> yield(name: "round_duration")

// Query: Client Participation Per Round
// Use: Stacked bar chart showing active clients
clientParticipation = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_client_train_r2")
  |> group(columns: ["_time"])
  |> count()
  |> yield(name: "active_clients")


// ============================================
// 4. ADVANCED ANALYSIS QUERIES
// ============================================

// Query: Training Convergence Rate (Derivative of Loss)
// Use: Detect when training is stagnating
convergenceRate = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_aggregated_loss")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> derivative(unit: 1m, nonNegative: false)
  |> yield(name: "loss_derivative")

// Query: Model Quality Over Time (Moving Average of R²)
// Use: Smoothed convergence visualization
smoothedR2 = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_aggregated_train_r2")
  |> aggregateWindow(every: 30s, fn: mean, createEmpty: false)
  |> movingAverage(n: 5)
  |> yield(name: "smoothed_r2")

// Query: Client Performance Distribution (Percentiles)
// Use: Box plot or distribution chart
clientPerformanceDistribution = from(bucket: "fl-metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "fl_client_train_r2")
  |> group()
  |> quantile(q: 0.5, method: "estimate_tdigest")
  |> yield(name: "median_r2")

// Query: Experiment Comparison (when tagged with experiment_id)
// Use: Overlay multiple experiment runs
experimentComparison = from(bucket: "fl-metrics")
  |> range(start: -7d)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_aggregated_train_r2")
  |> filter(fn: (r) => r["experiment_id"] == "${experiment_id}")
  |> group(columns: ["experiment_id"])
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)


// ============================================
// 5. DOWNSAMPLING TASKS (for retention)
// ============================================

// Task: Hourly Aggregation for Long-term Storage
// Schedule: Every hour
// option task = {name: "downsample_fl_metrics_1h", every: 1h}
hourlyDownsample = from(bucket: "fl-metrics")
  |> range(start: -2h, stop: -1h)
  |> filter(fn: (r) => r["_measurement"] =~ /fl_.*/)
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> to(bucket: "fl-metrics-hourly", org: "flower")

// Task: Daily Summary for Archive
// Schedule: Every day at midnight
// option task = {name: "archive_fl_metrics_1d", every: 1d}
dailyArchive = from(bucket: "fl-metrics-hourly")
  |> range(start: -2d, stop: -1d)
  |> filter(fn: (r) => r["_measurement"] =~ /fl_server_.*/)
  |> aggregateWindow(every: 1d, fn: mean, createEmpty: false)
  |> set(key: "_measurement", value: "fl_daily_summary")
  |> to(bucket: "fl-metrics-archive", org: "flower")


// ============================================
// 6. ANOMALY DETECTION QUERIES
// ============================================

// Query: Loss Spike Detection (>50% increase)
// Use: Alert trigger
lossSpikeDetection = from(bucket: "fl-metrics")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_aggregated_loss")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> difference()
  |> map(fn: (r) => ({
      r with
      spike_detected: r._value > 0.5 * (
        from(bucket: "fl-metrics")
          |> range(start: -10m, stop: -5m)
          |> filter(fn: (r) => r["_measurement"] == "fl_server_aggregated_loss")
          |> mean()
          |> findRecord(fn: (key) => true, idx: 0)
      )._value
  }))
  |> filter(fn: (r) => r.spike_detected == true)

// Query: R² Drop Detection
// Use: Alert when model quality degrades
r2DropDetection = from(bucket: "fl-metrics")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_aggregated_train_r2")
  |> last()
  |> filter(fn: (r) => r._value < 0.5)
  |> yield(name: "r2_below_threshold")
