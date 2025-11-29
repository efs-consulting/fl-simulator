#!/bin/bash
# FL Simulator Training Launcher
# Starts monitoring stack, server, and clients in correct order
# Created: 2025-11-29

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() { echo -e "${GREEN}[FL]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

# Default settings
NUM_CLIENTS=${1:-2}
WAIT_TIME=10

print_banner() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║           FL SIMULATOR - TRAINING LAUNCHER               ║"
    echo "║                    Flower.ai v1.23.0                     ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
}

check_docker() {
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker first."
        exit 1
    fi
    log "Docker is running ✓"
}

start_monitoring() {
    log "Starting monitoring stack (Prometheus, InfluxDB, Grafana)..."
    cd "$SCRIPT_DIR/monitoring"
    docker compose up -d

    # Wait for services to be healthy
    log "Waiting for monitoring services to be healthy..."
    sleep 5

    if curl -s http://localhost:3005/api/health > /dev/null 2>&1; then
        log "Grafana is healthy ✓"
    else
        warn "Grafana may still be starting..."
    fi

    if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
        log "Prometheus is healthy ✓"
    else
        warn "Prometheus may still be starting..."
    fi

    if curl -s http://localhost:8086/health > /dev/null 2>&1; then
        log "InfluxDB is healthy ✓"
    else
        warn "InfluxDB may still be starting..."
    fi
}

start_server() {
    log "Starting FL Server (SuperLink + ServerApp)..."
    cd "$SCRIPT_DIR/server/server"
    docker compose up -d

    log "Waiting for SuperLink to initialize..."
    sleep $WAIT_TIME

    # Check if SuperLink is running
    if docker ps | grep -q "superlink"; then
        log "SuperLink is running ✓"
    else
        error "SuperLink failed to start. Check logs with: docker compose logs"
        exit 1
    fi
}

start_clients() {
    log "Starting $NUM_CLIENTS FL Clients..."

    for i in $(seq 1 $NUM_CLIENTS); do
        client_dir="$SCRIPT_DIR/client$i"
        if [ -d "$client_dir" ]; then
            log "Starting Client $i..."
            cd "$client_dir"
            docker compose up -d
            sleep 2
        else
            warn "Client$i directory not found, skipping..."
        fi
    done

    log "Waiting for clients to connect to SuperLink..."
    sleep $WAIT_TIME
}

show_status() {
    echo ""
    log "═══════════════════════════════════════════════════════════"
    log "                    SERVICES STATUS"
    log "═══════════════════════════════════════════════════════════"
    echo ""
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(fl-|superlink|supernode|superexec)"
    echo ""
}

show_urls() {
    echo ""
    info "═══════════════════════════════════════════════════════════"
    info "                    ACCESS URLS"
    info "═══════════════════════════════════════════════════════════"
    echo ""
    echo "  📊 Grafana:     http://localhost:3005  (admin/flsimulator2025)"
    echo "  📈 Prometheus:  http://localhost:9090"
    echo "  🗄️  InfluxDB:    http://localhost:8086  (admin/flsimulator2025)"
    echo ""
    echo "  🔗 SuperLink:   localhost:9091-9093"
    echo ""
}

show_next_steps() {
    echo ""
    info "═══════════════════════════════════════════════════════════"
    info "                    NEXT STEPS"
    info "═══════════════════════════════════════════════════════════"
    echo ""
    echo "  To trigger FL training rounds:"
    echo ""
    echo "    cd $SCRIPT_DIR/server"
    echo "    flwr run . --stream"
    echo ""
    echo "  Or via Docker:"
    echo ""
    echo "    docker exec -it \$(docker ps -qf 'name=superexec-serverapp') flwr run . --stream"
    echo ""
    echo "  To view logs:"
    echo ""
    echo "    docker compose -f server/server/compose.yml logs -f"
    echo "    docker compose -f client1/compose.yml logs -f"
    echo ""
    echo "  To stop everything:"
    echo ""
    echo "    $SCRIPT_DIR/stop-fl-training.sh"
    echo ""
}

# Main execution
print_banner
check_docker

case "${1:-start}" in
    start|[0-9]*)
        start_monitoring
        start_server
        start_clients
        show_status
        show_urls
        show_next_steps
        log "FL Simulator is ready! 🚀"
        ;;
    status)
        show_status
        show_urls
        ;;
    *)
        echo "Usage: $0 [start|status] [num_clients]"
        echo ""
        echo "  start [n]  - Start monitoring, server, and n clients (default: 2)"
        echo "  status     - Show current service status"
        echo ""
        exit 1
        ;;
esac
