// FL Simulator Flux Queries for InfluxDB
// Created: 2025-11-29
// Updated: 2025-12-05 - Accuracy & Recall metrics (removed r2)
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

// Query: Convergence Curve - Aggregated Train Accuracy Over Time
// Use: Time series panel showing training progress
convergenceTrainAccuracy = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_train_accuracy")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "train_accuracy")

// Query: Convergence Curve - Aggregated Train Recall Over Time
// Use: Time series panel showing recall improvement
convergenceTrainRecall = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_train_recall")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "train_recall")

// Query: Convergence Curve - Aggregated Test Accuracy Over Time
// Use: Time series panel showing test accuracy
convergenceTestAccuracy = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_test_accuracy")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "test_accuracy")

// Query: Convergence Curve - Aggregated Test Recall Over Time
// Use: Time series panel showing test recall
convergenceTestRecall = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_test_recall")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "test_recall")

// Query: Convergence Curve - Aggregated Loss Over Time
// Use: Time series panel showing loss reduction
convergenceLoss = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_loss")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "loss")

// Query: Central Evaluation Accuracy
// Use: Separate panel for server-side evaluation accuracy
centralEvalAccuracy = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_central_evaluation" and r["_field"] == "accuracy")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "central_eval_accuracy")

// Query: Central Evaluation Recall
// Use: Separate panel for server-side evaluation recall
centralEvalRecall = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_central_evaluation" and r["_field"] == "recall")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "central_eval_recall")

// Query: Central Evaluation Loss
// Use: Separate panel for server-side evaluation loss
centralEvalLoss = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_central_evaluation" and r["_field"] == "loss")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "central_eval_loss")


// ============================================
// 2. PER-CLIENT PERFORMANCE QUERIES
// ============================================

// Query: All Clients Train Accuracy Comparison
// Use: Multi-line chart comparing client performance
clientTrainAccuracyComparison = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_client_metrics" and r["_field"] == "train_accuracy")
  |> group(columns: ["client_id"])
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "client_train_accuracy")

// Query: All Clients Train Recall Comparison
// Use: Multi-line chart comparing client recall
clientTrainRecallComparison = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_client_metrics" and r["_field"] == "train_recall")
  |> group(columns: ["client_id"])
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "client_train_recall")

// Query: All Clients Test Accuracy Comparison
// Use: Multi-line chart comparing test accuracy
clientTestAccuracyComparison = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_client_metrics" and r["_field"] == "test_accuracy")
  |> group(columns: ["client_id"])
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "client_test_accuracy")

// Query: All Clients Test Recall Comparison
// Use: Multi-line chart comparing test recall
clientTestRecallComparison = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_client_metrics" and r["_field"] == "test_recall")
  |> group(columns: ["client_id"])
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "client_test_recall")

// Query: Single Client Detailed Metrics
// Use: Detailed view when filtering by client_id variable
// Replace ${client_id} with Grafana variable
singleClientMetrics = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["client_id"] == "${client_id}")
  |> filter(fn: (r) => r["_measurement"] == "fl_client_metrics")
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")

// Query: Client Resource Usage Heatmap
// Use: Heatmap panel showing CPU/memory across clients
clientResourceHeatmap = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) =>
      (r["_measurement"] == "fl_client_metrics" and r["_field"] == "cpu_percent") or
      (r["_measurement"] == "fl_client_metrics" and r["_field"] == "memory_mb")
  )
  |> group(columns: ["client_id", "_field"])
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)

// Query: Straggler Detection - Clients Above 2x Mean CPU Time
// Use: Table or alert panel
stragglerDetection = from(bucket: "fl-metrics")
  |> range(start: -10m)
  |> filter(fn: (r) => r["_measurement"] == "fl_client_metrics" and r["_field"] == "cpu_time_sec")
  |> group(columns: ["client_id"])
  |> mean()
  |> map(fn: (r) => ({
      r with
      is_straggler: r._value > 2.0 * (
        from(bucket: "fl-metrics")
          |> range(start: -10m)
          |> filter(fn: (r) => r["_measurement"] == "fl_client_metrics" and r["_field"] == "cpu_time_sec")
          |> mean()
          |> findRecord(fn: (key) => true, idx: 0)
      )._value
  }))
  |> filter(fn: (r) => r.is_straggler == true)


// ============================================
// 3. ROUND-BY-ROUND ANALYSIS QUERIES
// ============================================

