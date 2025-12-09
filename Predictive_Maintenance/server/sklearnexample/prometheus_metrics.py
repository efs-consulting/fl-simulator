# prometheus_metrics.py
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import os
import threading

# Start Prometheus metrics server on port 8000 (you can change it)
def start_prometheus_server(port: int = 8000):
    if os.getenv("DISABLE_PROMETHEUS"):  # useful for local testing
        return
    # Start a separate thread so it doesn't block Flower
    def _run():
        start_http_server(port)
        print(f"Prometheus metrics available at http://localhost:{port}/metrics")
        # Keep thread alive forever
        import time
        while True:
            time.sleep(100)
    threading.Thread(target=_run, daemon=True).start()

# === Define your metrics once ===
# Client-side metrics
CLIENT_ROUND = Counter("fl_client_round_total", "Total training rounds completed", ["partition_id"])
CLIENT_TRAIN_R2 = Gauge("fl_client_train_r2", "Training R² on local data", ["partition_id"])
CLIENT_TEST_R2 = Gauge("fl_client_test_r2", "Test R² on local data", ["partition_id"])
CLIENT_LOSS = Gauge("fl_client_loss", "Local evaluation loss (MSE)", ["partition_id"])

# Server-side metrics
SERVER_ROUND = Gauge("fl_server_round", "Current federated round")
SERVER_AGG_TRAIN_R2 = Gauge("fl_server_aggregated_train_r2", "Weighted avg train R²")
SERVER_AGG_TEST_R2 = Gauge("fl_server_aggregated_test_r2", "Weighted avg test R²")
SERVER_AGG_LOSS = Gauge("fl_server_aggregated_loss", "Weighted avg test loss (MSE)")
SERVER_CONNECTED_CLIENTS = Gauge("fl_server_connected_clients", "Number of clients currently connected")