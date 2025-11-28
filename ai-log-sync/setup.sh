#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== ai-log-sync Setup ===${NC}"

# 1. Create Directory Structure
BASE_DIR="$HOME/ai-log-sync"
echo -e "\n${YELLOW}[1/4] Setting up directories in $BASE_DIR...${NC}"

mkdir -p "$BASE_DIR/inbox/raw/claude"
mkdir -p "$BASE_DIR/inbox/raw/openai"
mkdir -p "$BASE_DIR/staging/raw"
mkdir -p "$BASE_DIR/staging/logs"

echo -e "${GREEN}✓ Directories created:${NC}"
echo "  - $BASE_DIR/inbox (Place your exports here)"
echo "  - $BASE_DIR/staging (Processed logs)"

# 2. Check/Install Rclone
echo -e "\n${YELLOW}[2/4] Checking rclone...${NC}"
if ! command -v rclone &> /dev/null; then
    echo "rclone not found. Installing..."
    # Check OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install rclone
        else
            echo "Error: Homebrew not found. Please install rclone manually: https://rclone.org/install/"
            exit 1
        fi
    else
        # Linux/WSL
        curl https://rclone.org/install.sh | sudo bash
    fi
else
    echo -e "${GREEN}✓ rclone is installed${NC}"
fi

# 3. Configure Rclone Remote
REMOTE_NAME="gdrive"
echo -e "\n${YELLOW}[3/4] Configuring Google Drive remote...${NC}"

if rclone listremotes | grep -q "^$REMOTE_NAME:"; then
    echo -e "${GREEN}✓ Remote '$REMOTE_NAME' already exists${NC}"
else
    echo "Creating new remote '$REMOTE_NAME'..."
    echo "You will need to authorize rclone with your Google account."
    echo "Press Enter to start configuration (select 'n' for New Remote, name it 'gdrive', select 'drive')..."
    read -r
    rclone config
fi

# 4. Install Package
echo -e "\n${YELLOW}[4/4] Installing ai-log-sync...${NC}"
# Assuming we are in the project root
if [ -f "setup.py" ]; then
    pip install -e .
    echo -e "${GREEN}✓ Installed in editable mode${NC}"
else
    echo "Warning: setup.py not found. Skipping pip install."
fi

echo -e "\n${BLUE}=== Setup Complete! ===${NC}"
echo "To sync your logs:"
echo "1. Place Claude export ZIP/folder in: $BASE_DIR/inbox"
echo "2. Place ChatGPT export ZIP/folder in: $BASE_DIR/inbox"
echo "3. Run: ai-log-sync sync"
