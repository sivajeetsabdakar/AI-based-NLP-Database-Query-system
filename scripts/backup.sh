#!/bin/bash
# Production Backup Script for NLP Query Engine
# Comprehensive backup of all system components

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="nlp_query_engine_${DATE}"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
LOG_FILE="/var/log/backup.log"

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

# Create backup directory
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

log "Starting backup: ${BACKUP_NAME}"

# Function to backup PostgreSQL
backup_postgres() {
    log "Backing up PostgreSQL database..."
    
    if ! docker exec nlp-query-postgres-prod pg_dump -U postgres nlp_query_engine > "${BACKUP_DIR}/${BACKUP_NAME}/postgres.sql"; then
        error "PostgreSQL backup failed"
    fi
    
    # Get database size
    DB_SIZE=$(docker exec nlp-query-postgres-prod psql -U postgres -d nlp_query_engine -t -c "SELECT pg_size_pretty(pg_database_size('nlp_query_engine'));" | tr -d ' ')
    log "PostgreSQL backup completed. Database size: ${DB_SIZE}"
}

# Function to backup Redis
backup_redis() {
    log "Backing up Redis data..."
    
    if ! docker exec nlp-query-redis-prod redis-cli --rdb /data/dump.rdb; then
        error "Redis backup failed"
    fi
    
    if ! docker cp nlp-query-redis-prod:/data/dump.rdb "${BACKUP_DIR}/${BACKUP_NAME}/redis.rdb"; then
        error "Redis data copy failed"
    fi
    
    log "Redis backup completed"
}

# Function to backup ChromaDB
backup_chromadb() {
    log "Backing up ChromaDB data..."
    
    if ! docker exec nlp-query-chromadb-prod tar -czf /tmp/chromadb_backup.tar.gz -C /chroma/chroma .; then
        error "ChromaDB backup failed"
    fi
    
    if ! docker cp nlp-query-chromadb-prod:/tmp/chromadb_backup.tar.gz "${BACKUP_DIR}/${BACKUP_NAME}/chromadb.tar.gz"; then
        error "ChromaDB data copy failed"
    fi
    
    log "ChromaDB backup completed"
}

# Function to backup application data
backup_app_data() {
    log "Backing up application data..."
    
    # Backup logs
    if [ -d "/logs" ]; then
        tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/logs.tar.gz" -C /logs .
        log "Application logs backed up"
    fi
    
    # Backup configuration
    if [ -f "/app/config.py" ]; then
        cp /app/config.py "${BACKUP_DIR}/${BACKUP_NAME}/config.py"
        log "Application configuration backed up"
    fi
    
    # Backup environment variables (without secrets)
    env | grep -E '^(POSTGRES_|REDIS_|CHROMA_|MISTRAL_)' > "${BACKUP_DIR}/${BACKUP_NAME}/env_vars.txt"
    log "Environment variables backed up"
}

# Function to backup Docker volumes
backup_volumes() {
    log "Backing up Docker volumes..."
    
    # List of volumes to backup
    VOLUMES=("postgres_data" "redis_data" "chromadb_data")
    
    for volume in "${VOLUMES[@]}"; do
        log "Backing up volume: ${volume}"
        
        # Create a temporary container to access the volume
        docker run --rm -v "${volume}:/data" -v "${BACKUP_DIR}/${BACKUP_NAME}:/backup" alpine \
            tar -czf "/backup/${volume}.tar.gz" -C /data .
        
        if [ $? -eq 0 ]; then
            log "Volume ${volume} backed up successfully"
        else
            warning "Failed to backup volume ${volume}"
        fi
    done
}

