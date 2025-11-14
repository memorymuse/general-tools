#!/bin/bash
# backup-health-check.sh
# Quick health check overview for backup system

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$BASE_DIR/logs"
BACKUP_ROOT="/mnt/g/muse-backup"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BOLD}========== Muse Backup Health Check ==========${NC}"
echo ""

# 1. Check if backup drive is accessible
echo -e "${BOLD}[1] Backup Drive Status${NC}"
if [ -d "$BACKUP_ROOT" ] && [ -w "$BACKUP_ROOT" ]; then
    echo -e "  ${GREEN}✓${NC} Drive accessible: $BACKUP_ROOT"
else
    echo -e "  ${RED}✗${NC} Drive NOT accessible: $BACKUP_ROOT"
    echo ""
    exit 1
fi
echo ""

# 2. Check today's backup status
echo -e "${BOLD}[2] Today's Backup Status${NC}"
DAILY_MARKER="/tmp/.muse-backup-daily-$(date +%Y%m%d)"
MONTHLY_MARKER="/tmp/.muse-backup-monthly-$(date +%Y-%m)"

if [ -f "$DAILY_MARKER" ]; then
    echo -e "  ${GREEN}✓${NC} Daily backup completed today"
else
    echo -e "  ${YELLOW}⚠${NC} Daily backup not yet run today"
fi

if [ -f "$MONTHLY_MARKER" ]; then
    echo -e "  ${GREEN}✓${NC} Monthly backup completed this month"
else
    echo -e "  ${YELLOW}⚠${NC} Monthly backup not yet run this month"
fi
echo ""

# 3. Most recent backups
echo -e "${BOLD}[3] Most Recent Backups${NC}"

# Find most recent daily backup
RECENT_DAILY=$(find "$BACKUP_ROOT" -maxdepth 2 -type d -name "daily-*" 2>/dev/null | sort -r | head -1)
if [ -n "$RECENT_DAILY" ]; then
    DAILY_AGE=$(stat -c %Y "$RECENT_DAILY" 2>/dev/null || echo "0")
    DAILY_AGE_HUMAN=$(date -d "@$DAILY_AGE" '+%Y-%m-%d %H:%M' 2>/dev/null || echo "unknown")
    DAILY_SIZE=$(du -sh "$RECENT_DAILY" 2>/dev/null | cut -f1)
    echo -e "  ${BLUE}Daily:${NC} $DAILY_AGE_HUMAN ($DAILY_SIZE)"
else
    echo -e "  ${RED}Daily:${NC} No backups found"
fi

# Find most recent monthly backup
RECENT_MONTHLY=$(find "$BACKUP_ROOT" -maxdepth 2 -type d -name "full-*" 2>/dev/null | sort -r | head -1)
if [ -n "$RECENT_MONTHLY" ]; then
    MONTHLY_AGE=$(stat -c %Y "$RECENT_MONTHLY" 2>/dev/null || echo "0")
    MONTHLY_AGE_HUMAN=$(date -d "@$MONTHLY_AGE" '+%Y-%m-%d %H:%M' 2>/dev/null || echo "unknown")
    MONTHLY_SIZE=$(du -sh "$RECENT_MONTHLY" 2>/dev/null | cut -f1)
    echo -e "  ${BLUE}Monthly:${NC} $MONTHLY_AGE_HUMAN ($MONTHLY_SIZE)"
else
    echo -e "  ${RED}Monthly:${NC} No backups found"
fi
echo ""

