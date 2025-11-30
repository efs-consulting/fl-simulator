# FL Simulator Project State - 2025-11-30

## Current Status: FULLY OPERATIONAL

The FL Simulator is now fully functional with monitoring, server, and clients all working together.

## Architecture

```
Battery_SOH/
├── monitoring/               # InfluxDB + Prometheus + Grafana
│   ├── docker-compose.yml   # Port 3005 (Grafana), 9090 (Prometheus), 8086 (InfluxDB)
│   ├── prometheus.yml       # Prometheus config with container-based targets
│   └── grafana/             # Dashboards and alerting config
├── server/
│   ├── pyproject.toml       # FL config with superlink:9093 address
│   ├── sklearnexample/      # Server app module
│   ├── Data/                # Training data (data_type_0_section_7.mat)
│   └── server/
│       └── compose.yml      # SuperLink + ServerApp containers
├── client1/
│   ├── compose.yml          # SuperNode + ClientApp containers
│   └── quickstart-sklearn-tabular/
│       ├── pyproject.toml
│       ├── Data/            # Client training data
│       ├── Done/            # Processed data files
│       └── sklearnexample/  # Client app module
├── client2/                  # Same structure as client1
├── start-fl-training.sh     # Starts monitoring, server, clients
└── stop-fl-training.sh      # Stops FL components
```

## Services & Ports

| Service | Container | Port | Network |
|---------|-----------|------|---------|
| Grafana | fl-grafana | 3005 | fl-monitoring-network |
| Prometheus | fl-prometheus | 9090 | fl-monitoring-network |
| InfluxDB | fl-influxdb | 8086 | fl-monitoring-network |
| SuperLink | server-superlink-1 | 9091-9093 | fl-monitoring-network |
| Server App | server-superexec-serverapp-1 | 8001 | fl-monitoring-network |
| Client 1 Node | client1-supernode-2-1 | 9095 | fl-monitoring-network |
| Client 1 App | client1-superexec-clientapp-2-1 | 8002 | fl-monitoring-network |
| Client 2 Node | client2-supernode-3-1 | 9096 | fl-monitoring-network |
| Client 2 App | client2-superexec-clientapp-3-1 | 8003 | fl-monitoring-network |

## Credentials

- **Grafana**: admin / flsimulator2025
- **InfluxDB**: admin / flsimulator2025

## Key Configuration Details

### Docker Networks
All FL containers are connected to `fl-monitoring-network` (external) for Prometheus scraping:
```yaml
networks:
  - default
  - fl-monitoring-network
```

### Prometheus Configuration
Uses container names as targets (not host.docker.internal):
```yaml
- job_name: "flower-server"
  static_configs:
    - targets: ["server-superexec-serverapp-1:8001"]

- job_name: "flower-clients"
  static_configs:
    - targets: ["client1-superexec-clientapp-2-1:8002"]
    - targets: ["client2-superexec-clientapp-3-1:8003"]
```

### Prometheus Metrics (Available During Training)
- `fl_server_round` - Current FL round
- `fl_server_aggregated_train_r2` - Aggregated training R²
- `fl_server_aggregated_test_r2` - Aggregated test R²
- `fl_server_aggregated_loss` - Aggregated loss
- `fl_server_cetral_evaluation_R2` - Central evaluation R²
- `fl_client_train_r2{client_id}` - Per-client training R²
- `fl_client_test_r2{client_id}` - Per-client test R²

### Data File Management
- Each client has its own Data folder to avoid conflicts
- Files are moved to Done/ after processing (by task.py)
- Server data: `server/Data/data_type_0_section_7.mat`
- Client data: `clientN/quickstart-sklearn-tabular/Data/`

### Docker Compose Files
All compose files include:
```dockerfile
COPY --chown=app:app sklearnexample/ ./sklearnexample/
```
This copies the FL module into containers (required for `flwr run` to work).

### Server pyproject.toml
```toml
[tool.flwr.federations.remote-deployment]
address = "superlink:9093"  # Docker network address, not localhost
insecure = true
```

## Commands

### Start FL Training
```bash
cd Battery_SOH
./start-fl-training.sh 2  # Start with 2 clients
```

### Trigger Training Rounds
```bash
docker exec server-superexec-serverapp-1 flwr run . remote-deployment --stream
```

### Stop FL Training
```bash
./stop-fl-training.sh        # Keep monitoring running
./stop-fl-training.sh --all  # Stop everything
```

### View Logs
```bash
docker logs -f server-superexec-serverapp-1
docker logs -f client1-superexec-clientapp-2-1
```

### Check Prometheus Metrics (During Training)
```bash
docker exec fl-prometheus wget -q -O - http://server-superexec-serverapp-1:8001/metrics | grep "^fl_"
```

## Recent Training Results (2025-11-30)

Latest successful run:
- **Run ID**: 898551528189304045
- **Duration**: 109.87 seconds
- **Rounds**: 10
- **Best train R²**: 0.78 (round 7)
- **Final central R²**: -0.63 (improving from -11021)
- **Final Loss**: 0.000142

## Issues Fixed Today

1. **Port 3000 conflict** → Changed Grafana to port 3005
2. **Slack alerting error** → Removed Slack, kept email-only alerts
3. **Missing sklearnexample module** → Added COPY to Dockerfiles
4. **SuperLink connection failed** → Changed address to `superlink:9093`
5. **PROJECT_DIR not set** → Added exports in start-fl-training.sh
6. **Prometheus targets DOWN** → Connected all containers to fl-monitoring-network
7. **Prometheus wrong targets** → Changed from host.docker.internal to container names
8. **Client data conflicts** → Each client now has separate Data folder

## Prometheus/InfluxDB Monitoring Status

### What Works
- All containers connected to fl-monitoring-network
- Prometheus can reach FL metrics endpoint during training
- Metrics are exposed correctly (verified via wget from fl-prometheus)

### Current Limitation
- Prometheus metrics only available DURING training (~110 seconds)
- The metrics server runs inside the `flwr run` subprocess
- Prometheus marks targets as "down" between training runs

### Potential Solutions
1. Use Prometheus Pushgateway for push-based metrics
2. Run continuous training loops
3. Persist metrics to file and expose via separate sidecar

## Git Branch
`feature/influxdb-grafana-monitoring`

## Next Steps
- Implement Pushgateway for reliable metric collection
- Set up Grafana dashboards for FL training visualization
- Configure InfluxDB data retention policies
- Add more FL clients for larger-scale testing
