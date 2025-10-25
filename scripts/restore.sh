#!/bin/bash
# Production Restore Script for NLP Query Engine
# Comprehensive restore of all system components from backup

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
RESTORE_DIR="/tmp/restore"
LOG_FILE="/var/log/restore.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Function to show usage
usage() {
    echo "Usage: $0 <backup_file> [options]"
    echo ""
    echo "Options:"
    echo "  --dry-run          Show what would be restored without actually restoring"
    echo "  --force            Force restore even if services are running"
    echo "  --components       Restore specific components (postgres,redis,chromadb,app)"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 nlp_query_engine_20240101_120000.tar.gz"
    echo "  $0 nlp_query_engine_20240101_120000.tar.gz --dry-run"
    echo "  $0 nlp_query_engine_20240101_120000.tar.gz --components postgres,redis"
    exit 1
}

# Function to check if services are running
check_services() {
    log "Checking if services are running..."
    
    SERVICES=("nlp-query-postgres-prod" "nlp-query-redis-prod" "nlp-query-chromadb-prod" "nlp-query-backend-prod")
    
    for service in "${SERVICES[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "^${service}$"; then
            if [ "${FORCE:-false}" != "true" ]; then
                error "Service ${service} is running. Use --force to override or stop services first."
            else
                warning "Service ${service} is running but --force specified, continuing..."
            fi
        fi
    done
}

# Function to stop services
stop_services() {
    log "Stopping services for restore..."
    
    docker-compose -f docker-compose.prod.yml stop backend frontend
    
    # Stop databases if they're running
    docker-compose -f docker-compose.prod.yml stop postgres redis chromadb || true
    
    log "Services stopped"
}

# Function to start services
start_services() {
    log "Starting services after restore..."
    
    # Start databases first
    docker-compose -f docker-compose.prod.yml up -d postgres redis chromadb
    
    # Wait for databases to be ready
    log "Waiting for databases to be ready..."
    sleep 30
    
    # Start application services
    docker-compose -f docker-compose.prod.yml up -d backend frontend
    
    log "Services started"
}

# Function to extract backup
extract_backup() {
    local backup_file="$1"
    
    log "Extracting backup: ${backup_file}"
    
    if [ ! -f "${BACKUP_DIR}/${backup_file}" ]; then
        error "Backup file not found: ${BACKUP_DIR}/${backup_file}"
    fi
    
    # Create restore directory
    mkdir -p "${RESTORE_DIR}"
    
    # Extract backup
    if ! tar -xzf "${BACKUP_DIR}/${backup_file}" -C "${RESTORE_DIR}"; then
        error "Failed to extract backup file"
    fi
    
    # Get backup name (without .tar.gz)
    BACKUP_NAME=$(basename "${backup_file}" .tar.gz)
    
    log "Backup extracted to: ${RESTORE_DIR}/${BACKUP_NAME}"
}

# Function to restore PostgreSQL
restore_postgres() {
    log "Restoring PostgreSQL database..."
    
    if [ ! -f "${RESTORE_DIR}/${BACKUP_NAME}/postgres.sql" ]; then
        warning "PostgreSQL backup file not found, skipping..."
        return
    fi
    
    # Wait for PostgreSQL to be ready
    log "Waiting for PostgreSQL to be ready..."
    until docker exec nlp-query-postgres-prod pg_isready -U postgres; do
        sleep 2
    done
    
    # Drop and recreate database
    docker exec nlp-query-postgres-prod psql -U postgres -c "DROP DATABASE IF EXISTS nlp_query_engine;"
    docker exec nlp-query-postgres-prod psql -U postgres -c "CREATE DATABASE nlp_query_engine;"
    
    # Restore database
    if ! docker exec -i nlp-query-postgres-prod psql -U postgres -d nlp_query_engine < "${RESTORE_DIR}/${BACKUP_NAME}/postgres.sql"; then
        error "PostgreSQL restore failed"
    fi
    
    log "PostgreSQL database restored successfully"
}

# Function to restore Redis
restore_redis() {
    log "Restoring Redis data..."
    
    if [ ! -f "${RESTORE_DIR}/${BACKUP_NAME}/redis.rdb" ]; then
        warning "Redis backup file not found, skipping..."
        return
    fi
    
    # Stop Redis
    docker-compose -f docker-compose.prod.yml stop redis
    
    # Copy RDB file
    docker cp "${RESTORE_DIR}/${BACKUP_NAME}/redis.rdb" nlp-query-redis-prod:/data/dump.rdb
    
    # Start Redis
    docker-compose -f docker-compose.prod.yml up -d redis
    
    log "Redis data restored successfully"
}

# Function to restore ChromaDB
restore_chromadb() {
    log "Restoring ChromaDB data..."
    
    if [ ! -f "${RESTORE_DIR}/${BACKUP_NAME}/chromadb.tar.gz" ]; then
        warning "ChromaDB backup file not found, skipping..."
        return
    fi
    
    # Stop ChromaDB
    docker-compose -f docker-compose.prod.yml stop chromadb
    
    # Extract ChromaDB data
    docker run --rm -v chromadb_data:/data -v "${RESTORE_DIR}/${BACKUP_NAME}:/backup" alpine \
        tar -xzf /backup/chromadb.tar.gz -C /data
    
    # Start ChromaDB
    docker-compose -f docker-compose.prod.yml up -d chromadb
    
    log "ChromaDB data restored successfully"
}