# 4. Database verification (most recent daily)
echo -e "${BOLD}[4] Database Verification (Most Recent Daily)${NC}"
if [ -n "$RECENT_DAILY" ]; then
    # Check muse-v0 database
    V0_DB=$(find "$RECENT_DAILY" -path "*/muse-v0/muse/backend/muse.db" 2>/dev/null)
    if [ -n "$V0_DB" ]; then
        V0_DB_SIZE=$(du -h "$V0_DB" 2>/dev/null | cut -f1)
        echo -e "  ${GREEN}✓${NC} muse-v0/muse.db found ($V0_DB_SIZE)"
    else
        echo -e "  ${RED}✗${NC} muse-v0/muse.db NOT found"
    fi

    # Check muse-v1 database
    V1_DB=$(find "$RECENT_DAILY" -path "*/muse-v1/muse/backend/db/muse.db" 2>/dev/null)
    if [ -n "$V1_DB" ]; then
        V1_DB_SIZE=$(du -h "$V1_DB" 2>/dev/null | cut -f1)
        echo -e "  ${GREEN}✓${NC} muse-v1/muse.db found ($V1_DB_SIZE)"
    else
        echo -e "  ${RED}✗${NC} muse-v1/muse.db NOT found"
    fi
else
    echo -e "  ${YELLOW}⚠${NC} No daily backups to check"
fi
echo ""

# 5. File count trends (last 4 daily backups)
echo -e "${BOLD}[5] File Count Trends (Last 4 Daily Backups)${NC}"
RECENT_DAILIES=$(find "$BACKUP_ROOT" -maxdepth 2 -type d -name "daily-*" 2>/dev/null | sort -r | head -4)
if [ -n "$RECENT_DAILIES" ]; then
    echo -e "  ${BLUE}muse-v0:${NC}"
    for backup_dir in $RECENT_DAILIES; do
        backup_name=$(basename "$backup_dir")
        v0_count=$(find "$backup_dir/projects/muse-v0" -type f 2>/dev/null | wc -l)
        echo -e "    $backup_name: $v0_count files"
    done
    echo ""

    echo -e "  ${BLUE}muse-v1:${NC}"
    for backup_dir in $RECENT_DAILIES; do
        backup_name=$(basename "$backup_dir")
        v1_count=$(find "$backup_dir/projects/muse-v1" -type f 2>/dev/null | wc -l)
        echo -e "    $backup_name: $v1_count files"
    done
else
    echo -e "  ${YELLOW}⚠${NC} No daily backups to analyze"
fi
echo ""

# 6. Backup size trends (last 4 monthly backups)
echo -e "${BOLD}[6] Monthly Backup Size Trends${NC}"
RECENT_MONTHLIES=$(find "$BACKUP_ROOT" -maxdepth 2 -type d -name "full-*" 2>/dev/null | sort -r | head -4)
if [ -n "$RECENT_MONTHLIES" ]; then
    for backup_dir in $RECENT_MONTHLIES; do
        backup_name=$(basename "$backup_dir")
        backup_size=$(du -sh "$backup_dir" 2>/dev/null | cut -f1)
        echo -e "  $backup_name: $backup_size"
    done
else
    echo -e "  ${YELLOW}⚠${NC} No monthly backups to analyze"
fi
echo ""

# 7. Recent errors in logs
echo -e "${BOLD}[7] Recent Errors (Last 24h)${NC}"
ERROR_COUNT=0

for log_file in "$LOG_DIR"/*.log; do
    if [ -f "$log_file" ]; then
        recent_errors=$(grep -i "error\|failed" "$log_file" 2>/dev/null | tail -3)
        if [ -n "$recent_errors" ]; then
            echo -e "  ${RED}Errors in $(basename "$log_file"):${NC}"
            echo "$recent_errors" | sed 's/^/    /'
            ERROR_COUNT=$((ERROR_COUNT + 1))
        fi
    fi
done

if [ $ERROR_COUNT -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} No recent errors found"
fi
echo ""

# 8. Summary
echo -e "${BOLD}========== Summary ==========${NC}"
if [ -f "$DAILY_MARKER" ] && [ -n "$V0_DB" ] && [ -n "$V1_DB" ] && [ $ERROR_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ Backup system healthy${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ Review warnings above${NC}"
    exit 0
fi
