# FL Simulator

A Federated Learning simulation platform using the Flower framework with Docker-based deployment and real-time monitoring.

> **Last Updated**: 2025-12-02
> **Version**: 1.0.0

## Features

- **Docker-based FL Deployment**: Containerized server and clients for easy deployment
- **Real-time Monitoring**: InfluxDB + Grafana stack with 5 pre-configured dashboards
- **Battery SOH Use Case**: Complete implementation for Battery State of Health prediction
- **Scalable Architecture**: Support for 1-4+ federated clients
- **Automated Scripts**: One-command training start/stop

## Quick Start

```bash
# Clone and navigate to the project
cd fl-simulator/Battery_SOH

# Start federated learning with 4 clients
./start-fl-training.sh 4

# Access monitoring dashboards
open http://localhost:3005  # Grafana (admin/flsimulator2025)
```

## Project Structure

```
fl-simulator/
├── README.md                      # This file
├── fl-simulator/
│   └── Battery_SOH/              # Battery SOH FL implementation
│       ├── README.md             # Project documentation
│       ├── server/               # FL Server
│       ├── client1-4/            # FL Clients (4 instances)
│       ├── monitoring/           # Grafana + InfluxDB stack
│       ├── start-fl-training.sh  # Training launcher
│       └── stop-fl-training.sh   # Stop all containers
└── specs/                        # Specifications
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FL SIMULATOR                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│  │   Client 1  │     │   Client 2  │     │   Client 3  │   │
│  │  (Docker)   │     │  (Docker)   │     │  (Docker)   │   │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘   │
│         │                   │                   │           │
│         └───────────────────┼───────────────────┘           │
│                             │                               │
│                     ┌───────▼───────┐                       │
│                     │  FL Server    │                       │
│                     │  (Docker)     │                       │
│                     └───────┬───────┘                       │
│                             │                               │
│                     ┌───────▼───────┐                       │
│                     │   InfluxDB    │◄──── Metrics Push     │
│                     └───────┬───────┘                       │
│                             │                               │
│                     ┌───────▼───────┐                       │
│                     │   Grafana     │◄──── Visualization    │
│                     └───────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Monitoring Dashboards

| Dashboard | Description |
|-----------|-------------|
| **FL Global Training Progress** | Real-time training overview with R², loss, and round progress |
| **FL Client Comparison** | Compare performance metrics across all clients |
| **FL Round Analysis** | Detailed round-by-round convergence analysis |
| **FL Historical Analysis** | Long-term trends and historical data |
| **FL Experiment Comparison** | Compare different training experiments |

Access all dashboards at: <http://localhost:3005>

## Use Cases

### Battery SOH Prediction

Located in `fl-simulator/Battery_SOH/`:

- Federated learning for battery health prediction
- 4 clients with distributed battery data
- scikit-learn based model training
- R² and MSE loss tracking

See [Battery_SOH/README.md](fl-simulator/Battery_SOH/README.md) for details.

## Requirements

- Docker Engine 20.10+
- Docker Compose v2+
- Python 3.10+ (for local development)
- 4GB+ RAM recommended

## Configuration

### Server Settings

Edit `fl-simulator/Battery_SOH/server/pyproject.toml`:

```toml
[tool.flwr.app.config]
num-server-rounds = 10      # Number of FL rounds
fraction-fit = 1.0          # Fraction of clients for training
fraction-evaluate = 1.0     # Fraction of clients for evaluation
```

### Monitoring Settings

Edit `fl-simulator/Battery_SOH/monitoring/docker-compose.yml` for:

- Port mappings
- Resource limits
- Retention policies

## Ports Used

| Service | Port | Description |
|---------|------|-------------|
| Grafana | 3005 | Monitoring dashboards |
| InfluxDB | 8086 | Time-series database |
| FL SuperLink | 9092 | Flower server communication |

## Documentation

- [Battery SOH README](fl-simulator/Battery_SOH/README.md) - Main project documentation
- [Monitoring README](fl-simulator/Battery_SOH/monitoring/README.md) - Monitoring stack details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details.

## Changelog

### 2025-12-02

- Fixed all Grafana dashboards to use InfluxDB Flux queries
- Migrated from Prometheus to InfluxDB-only architecture
- Added 5 comprehensive monitoring dashboards
- Updated documentation across all READMEs

### 2025-11-29

- Initial project setup
- Docker-based FL deployment
- Basic monitoring with InfluxDB + Grafana
