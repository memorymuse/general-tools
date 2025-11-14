#!/bin/bash
# backup-daily.sh
# Executes daily backup of critical files from JSON configs

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_DIR="$BASE_DIR/configs"
LOG_DIR="$BASE_DIR/logs"
LOG_FILE="$LOG_DIR/backup-daily.log"
BACKUP_ROOT="/mnt/g/muse-backup"

# Generate timestamp and paths
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
YEAR_MONTH=$(date '+%Y-%m')
BACKUP_DIR="$BACKUP_ROOT/$YEAR_MONTH/daily-$TIMESTAMP"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "========== Daily Backup Started =========="
log "Backup directory: $BACKUP_DIR"

# Check if Windows drive mounted
if [ ! -d "$BACKUP_ROOT" ]; then
    log "ERROR: Backup root $BACKUP_ROOT not accessible (Windows drive not mounted?)"
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

# Process each config file
files_copied=0
dirs_copied=0
bytes_copied=0
start_time=$(date +%s)

process_config() {
    local config_file=$1
    local project_name=$2

    if [ ! -f "$config_file" ]; then
        log "ERROR: Config file not found: $config_file"
        return 1
    fi

    log "Processing config: $config_file ($project_name)"

    # Parse JSON and iterate over paths
    while IFS= read -r source_path; do
        # Skip if path doesn't exist
        if [ ! -e "$source_path" ]; then
            log "WARNING: Source not found, skipping: $source_path"
            continue
        fi

        # Determine relative path for backup destination
        if [[ "$source_path" == /home/kysonk/projects/* ]]; then
            rel_path="${source_path#/home/kysonk/projects/}"
            dest_path="$BACKUP_DIR/projects/$rel_path"
        elif [[ "$source_path" == /home/kysonk/* ]]; then
            rel_path="${source_path#/home/kysonk/}"
            dest_path="$BACKUP_DIR/home/$rel_path"
        else
            log "WARNING: Unexpected path format, skipping: $source_path"
            continue
        fi

        # Create parent directory
        mkdir -p "$(dirname "$dest_path")"

        # Copy file or directory
        if [ -d "$source_path" ]; then
            rsync -a \
                --exclude='__pycache__' \
                --exclude='*.pyc' \
                --exclude='midway-eval' \
                --exclude='agent_personas/midway-eval-system-reviewers' \
                "$source_path/" "$dest_path/" 2>&1 | tee -a "$LOG_FILE" || true
            log "Copied directory: $source_path"
            dirs_copied=$((dirs_copied + 1))
        else
            cp -p "$source_path" "$dest_path"
            log "Copied file: $source_path"
            files_copied=$((files_copied + 1))
        fi

    done < <(jq -r '.[]' < "$config_file")
}

# Process muse-v0 config
if [ -f "$CONFIG_DIR/muse-v0-daily.json" ]; then
    process_config "$CONFIG_DIR/muse-v0-daily.json" "muse-v0"
else
    log "WARNING: muse-v0-daily.json not found"
fi

# Process muse-v1 config
if [ -f "$CONFIG_DIR/muse-v1-daily.json" ]; then
    process_config "$CONFIG_DIR/muse-v1-daily.json" "muse-v1"
else
    log "WARNING: muse-v1-daily.json not found"
fi

# Calculate stats
end_time=$(date +%s)
duration=$((end_time - start_time))
backup_size=$(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1)

log "========== Daily Backup Completed =========="
log "Files copied: $files_copied"
log "Directories copied: $dirs_copied"
log "Backup size: $backup_size"
log "Duration: ${duration}s"
