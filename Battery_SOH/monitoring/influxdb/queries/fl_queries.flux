// ============================================================
// FL Simulator - InfluxDB Flux Queries
// ============================================================
// Use these queries in InfluxDB Data Explorer or Grafana
// Bucket: fl-metrics
// Organization: flower
// ============================================================

// ============================================================
// 1. CENTRAL EVALUATION - Model Performance Over Rounds
// ============================================================

// 1a. Central Evaluation accuracy over time (shows model improvement)
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_central_evaluation")
  |> filter(fn: (r) => r._field == "accuracy")
  |> sort(columns: ["_time"])

// 1b. Central Evaluation Loss over time
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_central_evaluation")
  |> filter(fn: (r) => r._field == "loss")
  |> sort(columns: ["_time"])

// 1c. Central Evaluation Loss over time
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_central_evaluation")
  |> filter(fn: (r) => r._field == "recall")
  |> sort(columns: ["_time"])

// 1d. Central Evaluation - Both accuracy and Loss pivoted by round
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_central_evaluation")
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> sort(columns: ["_time"])


// ============================================================
// 2. TRAINING PROGRESS - Round Tracking
// ============================================================

// 2a. Training rounds over time
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_training_progress")
  |> filter(fn: (r) => r._field == "round")
  |> sort(columns: ["_time"])

// 2b. Count of rounds per training session (group by hour)
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_training_progress")
  |> filter(fn: (r) => r._field == "round")
  |> aggregateWindow(every: 1h, fn: count, createEmpty: false)


// ============================================================
// 3. CLIENT METRICS - Per-Client Performance
// ============================================================

// 3a. Client Training accuracy by client_id
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_client_metrics")
  |> filter(fn: (r) => r._field == "train_accuracy")
  |> group(columns: ["client_id"])
  |> sort(columns: ["_time"])

// 3b. Client Test accuracy by client_id
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_client_metrics")
  |> filter(fn: (r) => r._field == "test_accuracy")
  |> group(columns: ["client_id"])
  |> sort(columns: ["_time"])


// 3a. Client Training accuracy by client_id
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_client_metrics")
  |> filter(fn: (r) => r._field == "train_recall")
  |> group(columns: ["client_id"])
  |> sort(columns: ["_time"])

// 3b. Client Test accuracy by client_id
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_client_metrics")
  |> filter(fn: (r) => r._field == "test_recall")
  |> group(columns: ["client_id"])
  |> sort(columns: ["_time"])



// 3c. Client Loss by client_id
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_client_metrics")
  |> filter(fn: (r) => r._field == "loss")
  |> group(columns: ["client_id"])
  |> sort(columns: ["_time"])

// 3d. Client CPU Usage by client_id
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_client_metrics")
  |> filter(fn: (r) => r._field == "cpu_percent")
  |> group(columns: ["client_id"])
  |> sort(columns: ["_time"])

// 3e. Client Memory Usage by client_id
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_client_metrics")
  |> filter(fn: (r) => r._field == "memory_mb")
  |> group(columns: ["client_id"])
  |> sort(columns: ["_time"])

// 3f. All client metrics pivoted (wide format)
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_client_metrics")
  |> pivot(rowKey: ["_time", "client_id", "round", "stage"], columnKey: ["_field"], valueColumn: "_value")
  |> sort(columns: ["_time"])


// ============================================================
// 4. SERVER AGGREGATED METRICS
// ============================================================

// 4a. Aggregated Training accuracy over rounds
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_server_metrics")
  |> filter(fn: (r) => r._field == "aggregated_train_accuracy")
  |> sort(columns: ["_time"])

// 4b. Aggregated Test accuracy over rounds
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_server_metrics")
  |> filter(fn: (r) => r._field == "aggregated_test_ accuracy")
  |> sort(columns: ["_time"])


// 4c. Aggregated Training accuracy over rounds
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_server_metrics")
  |> filter(fn: (r) => r._field == "aggregated_train_recall")
  |> sort(columns: ["_time"])

// 4d. Aggregated Test accuracy over rounds
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_server_metrics")
  |> filter(fn: (r) => r._field == "aggregated_test_ recall")
  |> sort(columns: ["_time"])


// 4e. Aggregated Loss over rounds
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_server_metrics")
  |> filter(fn: (r) => r._field == "aggregated_loss")
  |> sort(columns: ["_time"])

// 4f. All server metrics by stage (fit vs evaluate)
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_server_metrics")
  |> pivot(rowKey: ["_time", "round", "stage"], columnKey: ["_field"], valueColumn: "_value")
  |> sort(columns: ["_time"])


// ============================================================
// 5. ANALYTICS QUERIES
// ============================================================

