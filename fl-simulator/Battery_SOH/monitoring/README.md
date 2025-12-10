# FL Simulator Monitoring Stack

Real-time visualization and long-term storage for Federated Learning metrics using **InfluxDB** and **Grafana**.

> **Last Updated**: 2025-12-02
> **Status**: Fully operational with 5 working dashboards

## Quick Start

```bash
# Start the monitoring stack
cd fl-simulator/Battery_SOH/monitoring
docker compose up -d

# Check service health
docker compose ps

# View logs
docker compose logs -f
```

## Access URLs

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| **Grafana** | http://localhost:3005 | admin / flsimulator2025 |
| **InfluxDB** | http://localhost:8086 | admin / flsimulator2025 |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                FL SIMULATOR                                 │
│   Server + 4 Clients (Docker containers)                    │
│   Metrics pushed directly to InfluxDB                       │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP POST (line protocol)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   INFLUXDB 2.x                              │
│                   (Port 8086)                               │
│   • Time-series storage                                     │
│   • Flux query language                                     │
│   • Organization: flower                                    │
│   • Bucket: fl-metrics                                      │
└────────────────────┬────────────────────────────────────────┘
                     │ Flux queries
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   GRAFANA 10.2.0                            │
│                   (Port 3005)                               │
│   • 5 pre-configured dashboards                             │
│   • Real-time visualization                                 │
│   • 48-hour default time range                              │
└─────────────────────────────────────────────────────────────┘
```

## Dashboards

All dashboards use **InfluxDB Flux** queries and have a default time range of **48 hours**.

### 1. FL Global Training Progress

- **UID**: `fl-global-progress`
- **URL**: <http://localhost:3005/d/fl-global-progress>
- **Purpose**: Real-time overview of FL training
- **Panels**: Current round, aggregated R²/Loss gauges, convergence curves, training progress

### 2. FL Client Comparison

- **UID**: `fl-client-comparison`
- **URL**: <http://localhost:3005/d/fl-client-comparison>
- **Purpose**: Compare performance across all 4 clients
- **Panels**: Per-client Train R², Test R², Loss, CPU usage, Memory usage

### 3. FL Round Analysis

- **UID**: `fl-round-analysis`
- **URL**: <http://localhost:3005/d/fl-round-analysis>
- **Purpose**: Detailed round-by-round analysis
- **Panels**: Round overview stats, R² convergence table, Loss reduction, Client participation

### 4. FL Historical Analysis

- **UID**: `fl-historical-influxdb`
- **URL**: <http://localhost:3005/d/fl-historical-influxdb>
- **Purpose**: Long-term historical trends
- **Panels**: Central evaluation R², Loss over time, Server aggregated metrics

### 5. FL Experiment Comparison

- **UID**: `fl-experiment-comparison`
- **URL**: <http://localhost:3005/d/fl-experiment-comparison>
- **Purpose**: Compare experiments and analyze convergence
- **Panels**: Best R²/Loss metrics, Historical convergence, Client performance distribution

## InfluxDB Configuration

| Setting | Value |
|---------|-------|
| **Organization** | `flower` |
| **Bucket** | `fl-metrics` |
| **Token** | `fl-simulator-token-2025` |
| **Port** | 8086 |

### InfluxDB Buckets

| Bucket | Retention | Purpose |
|--------|-----------|---------|
| `fl-metrics` | 7 days | Primary metrics storage |
| `fl-metrics-hourly` | 90 days | Downsampled hourly aggregates |

### Measurements & Fields

| Measurement | Fields | Tags |
|-------------|--------|------|
| `fl_server_metrics` | `aggregated_train_r2`, `aggregated_test_r2`, `aggregated_loss` | `round`, `stage` |
| `fl_central_evaluation` | `r2`, `loss` | `round` |
| `fl_training_progress` | `round` | `stage` |
| `fl_client_metrics` | `train_r2`, `test_r2`, `loss`, `cpu_percent`, `memory_mb`, `cpu_time_sec` | `client_id`, `round`, `stage` |

## Troubleshooting

### No data in dashboards?

1. Check if FL training containers are running:

   ```bash
   docker ps | grep -E "(server|client)"
   ```

2. Query InfluxDB directly:

   ```bash
   curl -X POST "http://localhost:8086/api/v2/query?org=flower" \
     -H "Authorization: Token fl-simulator-token-2025" \
     -H "Content-Type: application/vnd.flux" \
     -d 'from(bucket: "fl-metrics") |> range(start: -1h) |> limit(n: 5)'
   ```

3. Check Grafana datasource:
   - Go to Grafana > Connections > Data sources > InfluxDB-FL
   - Click "Test" to verify connection

### Dashboard shows old data?

- Default time range is 48 hours
- Click on time picker (top right) and select appropriate range
- Use "Refresh" button or enable auto-refresh (10s/30s)

### Grafana container not starting?

```bash
docker compose logs grafana
docker compose restart grafana
```

## Files

```
monitoring/
├── docker-compose.yml              # Main stack configuration
├── README.md                       # This file
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── datasources.yml    # InfluxDB datasource config
│   │   └── dashboards/
│   │       └── dashboards.yml     # Dashboard provisioning
│   └── dashboards/
│       ├── fl-global-progress.json
│       ├── fl-client-comparison.json
│       ├── fl-round-analysis.json
│       ├── fl-historical-analysis.json
│       └── fl-experiment-comparison.json
└── influxdb/
    └── init-scripts/
        └── init-buckets.sh        # Bucket initialization
```

## Version Information

- InfluxDB: 2.7
- Grafana: 10.2.0
- Created: 2025-11-29
- Last Updated: 2025-12-02
