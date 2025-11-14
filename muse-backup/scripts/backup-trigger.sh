#!/bin/bash
# backup-trigger.sh
# Entry point - determines which backup(s) to run based on markers

set -euo pipefail

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$(dirname "$SCRIPT_DIR")/logs"
LOG_FILE="$LOG_DIR/backup-trigger.log"
DAILY_MARKER="/tmp/.muse-backup-daily-$(date +%Y%m%d)"
MONTHLY_MARKER="/tmp/.muse-backup-monthly-$(date +%Y-%m)"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# Check if daily backup needed
daily_needed=false
if [ ! -f "$DAILY_MARKER" ]; then
    daily_needed=true
    log "Daily backup needed (no marker for today)"
fi

# Check if monthly backup needed
monthly_needed=false
if [ ! -f "$MONTHLY_MARKER" ]; then
    monthly_needed=true
    log "Monthly backup needed (no marker for this month)"
fi

# If nothing to do, exit quietly
if [ "$daily_needed" = false ] && [ "$monthly_needed" = false ]; then
    exit 0
fi

# Run backups in background (non-blocking)
(
    if [ "$daily_needed" = true ]; then
        log "Starting daily backup..."
        if "$SCRIPT_DIR/backup-daily.sh"; then
            touch "$DAILY_MARKER"
            log "Daily backup completed successfully"
        else
            log "ERROR: Daily backup failed"
        fi
    fi

    if [ "$monthly_needed" = true ]; then
        log "Starting monthly backup..."
        if "$SCRIPT_DIR/backup-monthly.sh"; then
            touch "$MONTHLY_MARKER"
            log "Monthly backup completed successfully"
        else
            log "ERROR: Monthly backup failed"
        fi
    fi
) &

# Don't wait for background job - let terminal continue
log "Backup(s) started in background (PID: $!)"