// 5a. Best accuracy achieved in last 24 hours
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_central_evaluation")
  |> filter(fn: (r) => r._field == "accuracy")
  |> max()
  

  // 5b. Best recall achieved in last 24 hours
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_central_evaluation")
  |> filter(fn: (r) => r._field == "recall")
  |> max()

// 5c. Lowest loss achieved in last 24 hours
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_central_evaluation")
  |> filter(fn: (r) => r._field == "loss")
  |> min()

// 5d. Average client CPU usage
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_client_metrics")
  |> filter(fn: (r) => r._field == "cpu_percent")
  |> mean()
  |> group(columns: ["client_id"])

// 5e. Training sessions count (distinct training runs)
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_training_progress")
  |> filter(fn: (r) => r._field == "round")
  |> filter(fn: (r) => r._value == 1.0)
  |> count()

// 5f.  improvement from first to last round (per session)
first_accuracy = from(bucket: "fl-metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "fl_central_evaluation")
  |> filter(fn: (r) => r._field == "accuracy")
  |> first()

last_accuracy = from(bucket: "fl-metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "fl_central_evaluation")
  |> filter(fn: (r) => r._field == "accuracy")
  |> last()


// 5g.  improvement from first to last round (per session)
first_recall = from(bucket: "fl-metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "fl_central_evaluation")
  |> filter(fn: (r) => r._field == "recall")
  |> first()

last_recall = from(bucket: "fl-metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "fl_central_evaluation")
  |> filter(fn: (r) => r._field == "recall")
  |> last()


// ============================================================
// 6. COMPARISON QUERIES
// ============================================================

// 6a. Compare client performance (side by side)
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_client_metrics")
  |> filter(fn: (r) => r._field == "train_accuracy")
  |> group(columns: ["client_id", "round"])
  |> last()
  |> group()
  |> pivot(rowKey: ["round"], columnKey: ["client_id"], valueColumn: "_value")

// 6b. Compare client performance (side by side)
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_client_metrics")
  |> filter(fn: (r) => r._field == "train_recall")
  |> group(columns: ["client_id", "round"])
  |> last()
  |> group()
  |> pivot(rowKey: ["round"], columnKey: ["client_id"], valueColumn: "_value")


// 6c. Fit vs Evaluate stage metrics
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_client_metrics")
  |> filter(fn: (r) => r.stage == "fit" or r.stage == "evaluate")
  |> group(columns: ["stage", "_field"])
  |> mean()


// ============================================================
// 7. TIME-BASED AGGREGATIONS
// ============================================================

// 7a. Hourly average accuracy (for long-term trend analysis)
from(bucket: "fl-metrics")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "fl_central_evaluation")
  |> filter(fn: (r) => r._field == "accuracy")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)

// 7b. Hourly average recall (for long-term trend analysis)
from(bucket: "fl-metrics")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "fl_central_evaluation")
  |> filter(fn: (r) => r._field == "recall")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)

// 7c. Training frequency per day
from(bucket: "fl-metrics")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "fl_training_progress")
  |> filter(fn: (r) => r._field == "round")
  |> filter(fn: (r) => r._value == 1.0)
  |> aggregateWindow(every: 1d, fn: count, createEmpty: false)


// ============================================================
// 8. FL ANALYTICS QUERIES
// ============================================================

// 8a. Latest round summary
from(bucket: "fl-metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "fl_round_analytics")
  |> filter(fn: (r) => r._field == "round_summary")
  |> last()

// 8b. Latest model status
from(bucket: "fl-metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "fl_round_analytics")
  |> filter(fn: (r) => r._field == "model_status")
  |> last()

// 8c. Latest convergence analysis
from(bucket: "fl-metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "fl_round_analytics")
  |> filter(fn: (r) => r._field == "convergence_analysis")
  |> last()

// 8d. Latest recommendations
from(bucket: "fl-metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "fl_round_analytics")
  |> filter(fn: (r) => r._field == "recommendations")
  |> last()

// 8e. Overall health status
from(bucket: "fl-metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "fl_round_analytics")
  |> filter(fn: (r) => r._field == "overall_health")
  |> last()

// 8f. All analytics for a round (pivoted)
from(bucket: "fl-metrics")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "fl_round_analytics")
  |> pivot(rowKey: ["_time", "round"], columnKey: ["_field"], valueColumn: "_value")
  |> sort(columns: ["_time"], desc: true)

// 8g. Client analytics
from(bucket: "fl-metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "fl_client_analytics")
  |> filter(fn: (r) => r._field == "analysis")
  |> group(columns: ["client_id", "round"])
  |> last()
  |> group()
  |> sort(columns: ["_time"], desc: true)