// Query: Metrics by Round Number
// Use: Table showing progression across rounds
metricsByRound = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_training_progress")
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
  |> filter(fn: (r) => r["_measurement"] == "fl_training_progress")
  |> elapsed(unit: 1s)
  |> filter(fn: (r) => r.elapsed > 0)
  |> yield(name: "round_duration")

// Query: Client Participation Per Round
// Use: Stacked bar chart showing active clients
clientParticipation = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_client_metrics")
  |> group(columns: ["_time"])
  |> count()
  |> yield(name: "active_clients")


// ============================================
// 4. ADVANCED ANALYSIS QUERIES
// ============================================

// Query: Training Convergence Rate - Accuracy Improvement
// Use: Detect when training is stagnating
convergenceRateAccuracy = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_train_accuracy")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> derivative(unit: 1m, nonNegative: false)
  |> yield(name: "accuracy_derivative")

// Query: Training Convergence Rate - Recall Improvement
// Use: Detect when recall is stagnating
convergenceRateRecall = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_train_recall")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> derivative(unit: 1m, nonNegative: false)
  |> yield(name: "recall_derivative")

// Query: Training Convergence Rate (Derivative of Loss)
// Use: Detect when loss improvement is stagnating
convergenceRateLoss = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_loss")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> derivative(unit: 1m, nonNegative: false)
  |> yield(name: "loss_derivative")

// Query: Model Quality Over Time (Moving Average of Train Accuracy)
// Use: Smoothed convergence visualization
smoothedTrainAccuracy = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_train_accuracy")
  |> aggregateWindow(every: 30s, fn: mean, createEmpty: false)
  |> movingAverage(n: 5)
  |> yield(name: "smoothed_train_accuracy")

// Query: Model Quality Over Time (Moving Average of Train Recall)
// Use: Smoothed recall convergence visualization
smoothedTrainRecall = from(bucket: "fl-metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_train_recall")
  |> aggregateWindow(every: 30s, fn: mean, createEmpty: false)
  |> movingAverage(n: 5)
  |> yield(name: "smoothed_train_recall")

// Query: Client Performance Distribution (Percentiles) - Accuracy
// Use: Box plot or distribution chart
clientAccuracyDistribution = from(bucket: "fl-metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "fl_client_metrics" and r["_field"] == "train_accuracy")
  |> group()
  |> quantile(q: 0.5, method: "estimate_tdigest")
  |> yield(name: "median_accuracy")

// Query: Client Performance Distribution (Percentiles) - Recall
// Use: Box plot or distribution chart
clientRecallDistribution = from(bucket: "fl-metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "fl_client_metrics" and r["_field"] == "train_recall")
  |> group()
  |> quantile(q: 0.5, method: "estimate_tdigest")
  |> yield(name: "median_recall")

// Query: Experiment Comparison (when tagged with experiment_id)
// Use: Overlay multiple experiment runs
experimentComparisonAccuracy = from(bucket: "fl-metrics")
  |> range(start: -7d)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_train_accuracy")
  |> filter(fn: (r) => r["experiment_id"] == "${experiment_id}")
  |> group(columns: ["experiment_id"])
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)

// Query: Experiment Comparison - Recall
// Use: Overlay multiple experiment runs for recall
experimentComparisonRecall = from(bucket: "fl-metrics")
  |> range(start: -7d)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_train_recall")
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
  |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_loss")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> difference()
  |> map(fn: (r) => ({
      r with
      spike_detected: r._value > 0.5 * (
        from(bucket: "fl-metrics")
          |> range(start: -10m, stop: -5m)
          |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_loss")
          |> mean()
          |> findRecord(fn: (key) => true, idx: 0)
      )._value
  }))
  |> filter(fn: (r) => r.spike_detected == true)

// Query: Accuracy Drop Detection
// Use: Alert when model accuracy degrades
accuracyDropDetection = from(bucket: "fl-metrics")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_train_accuracy")
  |> last()
  |> filter(fn: (r) => r._value < 0.5)
  |> yield(name: "accuracy_below_threshold")

// Query: Recall Drop Detection
// Use: Alert when recall degrades below threshold
recallDropDetection = from(bucket: "fl-metrics")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "fl_server_metrics" and r["_field"] == "aggregated_train_recall")
  |> last()
  |> filter(fn: (r) => r._value < 0.5)
  |> yield(name: "recall_below_threshold")