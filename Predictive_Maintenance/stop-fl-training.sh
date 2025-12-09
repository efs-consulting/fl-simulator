#!/bin/bash
# FL Simulator Training Stopper
# Stops all FL components gracefully
# Created: 2025-11-29

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[FL]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

print_banner() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║           FL SIMULATOR - STOPPING SERVICES               ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
}

stop_clients() {
    log "Stopping FL Clients..."
    for client_dir in client client1 client2 client3 client4; do
        if [ -d "$SCRIPT_DIR/$client_dir" ] && [ -f "$SCRIPT_DIR/$client_dir/compose.yml" ]; then
            cd "$SCRIPT_DIR/$client_dir"
            docker compose down 2>/dev/null || true
            log "Stopped $client_dir"
        fi
    done
}

stop_server() {
    log "Stopping FL Server..."
    if [ -d "$SCRIPT_DIR/server/server" ]; then
        cd "$SCRIPT_DIR/server/server"
        docker compose down 2>/dev/null || true
        log "Stopped server"
    fi
}

stop_monitoring() {
    if [ "$1" == "--all" ]; then
        log "Stopping monitoring stack..."
        cd "$SCRIPT_DIR/monitoring"
        docker compose down 2>/dev/null || true
        log "Stopped monitoring"
    else
        warn "Keeping monitoring stack running. Use --all to stop everything."
    fi
}

show_status() {
    echo ""
    log "Remaining containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(fl-|superlink|supernode|superexec)" || echo "  No FL containers running"
    echo ""
}

# Main
print_banner

case "${1:-}" in
    --all)
        stop_clients
        stop_server
        stop_monitoring --all
        log "All FL services stopped ✓"
        ;;
    *)
        stop_clients
        stop_server
        stop_monitoring
        log "FL training stopped. Monitoring stack still running."
        echo ""
        echo "  Access Grafana: http://localhost:3005"
        echo "  To stop monitoring: $0 --all"
        ;;
esac

show_status
