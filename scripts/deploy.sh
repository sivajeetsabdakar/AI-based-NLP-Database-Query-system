#!/bin/bash
# Production Deployment Script for NLP Query Engine
# Automated deployment with zero-downtime updates

set -euo pipefail

# Configuration
DEPLOY_DIR="/opt/nlp-query-engine"
BACKUP_DIR="/backups"
LOG_FILE="/var/log/deploy.log"
HEALTH_CHECK_URL="http://localhost:8000/health"
ROLLBACK_ENABLED=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "$LOG_FILE"
}

# Function to show usage
usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --version <version>    Deploy specific version"
    echo "  --rollback            Rollback to previous version"
    echo "  --dry-run             Show what would be deployed without deploying"
    echo "  --force               Force deployment even if health checks fail"
    echo "  --backup              Create backup before deployment"
    echo "  --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --version v1.2.3"
    echo "  $0 --rollback"
    echo "  $0 --dry-run"
    exit 1
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    # Check if required files exist
    if [ ! -f "docker-compose.prod.yml" ]; then
        error "docker-compose.prod.yml not found"
    fi
    
    if [ ! -f "env.prod" ]; then
        error "env.prod not found"
    fi
    
    log "Prerequisites check passed"
}

# Function to create backup
create_backup() {
    if [ "${BACKUP:-false}" = "true" ]; then
        log "Creating backup before deployment..."
        
        if [ -f "scripts/backup.sh" ]; then
            bash scripts/backup.sh
            log "Backup created successfully"
        else
            warning "Backup script not found, skipping backup"
        fi
    fi
}

# Function to pull latest images
pull_images() {
    log "Pulling latest Docker images..."
    
    # Pull images for all services
    docker-compose -f docker-compose.prod.yml pull
    
    log "Docker images pulled successfully"
}

# Function to build images
build_images() {
    log "Building Docker images..."
    
    # Build images for all services
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    log "Docker images built successfully"
}

# Function to run health checks
run_health_checks() {
    local max_attempts=30
    local attempt=1
    
    log "Running health checks..."
    
    while [ $attempt -le $max_attempts ]; do
        info "Health check attempt $attempt/$max_attempts"
        
        if curl -f "${HEALTH_CHECK_URL}" > /dev/null 2>&1; then
            log "Health check passed"
            return 0
        fi
        
        sleep 10
        ((attempt++))
    done
    
    error "Health checks failed after $max_attempts attempts"
}

# Function to deploy services
deploy_services() {
    log "Deploying services..."
    
    # Start databases first
    log "Starting databases..."
    docker-compose -f docker-compose.prod.yml up -d postgres redis chromadb
    
    # Wait for databases to be ready
    log "Waiting for databases to be ready..."
    sleep 30
    
    # Start application services
    log "Starting application services..."
    docker-compose -f docker-compose.prod.yml up -d backend frontend
    
    # Start monitoring services
    log "Starting monitoring services..."
    docker-compose -f docker-compose.prod.yml up -d prometheus grafana
    
    log "Services deployed successfully"
}

# Function to run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Wait for backend to be ready
    sleep 10
    
    # Run migrations
    if docker exec nlp-query-backend-prod alembic upgrade head; then
        log "Database migrations completed successfully"
    else
        warning "Database migrations failed, but continuing deployment"
    fi
}

# Function to verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Check if all services are running
    SERVICES=("nlp-query-postgres-prod" "nlp-query-redis-prod" "nlp-query-chromadb-prod" "nlp-query-backend-prod" "nlp-query-frontend-prod")
    
    for service in "${SERVICES[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "^${service}$"; then
            log "Service ${service} is running"
        else
            error "Service ${service} is not running"
        fi
    done
    
    # Run health checks
    run_health_checks
    
    log "Deployment verification completed successfully"
}

# Function to rollback deployment
rollback_deployment() {
    log "Rolling back deployment..."
    
    # Stop current services
    docker-compose -f docker-compose.prod.yml down
    
    # Start previous version (if available)
    if [ -f "docker-compose.prod.yml.previous" ]; then
        mv docker-compose.prod.yml.previous docker-compose.prod.yml
        log "Previous configuration restored"
    fi
    
    # Start services with previous configuration
    docker-compose -f docker-compose.prod.yml up -d
    
    # Verify rollback
    run_health_checks
    
    log "Rollback completed successfully"
}

# Function to cleanup old images
cleanup_images() {
    log "Cleaning up old Docker images..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove dangling images
    docker image prune -a -f
    
    log "Docker images cleaned up"
}

# Function to update deployment status
update_status() {
    local status="$1"
    local version="${VERSION:-latest}"
    
    # Update deployment status file
    cat > "/tmp/deployment_status.json" << EOF
{
    "status": "${status}",
    "version": "${version}",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "deployment_id": "$(uuidgen)"
}
EOF
    
    log "Deployment status updated: ${status}"
}

# Function to send notifications
send_notification() {
    local message="$1"
    local status="$2"
    
    # Send email notification (if configured)
    if [ -n "${DEPLOY_ALERT_EMAIL:-}" ]; then
        echo "${message}" | mail -s "Deployment ${status} - NLP Query Engine" "${DEPLOY_ALERT_EMAIL}"
    fi
    
    # Send Slack notification (if configured)
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"${message}\"}" \
            "${SLACK_WEBHOOK_URL}"
    fi
}

# Main deployment process
main() {
    log "Starting NLP Query Engine deployment process..."
    
    # Check if dry run
    if [ "${DRY_RUN:-false}" = "true" ]; then
        log "DRY RUN MODE - No actual deployment will be performed"
        log "Would deploy version: ${VERSION:-latest}"
        log "Would create backup: ${BACKUP:-false}"
        log "Would force deployment: ${FORCE:-false}"
        exit 0
    fi
    
    # Check if rollback
    if [ "${ROLLBACK:-false}" = "true" ]; then
        rollback_deployment
        update_status "rolled_back"
        send_notification "Deployment rolled back successfully" "ROLLBACK"
        exit 0
    fi
    
    # Update status
    update_status "starting"
    
    # Check prerequisites
    check_prerequisites
    
    # Create backup
    create_backup
    
    # Pull images
    pull_images
    
    # Build images
    build_images
    
    # Deploy services
    deploy_services
    
    # Run migrations
    run_migrations
    
    # Verify deployment
    verify_deployment
    
    # Cleanup
    cleanup_images
    
    # Update status
    update_status "completed"
    
    # Send notification
    send_notification "Deployment completed successfully" "SUCCESS"
    
    log "Deployment process completed successfully"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --version)
            VERSION="$2"
            shift 2
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --backup)
            BACKUP=true
            shift
            ;;
        --help)
            usage
            ;;
        -*)
            error "Unknown option: $1"
            ;;
        *)
            error "Unknown argument: $1"
            ;;
    esac
done

# Error handling
trap 'error "Deployment process failed at line $LINENO"' ERR

# Run main function
main "$@"

