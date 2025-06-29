#!/bin/bash

# Devopin Community Backend Installer
# Usage: curl -sSL https://your-domain.com/install.sh | bash

set -e

# Configuration
INSTALL_DIR="/opt/devopin-backend"
SERVICE_USER="devopin"
SERVICE_NAME="devopin-backend"
GITHUB_REPO="your-username/devopin-community"
RELEASE_URL="https://github.com/${GITHUB_REPO}/releases/latest/download"
SOCKET_PATH="/run/devopin-agent.sock"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Detect OS and architecture
detect_system() {
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    case $ARCH in
        x86_64) ARCH="amd64" ;;
        aarch64) ARCH="arm64" ;;
        armv7l) ARCH="armv7" ;;
        *) log_error "Unsupported architecture: $ARCH"; exit 1 ;;
    esac
    
    log_info "Detected: $OS $ARCH"
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y curl wget sqlite3 systemd
    elif command -v yum &> /dev/null; then
        yum update -y
        yum install -y curl wget sqlite systemd
    elif command -v dnf &> /dev/null; then
        dnf update -y
        dnf install -y curl wget sqlite systemd
    else
        log_error "Unsupported package manager. Please install curl, wget, sqlite3, and systemd manually."
        exit 1
    fi
}

# Create service user
create_user() {
    log_info "Creating service user: $SERVICE_USER"
    
    if id "$SERVICE_USER" &>/dev/null; then
        log_warning "User $SERVICE_USER already exists"
    else
        useradd -r -s /bin/false -d $INSTALL_DIR $SERVICE_USER
        log_success "Created user: $SERVICE_USER"
    fi
}

# Download and install application
install_application() {
    log_info "Creating installation directory: $INSTALL_DIR"
    mkdir -p $INSTALL_DIR
    mkdir -p $INSTALL_DIR/logs
    cd $INSTALL_DIR
    
    log_info "Downloading Devopin Backend..."
    
    # Download executable
    BINARY_NAME="devopin-backend-${OS}-${ARCH}"
    wget -q --show-progress "${RELEASE_URL}/${BINARY_NAME}" -O devopin-backend
    
    if [[ ! -f "devopin-backend" ]]; then
        log_error "Failed to download executable"
        exit 1
    fi
    
    # Make executable
    chmod +x devopin-backend
    
    # Download additional files
    log_info "Downloading configuration files..."
    wget -q "${RELEASE_URL}/devopin.db" -O devopin.db || touch devopin.db
    
    # Create environment file
    cat > .env << EOF
DATABASE_URL=sqlite:///./devopin.db
PYTHONUNBUFFERED=1
EOF
    
    log_success "Application installed to $INSTALL_DIR"
}

# Install systemd service
install_service() {
    log_info "Installing systemd service..."
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Devopin Community Backend Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/devopin-backend
Restart=always
RestartSec=10

# Environment variables
Environment=DATABASE_URL=sqlite:///./devopin.db
Environment=PYTHONUNBUFFERED=1

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${INSTALL_DIR}/logs
ReadWritePaths=${INSTALL_DIR}/devopin.db
ReadWritePaths=/run/devopin-agent.sock
ReadWritePaths=/tmp/devopin-agent.sock

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${SERVICE_NAME}

[Install]
WantedBy=multi-user.target
EOF
    
    # Set ownership
    chown -R ${SERVICE_USER}:${SERVICE_USER} ${INSTALL_DIR}
    
    # Reload systemd
    systemctl daemon-reload
    systemctl enable ${SERVICE_NAME}
    
    log_success "Systemd service installed and enabled"
}

# Start service
start_service() {
    log_info "Starting Devopin Backend service..."
    
    systemctl start ${SERVICE_NAME}
    
    # Wait a moment and check status
    sleep 3
    
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        log_success "Devopin Backend is running!"
        log_info "Service status: systemctl status ${SERVICE_NAME}"
        log_info "View logs: journalctl -u ${SERVICE_NAME} -f"
        log_info "Web interface: http://localhost:8080"
    else
        log_error "Failed to start service. Check logs: journalctl -u ${SERVICE_NAME}"
        exit 1
    fi
}

# Create uninstaller
create_uninstaller() {
    cat > ${INSTALL_DIR}/uninstall.sh << 'EOF'
#!/bin/bash

SERVICE_NAME="devopin-backend"
INSTALL_DIR="/opt/devopin-backend"
SERVICE_USER="devopin"

echo "Stopping and removing Devopin Backend..."

# Stop and disable service
systemctl stop $SERVICE_NAME 2>/dev/null || true
systemctl disable $SERVICE_NAME 2>/dev/null || true

# Remove service file
rm -f /etc/systemd/system/${SERVICE_NAME}.service

# Reload systemd
systemctl daemon-reload

# Remove installation directory
rm -rf $INSTALL_DIR

# Remove user
userdel $SERVICE_USER 2>/dev/null || true

echo "Devopin Backend has been uninstalled."
EOF
    
    chmod +x ${INSTALL_DIR}/uninstall.sh
    log_info "Uninstaller created: ${INSTALL_DIR}/uninstall.sh"
}

# Main installation flow
main() {
    echo "=================================="
    echo "  Devopin Community Backend       "
    echo "  Installation Script             "
    echo "=================================="
    echo
    
    check_root
    detect_system
    install_dependencies
    create_user
    install_application
    install_service
    create_uninstaller
    start_service
    
    echo
    echo "=================================="
    log_success "Installation completed successfully!"
    echo "=================================="
    echo
    echo "Next steps:"
    echo "1. Open your browser and go to: http://localhost:8080"
    echo "2. Create your first user account"
    echo "3. Configure your monitoring settings"
    echo
    echo "Useful commands:"
    echo "  sudo systemctl status ${SERVICE_NAME}     # Check service status"
    echo "  sudo journalctl -u ${SERVICE_NAME} -f     # View live logs"
    echo "  sudo systemctl restart ${SERVICE_NAME}    # Restart service"
    echo "  sudo ${INSTALL_DIR}/uninstall.sh          # Uninstall"
    echo
}

# Run main function
main "$@"