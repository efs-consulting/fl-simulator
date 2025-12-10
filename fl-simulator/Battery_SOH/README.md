# Battery SOH Federated Learning

Federated Learning system for Battery State of Health (SOH) prediction using the Flower framework with Docker-based deployment.

> **Last Updated**: 2025-12-02
> **Status**: Fully operational with monitoring

## Overview

This project implements a federated learning system for predicting battery State of Health (SOH) using machine learning. The system consists of:

- **1 FL Server**: Coordinates training rounds and aggregates model updates
- **4 FL Clients**: Each trains on local battery data and sends updates to server
- **Monitoring Stack**: InfluxDB + Grafana for real-time metrics visualization

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Flower framework (`flwr`)

### Start Training

```bash
# Start FL training with 4 clients and 10 rounds
./start-fl-training.sh 4

# Or specify custom rounds
./start-fl-training.sh 4 20  # 4 clients, 20 rounds
```

### Stop Training

```bash
./stop-fl-training.sh
```

### Access Monitoring

- **Grafana**: <http://localhost:3005> (admin / flsimulator2025)
- **InfluxDB**: <http://localhost:8086> (admin / flsimulator2025)

## Project Structure

```
Battery_SOH/
├── server/                    # FL Server configuration
│   ├── pyproject.toml        # Flower project config
│   ├── docker-compose.yml    # Server container setup
│   └── server/               # Server application code
│       └── server_app.py
├── client1/                   # Client 1 (and client2-4)
│   ├── pyproject.toml
│   ├── docker-compose.yml
│   └── quickstart-sklearn-tabular/
│       ├── client_app.py     # Client training logic
│       └── Data/             # Local battery data
├── monitoring/               # Monitoring stack
│   ├── docker-compose.yml
│   ├── grafana/             # Grafana dashboards
│   └── README.md            # Monitoring documentation
├── start-fl-training.sh     # Training launcher script
└── stop-fl-training.sh      # Stop all containers
```

## Training Metrics

The system tracks the following metrics during training:

| Metric | Description |
|--------|-------------|
| `aggregated_train_r2` | R² score from aggregated training |
| `aggregated_test_r2` | R² score from aggregated testing |
| `aggregated_loss` | MSE loss from aggregated model |
| `r2` (central eval) | R² from central evaluation |
| `loss` (central eval) | Loss from central evaluation |
| `train_r2` (per client) | Individual client training R² |
| `cpu_percent` | Client CPU usage |
| `memory_mb` | Client memory usage |

## Grafana Dashboards

Five pre-configured dashboards are available:

1. **FL Global Training Progress** - Real-time training overview
2. **FL Client Comparison** - Compare all 4 clients
3. **FL Round Analysis** - Round-by-round metrics
4. **FL Historical Analysis** - Long-term trends
5. **FL Experiment Comparison** - Experiment analysis

See [monitoring/README.md](monitoring/README.md) for detailed dashboard information.

## Configuration

### Server Configuration

Edit `server/pyproject.toml`:

```toml
[tool.flwr.app.config]
num-server-rounds = 10
fraction-fit = 1.0
fraction-evaluate = 1.0
```

### Client Configuration

Each client's data is stored in:

```
client{N}/quickstart-sklearn-tabular/Data/
```

## Docker Containers

When running, the following containers are created:

| Container | Port | Purpose |
|-----------|------|---------|
| `server-superexec-*` | - | FL SuperExec server |
| `server-superlink-*` | 9092 | FL SuperLink |
| `client{N}-clientapp-*` | - | Client applications |
| `grafana` | 3005 | Visualization |
| `influxdb` | 8086 | Metrics storage |

## Troubleshooting

### Training not starting?

```bash
# Check container status
docker ps

# View server logs
docker logs server-superexec-serverapp-1

# View client logs
docker logs client1-clientapp-1
```

### No metrics in Grafana?

1. Ensure training is running (`docker ps`)
2. Check InfluxDB has data (see monitoring/README.md)
3. Verify time range is set to "Last 48 hours"

### Port conflicts?

```bash
# Check ports in use
lsof -i :3005
lsof -i :8086
lsof -i :9092
```

## Version Information

- Flower: Latest
- Python: 3.10+
- InfluxDB: 2.7
- Grafana: 10.2.0
- Docker Compose: v2

## License

See repository root for license information.
