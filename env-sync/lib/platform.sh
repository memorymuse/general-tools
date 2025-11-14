#!/usr/bin/env bash
#
# Platform Detection Library
# Cross-platform compatibility for cc-isolate
#

# Detect operating system
detect_os() {
    case "$(uname -s)" in
        Linux*)
            if grep -qi microsoft /proc/version 2>/dev/null; then
                echo "wsl"
            else
                echo "linux"
            fi
            ;;
        Darwin*)
            echo "macos"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            echo "windows"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# Cache the OS detection
OS_TYPE="${OS_TYPE:-$(detect_os)}"

# Platform check functions
is_linux() {
    [[ "$OS_TYPE" == "linux" ]]
}

is_wsl() {
    [[ "$OS_TYPE" == "wsl" ]]
}

is_macos() {
    [[ "$OS_TYPE" == "macos" ]]
}

is_windows() {
    [[ "$OS_TYPE" == "windows" ]]
}

# Get human-readable platform name
get_platform_name() {
    case "$OS_TYPE" in
        linux)
            echo "Linux"
            ;;
        wsl)
            echo "WSL (Windows Subsystem for Linux)"
            ;;
        macos)
            echo "macOS"
            ;;
        windows)
            echo "Windows"
            ;;
        *)
            echo "Unknown"
            ;;
    esac
}

# Get the system bashrc location based on platform
get_system_bashrc() {
    if is_macos; then
        # macOS doesn't have a default ~/.bashrc, but might have ~/.bash_profile
        if [[ -f "$HOME/.bash_profile" ]]; then
            echo "$HOME/.bash_profile"
        elif [[ -f "$HOME/.bashrc" ]]; then
            echo "$HOME/.bashrc"
        else
            echo "$HOME/.bashrc"  # Default even if it doesn't exist
        fi
    else
        # Linux/WSL typically use ~/.bashrc
        echo "$HOME/.bashrc"
    fi
}

# Get the system profile location
get_system_profile() {
    if is_macos; then
        echo "$HOME/.bash_profile"
    else
        echo "$HOME/.profile"
    fi
}

# Check if running in WSL and get Windows home directory
get_windows_home() {
    if is_wsl; then
        # Try to get Windows username from environment
        local win_user="${WIN_USER:-$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r')}"
        if [[ -n "$win_user" ]]; then
            echo "/mnt/c/Users/$win_user"
        fi
    fi
}

# Determine sed in-place syntax (BSD vs GNU)
sed_inplace() {
    if is_macos; then
        # macOS uses BSD sed which requires an extension for -i
        sed -i '' "$@"
    else
        # Linux uses GNU sed
        sed -i "$@"
    fi
}

# Cross-platform readlink for getting absolute paths
abs_path() {
    local path="$1"

    if command -v realpath >/dev/null 2>&1; then
        realpath "$path"
    elif command -v greadlink >/dev/null 2>&1; then
        # macOS with coreutils installed
        greadlink -f "$path"
    else
        # Fallback: use Python if available
        if command -v python3 >/dev/null 2>&1; then
            python3 -c "import os; print(os.path.abspath('$path'))"
        elif command -v python >/dev/null 2>&1; then
            python -c "import os; print(os.path.abspath('$path'))"
        else
            # Last resort: basic resolution
            echo "$(cd "$(dirname "$path")" && pwd)/$(basename "$path")"
        fi
    fi
}

# Get number of CPU cores (cross-platform)
get_cpu_count() {
    if is_macos; then
        sysctl -n hw.ncpu
    else
        nproc
    fi
}

# Cross-platform clipboard copy
copy_to_clipboard() {
    if is_macos; then
        pbcopy
    elif is_wsl; then
        clip.exe
    elif command -v xclip >/dev/null 2>&1; then
        xclip -selection clipboard
    elif command -v xsel >/dev/null 2>&1; then
        xsel --clipboard --input
    else
        # Fallback: just output to stdout
        cat
    fi
}

# Export functions
export -f detect_os
export -f is_linux
export -f is_wsl
export -f is_macos
export -f is_windows
export -f get_platform_name
export -f get_system_bashrc
export -f get_system_profile
export -f get_windows_home
export -f sed_inplace
export -f abs_path
export -f get_cpu_count
export -f copy_to_clipboard
