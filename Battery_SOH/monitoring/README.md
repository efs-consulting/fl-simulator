# FL Simulator Monitoring Stack

Real-time visualization and long-term storage for Federated Learning metrics using InfluxDB, Prometheus, and Grafana.

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
| **Grafana** | http://localhost:3002 | admin / flsimulator2025 |
| **Prometheus** | http://localhost:9090 | - |
| **InfluxDB** | http://localhost:8086 | admin / flsimulator2025 |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                FL SIMULATOR CLIENTS                         │
│         (Ports 8000, 8002, 8003, 8004)                     │
└────────────────────┬────────────────────────────────────────┘
                     │ Prometheus scrape (1s)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   PROMETHEUS                                │
│                   (Port 9090)                               │
│   • Real-time metrics collection                           │
│   • Alert rules evaluation                                  │
│   • 7-day local retention                                   │
└────────────────────┬────────────────────────────────────────┘
                     │ remote_write
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   INFLUXDB 2.x                              │
│                   (Port 8086)                               │
│   • Long-term time-series storage                          │
│   • Flux query language                                     │
│   • Multiple retention policies                             │
└────────────────────┬────────────────────────────────────────┘
                     │ Flux queries
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   GRAFANA                                   │
│                   (Port 3002)                               │
│   • Interactive dashboards                                  │
│   • Real-time visualization                                 │
│   • Alerting & notifications                                │
└─────────────────────────────────────────────────────────────┘
```

## Dashboards

### 1. FL Global Training Progress
- **UID**: `fl-global-progress`
- **Purpose**: Real-time overview of FL training
- **Panels**: Current round, aggregated R²/Loss gauges, convergence curves

### 2. FL Client Comparison
- **UID**: `fl-client-comparison`
- **Purpose**: Compare performance across all clients
- **Panels**: Per-client R², loss, CPU/memory usage, training time

### 3. FL Round Analysis
- **UID**: `fl-round-analysis`
- **Purpose**: Detailed round-by-round analysis
- **Panels**: Convergence rates, improvement metrics, client participation

## InfluxDB Buckets

| Bucket | Retention | Purpose |
|--------|-----------|---------|
| `fl-metrics` | 7 days | Raw high-frequency metrics |
| `fl-metrics-hourly` | 90 days | Downsampled hourly aggregates |
| `fl-metrics-archive` | 365 days | Long-term archive |
| `prometheus` | 7 days | Prometheus remote write data |

## Flux Queries

Pre-built Flux queries are available in `flux-queries/fl-queries.flux`:

- Convergence curve queries
- Per-client comparison
- Round-by-round analysis
- Anomaly detection
- Downsampling tasks

## Alert Rules

Configured alerts in `prometheus-alerts.yml`:

| Alert | Severity | Condition |
|-------|----------|-----------|
| FLTrainingLossSpike | warning | Loss increases >50% |
| FLR2Degradation | warning | R² drops below 0.5 |
| FLClientTimeout | warning | No metrics for 2 minutes |
| FLClientHighCPU | warning | CPU > 90% |
| FLNoProgress | warning | No new rounds for 5 minutes |

## Configuration

### Environment Variables

Create a `.env` file to customize:

```bash
# InfluxDB
INFLUXDB_PASSWORD=your-secure-password
INFLUXDB_TOKEN=your-api-token

# Grafana
GRAFANA_PASSWORD=your-grafana-password
```

### Connecting FL Simulator

Ensure your FL server and clients expose Prometheus metrics on the configured ports:

- Server: Port 8001
- Client 0: Port 8000
- Client 1: Port 8002
- Client 2: Port 8003
- Client 3: Port 8004

## Troubleshooting

### No data in dashboards?

1. Check if FL simulator is running:
   ```bash
   curl http://localhost:8001/metrics
   ```

2. Check Prometheus targets:
   - Visit http://localhost:9090/targets
   - All targets should show "UP"

3. Check InfluxDB connection:
   ```bash
   docker compose logs influxdb
   ```

### Grafana shows "No data"?

1. Verify datasource configuration in Grafana
2. Check time range selector (default: last 1 hour)
3. Ensure FL training has completed at least one round

### High memory usage?

Adjust retention policies in `prometheus.yml` and InfluxDB bucket settings.

## Development

### Adding new metrics

1. Add Prometheus Gauge/Counter in your FL code
2. Update `prometheus.yml` if new ports needed
3. Create Grafana panel for visualization
4. Add Flux query to `fl-queries.flux`

### Customizing dashboards

1. Edit dashboards in Grafana UI
2. Export JSON via Dashboard Settings > JSON Model
3. Save to `grafana/dashboards/` directory

## Files

```
monitoring/
├── docker-compose.yml              # Main stack configuration
├── prometheus.yml                  # Prometheus scrape config
├── prometheus-alerts.yml           # Alert rules
├── flux-queries/
│   └── fl-queries.flux            # Pre-built Flux queries
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── datasources.yml    # InfluxDB + Prometheus
│   │   └── dashboards/
│   │       └── dashboards.yml     # Dashboard provisioning
│   └── dashboards/
│       ├── fl-global-progress.json
│       ├── fl-client-comparison.json
│       └── fl-round-analysis.json
└── influxdb/
    └── init-scripts/
        └── init-buckets.sh        # Bucket initialization
```

## Version Information

- InfluxDB: 2.7
- Prometheus: 2.47.0
- Grafana: 10.2.0
- Created: 2025-11-29
