#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# TARGETED CALLING PIPELINE ORCHESTRATOR (FULLY CONTAINERIZED)
# ═══════════════════════════════════════════════════════════════════════════
# Usage:
#   ./pipeline.sh start    - Start with dataset preprocessing + training
#   ./pipeline.sh restart  - Restart without preprocessing (use existing data)
#   ./pipeline.sh stop     - Stop all components
#   ./pipeline.sh status   - Show current status
#   ./pipeline.sh logs     - Tail all container logs
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="docker/docker-compose-full.yml"
PROJECT_NAME="targeting"

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

print_header() {
    echo -e "${CYAN}"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo "   TARGETED CALLING PIPELINE - $1"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

print_step() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} ${GREEN}$1${NC}"
}

print_warning() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} ${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} ${RED}❌ $1${NC}"
}

print_success() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} ${GREEN}✓ $1${NC}"
}

wait_for_container() {
    local container=$1
    local max_attempts=60
    local attempt=1
    
    echo -n "   Waiting for $container..."
    while [ $attempt -le $max_attempts ]; do
        if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
            echo -e " ${GREEN}RUNNING${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    echo -e " ${RED}TIMEOUT${NC}"
    return 1
}

# ═══════════════════════════════════════════════════════════════════════════
# DOCKER COMMANDS
# ═══════════════════════════════════════════════════════════════════════════

build_images() {
    print_step "Building Docker images (cached)..."
    cd "$SCRIPT_DIR"
    docker-compose -p $PROJECT_NAME -f "$COMPOSE_FILE" build
    print_success "Docker images built"
}

build_images_fresh() {
    print_step "Building Docker images (no cache - fresh)..."
    cd "$SCRIPT_DIR"
    docker-compose -p $PROJECT_NAME -f "$COMPOSE_FILE" build --no-cache
    print_success "Docker images built"
}

start_infrastructure() {
    print_step "Starting infrastructure (Redis, NATS, Prometheus, Grafana)..."
    cd "$SCRIPT_DIR"
    
    docker-compose -p $PROJECT_NAME -f "$COMPOSE_FILE" up -d redis nats prometheus grafana
    
    # Wait for health checks
    sleep 5
    wait_for_container "targeting-redis"
    wait_for_container "targeting-nats"
    wait_for_container "targeting-prometheus"
    wait_for_container "targeting-grafana"
    
    print_success "Infrastructure started"
}

run_dataset_init() {
    print_step "Running dataset preprocessing..."
    cd "$SCRIPT_DIR"
    
    docker-compose -p $PROJECT_NAME -f "$COMPOSE_FILE" --profile init run --rm dataset-init
    
    if [ $? -eq 0 ]; then
        print_success "Dataset preprocessing complete"
    else
        print_warning "Dataset preprocessing had issues (may already exist)"
    fi
}

run_trainer() {
    print_step "Running initial model training..."
    cd "$SCRIPT_DIR"
    
    docker-compose -p $PROJECT_NAME -f "$COMPOSE_FILE" --profile init run --rm trainer
    
    if [ $? -eq 0 ]; then
        print_success "Model training complete"
    else
        print_error "Training failed!"
        exit 1
    fi
}

run_redis_loader() {
    print_step "Loading MASTERFILE to Redis..."
    cd "$SCRIPT_DIR"
    
    docker-compose -p $PROJECT_NAME -f "$COMPOSE_FILE" --profile init run --rm redis-loader
    
    if [ $? -eq 0 ]; then
        print_success "MASTERFILE loaded to Redis"
    else
        print_warning "Redis loading had issues (may already exist)"
    fi
}

start_pipeline_nodes() {
    print_step "Starting pipeline nodes..."
    cd "$SCRIPT_DIR"
    
    docker-compose -p $PROJECT_NAME -f "$COMPOSE_FILE" up -d \
        data-updater \
        car-predictor \
        car-feedback \
        oracle \
        lead-publisher \
        transaction-publisher \
        backend
    
    sleep 5
    wait_for_container "targeting-data-updater"
    wait_for_container "targeting-car-predictor"
    wait_for_container "targeting-car-feedback"
    wait_for_container "targeting-oracle"
    wait_for_container "targeting-backend"
    
    print_success "Pipeline nodes started"
}

stop_all() {
    print_step "Stopping all containers..."
    cd "$SCRIPT_DIR"
    docker-compose -p $PROJECT_NAME -f "$COMPOSE_FILE" --profile init down
    print_success "All containers stopped"
}

