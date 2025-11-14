#!/bin/bash
# backup-monthly.sh
# Executes monthly full backup with exclusions from JSON configs

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$BASE_DIR/configs"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/backup-monthly.log"
BACKUP_ROOT="/mnt/g/muse-backup"

# Source directories
MUSE_V0="/home/kysonk/projects/muse-v0"
MUSE_V1="/home/kysonk/projects/muse-v1"

# Generate timestamp and paths
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
YEAR_MONTH=$(date '+%Y-%m')
BACKUP_DIR="$BACKUP_ROOT/$YEAR_MONTH/full-$TIMESTAMP"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "========== Monthly Full Backup Started =========="
log "Backup directory: $BACKUP_DIR"

# Check if Windows drive mounted
if [ ! -d "$BACKUP_ROOT" ]; then
    log "ERROR: Backup root $BACKUP_ROOT not accessible"
    exit 1
fi

# Create directory structure
mkdir -p "$BACKUP_DIR"
log "Created backup directory"

# Check jq is available
if ! command -v jq >/dev/null 2>&1; then
    log "ERROR: jq is not installed (required for JSON parsing)"
    exit 1
fi

start_time=$(date +%s)

# Function to build rsync exclude arguments from JSON config
build_exclude_args() {
    local config_file=$1
    local exclude_args=()

    if [ ! -f "$config_file" ]; then
        log "WARNING: Excludes config not found: $config_file"
        echo ""
        return
    fi

    while IFS= read -r pattern; do
        exclude_args+=("--exclude=$pattern")
    done < <(jq -r '.[]' < "$config_file")

    log "Loaded ${#exclude_args[@]} exclude patterns from $config_file"
    printf '%s\n' "${exclude_args[@]}"
}

# Backup muse-v0
if [ -d "$MUSE_V0" ]; then
    log "Backing up muse-v0..."

    # Build exclude args
    readarray -t EXCLUDE_ARGS_V0 < <(build_exclude_args "$CONFIG_DIR/muse-v0-monthly.json")

    # Run rsync
    rsync -avh --progress \
        "${EXCLUDE_ARGS_V0[@]}" \
        "$MUSE_V0/" \
        "$BACKUP_DIR/muse-v0/" \
        2>&1 | grep -E '(sent|total size|speedup)' | tee -a "$LOG_FILE" || true

    log "muse-v0 backup completed"
else
    log "WARNING: muse-v0 directory not found: $MUSE_V0"
fi

# Backup muse-v1
if [ -d "$MUSE_V1" ]; then
    log "Backing up muse-v1..."

    # Build exclude args
    readarray -t EXCLUDE_ARGS_V1 < <(build_exclude_args "$CONFIG_DIR/muse-v1-monthly.json")

    # Run rsync
    rsync -avh --progress \
        "${EXCLUDE_ARGS_V1[@]}" \
        "$MUSE_V1/" \
        "$BACKUP_DIR/muse-v1/" \
        2>&1 | grep -E '(sent|total size|speedup)' | tee -a "$LOG_FILE" || true

    log "muse-v1 backup completed"
else
    log "WARNING: muse-v1 directory not found: $MUSE_V1"
fi

# Calculate stats
end_time=$(date +%s)
duration=$((end_time - start_time))
backup_size=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)

log "========== Monthly Full Backup Completed =========="
log "Backup size: $backup_size"
log "Duration: ${duration}s"