# Function to create backup manifest
create_manifest() {
    log "Creating backup manifest..."
    
    cat > "${BACKUP_DIR}/${BACKUP_NAME}/manifest.txt" << EOF
NLP Query Engine Backup Manifest
================================
Backup Date: $(date)
Backup Name: ${BACKUP_NAME}
System Version: $(docker --version)
Docker Compose Version: $(docker-compose --version)

Components Backed Up:
- PostgreSQL Database
- Redis Cache
- ChromaDB Vector Database
- Application Data
- Docker Volumes
- Configuration Files

Backup Contents:
$(ls -la "${BACKUP_DIR}/${BACKUP_NAME}")

Total Size: $(du -sh "${BACKUP_DIR}/${BACKUP_NAME}" | cut -f1)
EOF

    log "Backup manifest created"
}

# Function to compress backup
compress_backup() {
    log "Compressing backup..."
    
    cd "${BACKUP_DIR}"
    tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
    
    if [ $? -eq 0 ]; then
        BACKUP_SIZE=$(du -sh "${BACKUP_NAME}.tar.gz" | cut -f1)
        log "Backup compressed successfully. Size: ${BACKUP_SIZE}"
        
        # Remove uncompressed directory
        rm -rf "${BACKUP_NAME}"
        log "Uncompressed backup directory removed"
    else
        error "Backup compression failed"
    fi
}

# Function to upload to S3 (if configured)
upload_to_s3() {
    if [ -n "${BACKUP_S3_BUCKET:-}" ] && [ -n "${BACKUP_S3_ACCESS_KEY:-}" ] && [ -n "${BACKUP_S3_SECRET_KEY:-}" ]; then
        log "Uploading backup to S3..."
        
        # Configure AWS CLI
        export AWS_ACCESS_KEY_ID="${BACKUP_S3_ACCESS_KEY}"
        export AWS_SECRET_ACCESS_KEY="${BACKUP_S3_SECRET_KEY}"
        export AWS_DEFAULT_REGION="${BACKUP_S3_REGION:-us-east-1}"
        
        if aws s3 cp "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" "s3://${BACKUP_S3_BUCKET}/backups/"; then
            log "Backup uploaded to S3 successfully"
        else
            warning "Failed to upload backup to S3"
        fi
    else
        log "S3 configuration not provided, skipping upload"
    fi
}

# Function to cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
    
    find "${BACKUP_DIR}" -name "nlp_query_engine_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete
    
    if [ $? -eq 0 ]; then
        log "Old backups cleaned up successfully"
    else
        warning "Failed to cleanup old backups"
    fi
}

# Function to verify backup integrity
verify_backup() {
    log "Verifying backup integrity..."
    
    # Check if backup file exists and is not empty
    if [ -f "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" ] && [ -s "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" ]; then
        log "Backup file exists and is not empty"
        
        # Test tar file integrity
        if tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" > /dev/null 2>&1; then
            log "Backup archive integrity verified"
        else
            error "Backup archive is corrupted"
        fi
    else
        error "Backup file not found or empty"
    fi
}

# Main backup process
main() {
    log "Starting NLP Query Engine backup process..."
    
    # Check if backup is enabled
    if [ "${BACKUP_ENABLED:-true}" != "true" ]; then
        log "Backup is disabled, exiting"
        exit 0
    fi
    
    # Perform backups
    backup_postgres
    backup_redis
    backup_chromadb
    backup_app_data
    backup_volumes
    
    # Create manifest
    create_manifest
    
    # Compress backup
    compress_backup
    
    # Verify backup
    verify_backup
    
    # Upload to S3
    upload_to_s3
    
    # Cleanup old backups
    cleanup_old_backups
    
    log "Backup process completed successfully"
    
    # Send notification (if configured)
    if [ -n "${BACKUP_ALERT_EMAIL:-}" ]; then
        echo "NLP Query Engine backup completed successfully at $(date)" | \
            mail -s "Backup Success - ${BACKUP_NAME}" "${BACKUP_ALERT_EMAIL}"
    fi
}

# Error handling
trap 'error "Backup process failed at line $LINENO"' ERR

# Run main function
main "$@"