run_cleanup() {
    print_step "Cleaning up previous run data..."
    cd "$SCRIPT_DIR"
    
    # Clean logs
    rm -f ./carLoanFeedback/feedback_node.log 2>/dev/null || true
    rm -f ./carLoanPredictor/*.log 2>/dev/null || true
    rm -f ./oracle/*.log 2>/dev/null || true
    rm -f ./output.txt 2>/dev/null || true
    
    # Clean modelVisualiser outputs
    rm -rf ./modelVisualiser/gif_images 2>/dev/null || true
    rm -rf ./modelVisualiser/cluster_stats 2>/dev/null || true
    rm -rf ./modelVisualiser/weight_evolution 2>/dev/null || true
    rm -rf ./modelVisualiser/cluster_count_evolution 2>/dev/null || true
    
    print_success "Cleanup complete"
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN COMMANDS
# ═══════════════════════════════════════════════════════════════════════════

cmd_start() {
    print_header "STARTING (with preprocessing + training)"
    
    # 0. Build images (fresh, no cache)
    build_images_fresh
    
    # 1. Stop any existing containers
    stop_all 2>/dev/null || true
    
    # 2. Reset Prometheus data (for fresh metrics)
    print_step "Resetting Prometheus data..."
    docker volume rm targeting-calling_prometheus-data 2>/dev/null || true
    
    # 3. Run cleanup
    run_cleanup
    
    # 4. Start infrastructure
    start_infrastructure
    
    # 5. Run dataset preprocessing
    run_dataset_init
    
    # 6. Run model training
    run_trainer
    
    # 7. Load MASTERFILE to Redis
    run_redis_loader
    
    # 8. Start pipeline nodes
    start_pipeline_nodes
    
    echo ""
    print_header "PIPELINE STARTED"
    echo -e "${GREEN}All containers are running!${NC}"
    echo ""
    echo "Endpoints (Targeted-Calling):"
    echo "  • Grafana Dashboard: http://localhost:3001 (admin/admin)"
    echo "  • Prometheus:        http://localhost:9095"
    echo "  • Backend API:       http://localhost:5001"
    echo "  • Redis:             localhost:6380"
    echo "  • NATS:              localhost:4223"
    echo ""
    echo "Frontend (run separately):"
    echo "  cd Frontend && npm run dev  → http://localhost:5173"
    echo ""
    echo "To view logs: ./pipeline.sh logs"
    echo "To stop:      ./pipeline.sh stop"
}

cmd_restart() {
    print_header "RESTARTING (without preprocessing)"
    
    # 1. Stop ALL containers
    print_step "Stopping all containers..."
    cd "$SCRIPT_DIR"
    docker-compose -p $PROJECT_NAME -f "$COMPOSE_FILE" --profile init down 2>/dev/null || true
    
    # 2. Reset Prometheus data for fresh metrics
    print_step "Resetting Prometheus data..."
    docker volume rm targeting-calling_prometheus-data 2>/dev/null || true
    docker volume rm targeting-calling_grafana-data 2>/dev/null || true
    
    # 3. Rebuild images (with cache)
    build_images
    
    # 4. Start infrastructure
    start_infrastructure
    
    # 5. Run cleanup
    run_cleanup
    
    # 6. Check if trained model exists
    if [ ! -f "./Persistence/car_loan_gmm.pkl" ] && [ ! -f "./Persistence/gmm_model.pkl" ]; then
        print_warning "No trained model found - running training..."
        run_dataset_init
        run_trainer
    fi
    
    # 7. Always load MASTERFILE to Redis
    run_redis_loader
    
    # 8. Start pipeline nodes
    start_pipeline_nodes
    
    echo ""
    print_header "PIPELINE RESTARTED"
    echo -e "${GREEN}All containers are running!${NC}"
    echo ""
    echo "Endpoints (Targeted-Calling):"
    echo "  • Grafana Dashboard: http://localhost:3001 (admin/admin)"
    echo "  • Backend API:       http://localhost:5001"
    echo ""
    echo "To view logs: ./pipeline.sh logs"
    echo "To stop:      ./pipeline.sh stop"
}

cmd_stop() {
    print_header "STOPPING"
    stop_all
    
    print_step "Cleaning up state files..."
    rm -f ./output.txt 2>/dev/null || true
    print_success "State files cleaned"
    
    print_header "PIPELINE STOPPED"
    echo -e "${GREEN}All containers have been stopped.${NC}"
}

cmd_status() {
    print_header "STATUS"
    cd "$SCRIPT_DIR"
    
    echo -e "${YELLOW}Docker Containers:${NC}"
    docker-compose -p $PROJECT_NAME -f "$COMPOSE_FILE" ps
    
    echo ""
    echo -e "${YELLOW}Service Endpoints (Targeted-Calling):${NC}"
    echo "   Grafana:    http://localhost:3001 (admin/admin)"
    echo "   Prometheus: http://localhost:9095"
    echo "   Backend:    http://localhost:5000"
    echo "   NATS:       localhost:4223"
    echo "   Redis:      localhost:6380"
    echo ""
    echo -e "${YELLOW}Frontend:${NC}"
    echo "   cd Frontend && npm run dev  → http://localhost:5173"
}

cmd_logs() {
    cd "$SCRIPT_DIR"
    docker-compose -p $PROJECT_NAME -f "$COMPOSE_FILE" logs -f --tail=100
}

# ═══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

show_usage() {
    echo "Usage: $0 {start|restart|stop|status|logs}"
    echo ""
    echo "Commands:"
    echo "  start   - Full start (builds images, generates dataset, trains model)"
    echo "  restart - Quick restart (uses existing model, skips preprocessing)"
    echo "  stop    - Stop all containers"
    echo "  status  - Show container status"
    echo "  logs    - Tail all container logs"
    echo ""
}

case "${1:-}" in
    start)
        cmd_start
        ;;
    restart)
        cmd_restart
        ;;
    stop)
        cmd_stop
        ;;
    status)
        cmd_status
        ;;
    logs)
        cmd_logs
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
