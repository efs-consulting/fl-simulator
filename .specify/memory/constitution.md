# FL-Simulator Constitution

## Core Principles

### I. Federated-First Architecture

All features must respect FL boundaries: clients remain isolated, only model parameters and metrics are shared. Never expose raw client data to the server. All client-server communication follows Flower.ai protocols (gRPC).

### II. Observable by Default

Every FL process must emit metrics to Prometheus. New features must include corresponding Gauges/Counters. Visualization components must consume metrics via standard Prometheus queries.

### III. Test-First (NON-NEGOTIABLE)

TDD mandatory: Tests written → User approved → Tests fail → Then implement. FL testing requires:

- Unit tests for local model operations
- Integration tests for client-server communication
- Simulation tests for full FL round validation

### IV. Container-Native

All components run in Docker containers with explicit resource limits. Compose files define service dependencies. New features must include compose configuration updates.

### V. Simplicity & YAGNI

Start with minimal visualization features. Add complexity only when validated by user needs. Prefer extending existing Prometheus metrics over creating new data pipelines.

## Technology Stack

**Core Framework**: Flower.ai v1.23.0+
**ML Backend**: Scikit-learn (SGDRegressor)
**Metrics Collection**: Prometheus (real-time scraping, alerting)
**Metrics Storage**: InfluxDB 2.x/3.0 (long-term time-series, Flux queries)
**Visualization**: Grafana (dashboards, ML-based anomaly detection)
**Containers**: Docker Compose v3.9
**Language**: Python 3.8+

## InfluxDB Schema Guidelines

- **Tags** (indexed): round, stage, client_tier, aggregation_method
- **Fields** (values): loss, r2, cpu_percent, memory_mb, client_id
- **Avoid**: High-cardinality tags (unique client_id as tag)
- **Retention**: raw=7d, hourly=90d, archive=1y+
- **Write Batching**: 5,000-10,000 lines, gzip compression enabled

## Development Workflow

1. **Spec First**: Use `/speckit.spec` to define feature requirements
2. **Plan**: Use `/speckit.plan` for technical design
3. **Tasks**: Use `/speckit.tasks` to break down implementation
4. **Implement**: Follow TDD with Red-Green-Refactor
5. **Review**: Verify constitution compliance

## Quality Gates

- All PRs must pass Prometheus metric validation
- Container builds must succeed with explicit healthchecks
- FL round simulation must complete without errors
- No client data may leak to visualization layer

## Governance

Constitution supersedes all other practices. Amendments require:

1. Documentation of proposed change
2. Impact analysis on existing FL processes
3. Migration plan for running deployments

**Version**: 1.0.0 | **Ratified**: 2025-11-28 | **Last Amended**: 2025-11-28
