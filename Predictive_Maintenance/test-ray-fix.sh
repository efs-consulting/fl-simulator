#!/bin/bash
# Test script for Ray metrics exporter fix
# This script rebuilds all FL containers and checks for Ray metrics errors

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "  FL Simulator - Ray Metrics Fix Tester"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_pass() { echo -e "${GREEN}✓${NC} $1"; }
log_fail() { echo -e "${RED}✗${NC} $1"; }
log_info() { echo -e "${YELLOW}ℹ${NC} $1"; }

# Step 1: Clean up old containers and images
log_info "Step 1: Cleaning up old containers and images..."
docker compose -f monitoring/docker-compose.yml down -v 2>/dev/null || true
docker compose -f server/server/compose.yml down -v 2>/dev/null || true
docker compose -f client1/compose.yml down -v 2>/dev/null || true
docker compose -f client2/compose.yml down -v 2>/dev/null || true
docker compose -f client3/compose.yml down -v 2>/dev/null || true
docker compose -f client4/compose.yml down -v 2>/dev/null || true
log_pass "Cleaned old containers"
echo ""

# Step 2: Start monitoring stack
log_info "Step 2: Starting monitoring stack..."
cd monitoring
docker compose up -d
sleep 5
log_pass "Monitoring stack started"
cd ..
echo ""

# Step 3: Start server
log_info "Step 3: Starting FL Server (SuperLink + ServerApp)..."
cd server/server
export PROJECT_DIR="../../"
docker compose up -d --build
sleep 10
log_pass "FL Server started (building may take 1-2 minutes...)"
cd ../..
echo ""

# Step 4: Start clients
log_info "Step 4: Starting FL Clients (1-2)..."
for i in 1 2; do
  client_dir="client$i"
  if [ -d "$client_dir" ]; then
    cd "$client_dir"
    export PROJECT_DIR="$PWD/quickstart-sklearn-tabular"
    docker compose up -d --build
    sleep 3
  fi
  cd ..
done
log_pass "FL Clients started (building may take 1-2 minutes...)"
echo ""

# Step 5: Wait for all services to stabilize
log_info "Step 5: Waiting for services to stabilize (30 seconds)..."
sleep 30
log_pass "Services should be ready"
echo ""

# Step 6: Check for Ray metrics exporter errors in all services
log_info "Step 6: Checking for Ray metrics exporter errors in all services..."
echo ""

ERROR_FOUND=0

# Check superlink
log_info "Checking superlink..."
if docker logs $(docker ps -qf 'name=superlink' 2>/dev/null) 2>&1 | grep -i "failed to establish connection to the metrics exporter agent" > /dev/null 2>&1; then
  log_fail "superlink: Found metrics exporter errors"
  ERROR_FOUND=1
else
  log_pass "superlink: No metrics exporter errors"
fi

# Check superexec-serverapp
log_info "Checking superexec-serverapp..."
if docker logs $(docker ps -qf 'name=superexec-serverapp' 2>/dev/null) 2>&1 | grep -i "failed to establish connection to the metrics exporter agent" > /dev/null 2>&1; then
  log_fail "superexec-serverapp: Found metrics exporter errors"
  ERROR_FOUND=1
else
  log_pass "superexec-serverapp: No metrics exporter errors"
fi

# Check all supernodes and superexec-clientapps
for i in 1 2; do
  client_dir="client$i"
  if [ -d "$client_dir" ]; then
    log_info "Checking client$i services..."
    
    # Supernode check
    SUPERNODE_NAME=$(docker ps --format '{{.Names}}' | grep -E "supernode-[0-9]" | head -1)
    if [ -n "$SUPERNODE_NAME" ]; then
      if docker logs "$SUPERNODE_NAME" 2>&1 | grep -i "failed to establish connection to the metrics exporter agent" > /dev/null 2>&1; then
        log_fail "$SUPERNODE_NAME: Found metrics exporter errors"
        ERROR_FOUND=1
      else
        log_pass "$SUPERNODE_NAME: No metrics exporter errors"
      fi
    fi
    
    # Superexec-clientapp check
    SUPEREXEC_NAME=$(docker ps --format '{{.Names}}' | grep -E "superexec-clientapp-[0-9]" | head -1)
    if [ -n "$SUPEREXEC_NAME" ]; then
      if docker logs "$SUPEREXEC_NAME" 2>&1 | grep -i "failed to establish connection to the metrics exporter agent" > /dev/null 2>&1; then
        log_fail "$SUPEREXEC_NAME: Found metrics exporter errors"
        ERROR_FOUND=1
      else
        log_pass "$SUPEREXEC_NAME: No metrics exporter errors"
      fi
    fi
  fi
done

echo ""
echo "=========================================="

if [ $ERROR_FOUND -eq 0 ]; then
  log_pass "TEST PASSED: No Ray metrics exporter errors found!"
  echo ""
  echo "Next steps:"
  echo "1. Start FL training: cd server && flwr run . --stream"
  echo "2. View live logs: docker logs -f <container-name>"
  echo "3. Access monitoring at http://localhost:3005 (Grafana)"
  exit 0
else
  log_fail "TEST FAILED: Ray metrics exporter errors still present"
  echo ""
  echo "Debugging tips:"
  echo "1. Check full container logs: docker logs <container-name>"
  echo "2. Inspect Ray process: docker exec -it <container-name> ps aux | grep ray"
  echo "3. Check Ray configuration: docker exec -it <container-name> env | grep RAY_"
  exit 1
fi