# Function to restore application data
restore_app_data() {
    log "Restoring application data..."
    
    # Restore logs
    if [ -f "${RESTORE_DIR}/${BACKUP_NAME}/logs.tar.gz" ]; then
        tar -xzf "${RESTORE_DIR}/${BACKUP_NAME}/logs.tar.gz" -C /logs
        log "Application logs restored"
    fi
    
    # Restore configuration
    if [ -f "${RESTORE_DIR}/${BACKUP_NAME}/config.py" ]; then
        cp "${RESTORE_DIR}/${BACKUP_NAME}/config.py" /app/config.py
        log "Application configuration restored"
    fi
    
    log "Application data restored successfully"
}

# Function to restore Docker volumes
restore_volumes() {
    log "Restoring Docker volumes..."
    
    # List of volumes to restore
    VOLUMES=("postgres_data" "redis_data" "chromadb_data")
    
    for volume in "${VOLUMES[@]}"; do
        if [ -f "${RESTORE_DIR}/${BACKUP_NAME}/${volume}.tar.gz" ]; then
            log "Restoring volume: ${volume}"
            
            # Create a temporary container to restore the volume
            docker run --rm -v "${volume}:/data" -v "${RESTORE_DIR}/${BACKUP_NAME}:/backup" alpine \
                tar -xzf "/backup/${volume}.tar.gz" -C /data
            
            if [ $? -eq 0 ]; then
                log "Volume ${volume} restored successfully"
            else
                warning "Failed to restore volume ${volume}"
            fi
        else
            warning "Volume backup file not found: ${volume}.tar.gz"
        fi
    done
}

# Function to verify restore
verify_restore() {
    log "Verifying restore..."
    
    # Check if services are running
    SERVICES=("nlp-query-postgres-prod" "nlp-query-redis-prod" "nlp-query-chromadb-prod")
    
    for service in "${SERVICES[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q "^${service}$"; then
            log "Service ${service} is running"
        else
            warning "Service ${service} is not running"
        fi
    done
    
    # Test database connection
    if docker exec nlp-query-postgres-prod psql -U postgres -d nlp_query_engine -c "SELECT 1;" > /dev/null 2>&1; then
        log "PostgreSQL connection verified"
    else
        warning "PostgreSQL connection failed"
    fi
    
    # Test Redis connection
    if docker exec nlp-query-redis-prod redis-cli ping > /dev/null 2>&1; then
        log "Redis connection verified"
    else
        warning "Redis connection failed"
    fi
    
    # Test ChromaDB connection
    if curl -f http://localhost:8001/api/v1/heartbeat > /dev/null 2>&1; then
        log "ChromaDB connection verified"
    else
        warning "ChromaDB connection failed"
    fi
    
    log "Restore verification completed"
}

# Function to cleanup restore directory
cleanup() {
    log "Cleaning up restore directory..."
    rm -rf "${RESTORE_DIR}"
    log "Cleanup completed"
}

# Main restore process
main() {
    local backup_file="$1"
    local components="${COMPONENTS:-postgres,redis,chromadb,app}"
    
    log "Starting NLP Query Engine restore process..."
    log "Backup file: ${backup_file}"
    log "Components: ${components}"
    
    # Check if dry run
    if [ "${DRY_RUN:-false}" = "true" ]; then
        log "DRY RUN MODE - No actual restore will be performed"
        log "Would restore from: ${BACKUP_DIR}/${backup_file}"
        log "Would restore components: ${components}"
        exit 0
    fi
    
    # Check services
    check_services
    
    # Extract backup
    extract_backup "${backup_file}"
    
    # Stop services
    stop_services
    
    # Restore components based on selection
    IFS=',' read -ra COMPONENT_ARRAY <<< "$components"
    for component in "${COMPONENT_ARRAY[@]}"; do
        case "$component" in
            "postgres")
                restore_postgres
                ;;
            "redis")
                restore_redis
                ;;
            "chromadb")
                restore_chromadb
                ;;
            "app")
                restore_app_data
                ;;
            "volumes")
                restore_volumes
                ;;
            *)
                warning "Unknown component: ${component}"
                ;;
        esac
    done
    
    # Start services
    start_services
    
    # Verify restore
    verify_restore
    
    # Cleanup
    cleanup
    
    log "Restore process completed successfully"
    
    # Send notification (if configured)
    if [ -n "${BACKUP_ALERT_EMAIL:-}" ]; then
        echo "NLP Query Engine restore completed successfully at $(date)" | \
            mail -s "Restore Success - ${backup_file}" "${BACKUP_ALERT_EMAIL}"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --components)
            COMPONENTS="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        -*)
            error "Unknown option: $1"
            ;;
        *)
            if [ -z "${BACKUP_FILE:-}" ]; then
                BACKUP_FILE="$1"
            else
                error "Multiple backup files specified"
            fi
            shift
            ;;
    esac
done

# Check if backup file is specified
if [ -z "${BACKUP_FILE:-}" ]; then
    error "Backup file not specified"
fi

# Error handling
trap 'error "Restore process failed at line $LINENO"' ERR

# Run main function
main "${BACKUP_FILE}"

