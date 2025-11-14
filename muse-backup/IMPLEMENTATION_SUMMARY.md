# Muse Backup System - Implementation Summary

**Implementation Date:** October 29, 2025  
**Status:** ✅ COMPLETE & OPERATIONAL

## System Overview

Automated two-tier backup system for Muse v0 and v1 projects, designed for WSL2 environments with sporadic work patterns.

### Backup Strategy

- **Daily Backups**: Critical files only (~120MB, 22s execution) with smart exclusions
- **Monthly Backups**: Full project snapshot with exclusions (~1.1GB, ~3min execution)
- **Destination**: `/mnt/g/muse-backup/YYYY-MM/`
- **Triggers**: `~/.bashrc` (first terminal of day) + `@reboot` cron (WSL restarts)

## Directory Structure

```
~/projects/general_tools/muse-backup/
├── configs/
│   ├── muse-v0-daily.json      # 24 critical paths for v0
│   ├── muse-v0-monthly.json    # 51 exclude patterns for v0
│   ├── muse-v1-daily.json      # 24 critical paths for v1
│   └── muse-v1-monthly.json    # 51 exclude patterns for v1
│
├── scripts/
│   ├── backup-trigger.sh       # Entry point, marker-based execution
│   ├── backup-daily.sh         # Copies critical files from JSON
│   ├── backup-monthly.sh       # Full rsync with exclusions
│   ├── validate-config.sh      # JSON validation utility
│   └── backup-health-check.sh  # Quick system health overview
│
└── logs/
    ├── backup-trigger.log
    ├── backup-daily.log
    └── backup-monthly.log
```

## Automated Triggers

### 1. Bashrc Integration (lines 168-178)
```bash
# Quick health check alias
alias backup-health='~/projects/general_tools/muse-backup/scripts/backup-health-check.sh'

# Automated backup trigger (runs in background, non-blocking)
if [ -f "$HOME/projects/general_tools/muse-backup/scripts/backup-trigger.sh" ]; then
    "$HOME/projects/general_tools/muse-backup/scripts/backup-trigger.sh" &
fi
```

### 2. Cron @reboot Entry
```
@reboot sleep 60 && /home/kysonk/projects/general_tools/muse-backup/scripts/backup-trigger.sh
```

## How It Works

### Idempotency via Markers

The system uses marker files in `/tmp/` to prevent duplicate backups:

- **Daily**: `/tmp/.muse-backup-daily-YYYYMMDD`
- **Monthly**: `/tmp/.muse-backup-monthly-YYYY-MM`

If markers exist, `backup-trigger.sh` exits silently (no terminal spam).

### Backup Execution Flow

1. **Terminal starts** → bashrc runs `backup-trigger.sh` in background
2. **Trigger checks markers** → Determines what's needed (daily/monthly/nothing)
3. **If needed** → Forks background process, runs backup(s), creates markers on success
4. **Terminal proceeds** → No blocking, backups happen invisibly

### Error Handling

- Missing source paths: Logged as warnings, script continues
- Missing config: Error logged, script exits with code 1
- Backup failures: No marker created (will retry next invocation)
- G: drive unmounted: Error logged, script exits

### Daily Backup Exclusions

To optimize daily backups, the following are automatically excluded:

- `__pycache__/` - Python cache directories
- `*.pyc` - Python bytecode files
- `docs/midway-eval/` - Interim evaluation documentation
- `docs/agent_personas/midway-eval-system-reviewers/` - Eval reviewer personas

**Impact**: Reduces daily backup from 647 → 255 files (61% reduction), 136M → 120M (12% smaller), 28s → 22s (21% faster).

These items are still included in monthly full backups via the monthly exclusion configs.

## Testing Results

### Validation Passed ✅

- All 4 JSON configs valid (24 items in daily, 51 patterns in monthly)
- 46/48 paths exist (2 missing paths documented, acceptable)
- All bash scripts syntax-valid
- Destination directory creation successful
- Bashrc integration non-breaking

### Execution Test Results ✅

**Daily Backup (2025-10-29 02:36:11 - Optimized)**
- Duration: 22s
- Size: 120M
- Files: 255 total (27 direct + 228 in directories)
- Directories: 19 copied
- Exclusions: `__pycache__`, `*.pyc`, `docs/midway-eval`, eval reviewers
- Status: ✅ Both databases verified (v0: 8.4M, v1: 8.7M)

**Monthly Backup (2025-10-29 02:08:49)**
- Duration: 192s (3min 12s)
- Size: 1.1G
- muse-v0: 1.04GB
- muse-v1: 61.47MB
- Status: ✅ Complete with exclusions applied

## Usage

### Quick Health Check

```bash
backup-health
```

Shows:
- Drive accessibility
- Today's backup status (daily/monthly)
- Most recent backup timestamps and sizes
- Database verification (both muse.db files present)
- File count trends (last 4 dailies)
- Monthly backup size trends
- Recent errors (last 24h)

