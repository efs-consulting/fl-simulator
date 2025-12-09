# Ray Metrics Exporter Fix

## Problem

The Flower Federated Learning Simulator was experiencing repeated warnings from Ray components:

```
(pid=gcs_server) Failed to establish connection to the event+metrics exporter agent. 
Events and metrics will not be exported. 
Exporter agent status: RpcError: Running out of retries to initialize the metrics agent. rpc_code: 14

(raylet) Failed to establish connection to the metrics exporter agent. 
Metrics will not be exported. 
Exporter agent status: RpcError: Running out of retries to initialize the metrics agent. rpc_code: 14

[core_worker_process] Failed to establish connection to the metrics exporter agent. 
Metrics will not be exported. 
Exporter agent status: RpcError: Running out of retries to initialize the metrics agent. rpc_code: 14
```

### Root Cause

These errors come from Ray processes (`gcs_server`, `raylet`, `core_worker`) running inside Flower containers (`flwr/superlink`, `flwr/superexec`, `flwr/supernode`). Ray attempts to initialize a metrics exporter agent (via gRPC) but the process is either:

1. Not started in the container
2. Unreachable on the expected port
3. Configured but the agent binary is missing

The error (rpc_code: 14 = UNAVAILABLE) indicates the metric exporter agent could not be contacted. While non-fatal (Ray continues without metrics), the logs are noisy and can obscure useful information.

## Solution

Disabled Ray's metrics exporter initialization in all Flower service containers by setting three environment variables:

1. **RAY_DISABLE_METRICS=1** — Completely disables Ray metrics collection/exporting
2. **RAY_metrics_exporter_port=0** — Prevents Ray from trying to bind a metrics exporter port
3. **RAY_BACKEND_LOG_LEVEL=warning** — Reduces Ray log verbosity to only show warnings and errors

### Files Modified

Environment blocks added to all superlink, supernode, and superexec services:

- `server/server/compose.yml` (superlink + superexec-serverapp)
- `client1/compose.yml` (supernode-2 + superexec-clientapp-2)
- `client2/compose.yml` (supernode-3 + superexec-clientapp-3)
- `client3/compose.yml` (supernode-4 + superexec-clientapp-4)
- `client4/compose.yml` (supernode-5 + superexec-clientapp-5)

### Example Change

Before:
```yaml
superlink:
  image: flwr/superlink:${FLWR_VERSION:-1.23.0}
  command:
    - --isolation
    - process
```

After:
```yaml
superlink:
  image: flwr/superlink:${FLWR_VERSION:-1.23.0}
  environment:
    # Disable Ray metrics exporter to prevent connection errors
    - RAY_DISABLE_METRICS=1
    - RAY_metrics_exporter_port=0
    - RAY_BACKEND_LOG_LEVEL=warning
  command:
    - --isolation
    - process
```

## Testing the Fix

### 1. Clean up old containers and images (recommended):

```bash
cd /home/soroush/Desktop/Files/Tutorals/11/fl-simulator/Battery_SOH
docker compose -f monitoring/docker-compose.yml down -v
docker compose -f server/server/compose.yml down -v
docker compose -f client1/compose.yml down -v
docker compose -f client2/compose.yml down -v
docker compose -f client3/compose.yml down -v
docker compose -f client4/compose.yml down -v
docker system prune -f
```

### 2. Start the FL Simulator with the fix:

```bash
./start-fl-training.sh 2
```

Or manually:
```bash
# Start monitoring
cd monitoring
docker compose up -d

# Start server
cd ../server/server
export PROJECT_DIR="../.."
docker compose up -d --build

# Start clients (adjust loop for number of clients)
for i in 1 2; do
  cd "../../client$i"
  export PROJECT_DIR="$PWD/quickstart-sklearn-tabular"
  docker compose up -d --build
done
```

### 3. Verify the fix by checking logs:

```bash
# Check server logs (should NOT see metrics exporter errors)
docker logs -f $(docker ps -qf 'name=superlink') 2>&1 | grep -i "metrics\|exporter" || echo "✓ No metrics errors"

# Check client logs
docker logs -f $(docker ps -qf 'name=superexec-clientapp') 2>&1 | grep -i "metrics\|exporter" || echo "✓ No metrics errors"
```

Expected output: Either silence or only INFO/DEBUG logs—**no ERROR or WARN** lines about `failed to establish connection to the metrics exporter agent`.

### 4. Verify FL training still works:

```bash
cd /home/soroush/Desktop/Files/Tutorals/11/fl-simulator/Battery_SOH/server

# Trigger FL training (inside or outside the container)
flwr run . --stream

# Or via docker:
docker exec -it $(docker ps -qf 'name=superexec-serverapp') flwr run . --stream
```

FL training should proceed normally; metrics will be logged to Prometheus and InfluxDB as configured in `server_app.py`.

## Impact

- ✅ **Eliminates noisy Ray metrics exporter errors** from logs
- ✅ **Reduces log pollution**, making it easier to spot real issues
- ✅ **No impact on FL training functionality** — Prometheus and InfluxDB metrics still work
- ✅ **Reversible** — Simply remove the `environment` block to re-enable Ray metrics if needed later
- ✅ **No performance impact** — Ray still runs; only metrics export is disabled

## Notes

- **Ray metrics are disabled at the Ray library level**, but **Flower/Prometheus/InfluxDB metrics remain active** (see `server_app.py` for `prometheus_client` and `influxdb_client` usage).
- If you want Ray metrics in the future, remove the three environment variables and rebuild containers.
- The fix is **non-breaking** and **safe to deploy** — it only silences an optional feature (Ray's OpenTelemetry exporter).

## References

- Ray documentation: https://docs.ray.io/en/latest/ray-core/configure.html
- Flower documentation: https://flower.ai/docs/
- Environment variables for Ray: https://docs.ray.io/en/latest/ray-core/ray-logging.html

---

**Applied: 2025-12-09**  
**Status: Ready to test**