### Manual Backup Execution

```bash
# Run daily backup
~/projects/general_tools/muse-backup/scripts/backup-daily.sh

# Run monthly backup
~/projects/general_tools/muse-backup/scripts/backup-monthly.sh

# Run trigger (checks markers, runs what's needed)
~/projects/general_tools/muse-backup/scripts/backup-trigger.sh
```

### Config Validation

```bash
~/projects/general_tools/muse-backup/scripts/validate-config.sh
```

### View Logs

```bash
tail -50 ~/projects/general_tools/muse-backup/logs/backup-daily.log
tail -50 ~/projects/general_tools/muse-backup/logs/backup-monthly.log
tail -50 ~/projects/general_tools/muse-backup/logs/backup-trigger.log
```

## Backup Locations

All backups stored at: `/mnt/g/muse-backup/YYYY-MM/`

**Naming conventions:**
- Daily: `daily-YYYYMMDD-HHMMSS/`
- Monthly: `full-YYYYMMDD-HHMMSS/`

**Directory structure inside backups:**
- Daily: `projects/muse-vX/` and `home/` (follows source paths)
- Monthly: `muse-vX/` (clean project roots)

## Configuration

### Adding Paths to Daily Backup

Edit the JSON config files:

```bash
vim ~/projects/general_tools/muse-backup/configs/muse-v0-daily.json
vim ~/projects/general_tools/muse-backup/configs/muse-v1-daily.json
```

Format: JSON array of absolute paths
```json
[
  "/home/kysonk/projects/muse-v0/some/critical/file.py",
  "/home/kysonk/projects/muse-v1/important/directory"
]
```

### Adding Exclusion Patterns

Edit the monthly exclusion configs:

```bash
vim ~/projects/general_tools/muse-backup/configs/muse-v0-monthly.json
vim ~/projects/general_tools/muse-backup/configs/muse-v1-monthly.json
```

Format: JSON array of rsync exclude patterns
```json
[
  "node_modules",
  "*.pyc",
  "__pycache__",
  ".git/objects"
]
```

After editing, validate:
```bash
~/projects/general_tools/muse-backup/scripts/validate-config.sh
```

## Maintenance

### Manual Retention Management

Currently no automated retention. Delete old backups manually:

```bash
# List all backups with sizes
du -sh /mnt/g/muse-backup/*/*/

# Remove old month
rm -rf /mnt/g/muse-backup/2025-09/
```

### Backups

The following files are backed up and can be restored:

- `~/.bashrc` → `~/.bashrc.backup-YYYYMMDD-HHMMSS`
- Crontab → `~/crontab.backup-YYYYMMDD-HHMMSS`

To restore original state:
```bash
# Restore bashrc
cp ~/.bashrc.backup-YYYYMMDD-HHMMSS ~/.bashrc

# Restore crontab
crontab ~/crontab.backup-YYYYMMDD-HHMMSS
```

## System Requirements

- **jq**: JSON parser (installed: jq-1.6)
- **rsync**: File synchronization (installed: 3.2.7)
- **bash**: Shell scripting (WSL Ubuntu default)
- **G: drive**: Windows mount at `/mnt/g/` (writable)

## Known Issues & Notes

1. **Missing Paths**: 2 paths in configs don't exist:
   - `/home/kysonk/projects/muse-v0/muse/backend/pagination_implemen.py`
   - `/home/kysonk/projects/muse-v1/streams/cc-optimizations/CLAUDE.md`
   
   These are skipped with warnings (non-fatal).

2. **First Run After WSL Restart**: The `@reboot` cron entry waits 60s before running to ensure filesystem is ready.

3. **Background Execution**: Backups run in background. Terminal startup is non-blocking (~0s delay).

4. **Marker Persistence**: Markers in `/tmp/` survive sleep/wake but are cleared on WSL restart (intentional - ensures @reboot cron can run).

## Implementation Statistics

- **Total Files Created**: 9 (4 configs + 5 scripts)
- **Total Lines of Code**: ~750 lines bash/JSON
- **Implementation Time**: ~2 hours (design + implementation + testing)
- **First Successful Backup**: October 29, 2025 02:08:19
- **System Status**: ✅ Operational

## Next Steps (Optional)

Future enhancements (not currently implemented):

1. **Automated Retention**: Script to auto-delete backups older than X days/months
2. **Compression**: Add `.tar.gz` compression for monthly backups
3. **Incremental Monthly**: Use rsync `--link-dest` for space-efficient monthly backups
4. **Email Notifications**: Send email on backup failures
5. **Backup Verification**: SHA256 checksum validation
6. **Restore Script**: Automated restore from backup timestamp

---

**Last Updated**: October 29, 2025  
**System Health**: ✅ All green
