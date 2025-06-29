#!/bin/bash

# Devopin Community Backend Uninstaller
# Usage: sudo ./uninstall.sh

set -e

# Configuration
INSTALL_DIR="/opt/devopin-backend"
SERVICE_USER="devopin"
SERVICE_NAME="devopin-backend"

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

# Confirm uninstallation
confirm_uninstall() {
    echo "=================================="
    echo "  Devopin Community Backend       "
    echo "  Uninstaller                     "
    echo "=================================="
    echo
    log_warning "This will completely remove Devopin Backend from your system."
    echo
    echo "The following will be removed:"
    echo "  - Service: $SERVICE_NAME"
    echo "  - Installation directory: $INSTALL_DIR"
    echo "  - Service user: $SERVICE_USER"
    echo "  - All data and logs"
    echo
    
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Uninstallation cancelled."
        exit 0
    fi
}

# Backup data
backup_data() {
    if [[ -f "${INSTALL_DIR}/devopin.db" ]]; then
        log_info "Creating backup of database..."
        BACKUP_DIR="/tmp/devopin-backup-$(date +%Y%m%d-%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        cp "${INSTALL_DIR}/devopin.db" "$BACKUP_DIR/"
        cp -r "${INSTALL_DIR}/logs" "$BACKUP_DIR/" 2>/dev/null || true
        cp "${INSTALL_DIR}/.env" "$BACKUP_DIR/" 2>/dev/null || true
        
        log_success "Backup created: $BACKUP_DIR"
        echo "You can restore your data later if needed."
    fi
}

# Stop and remove service
remove_service() {
    log_info "Stopping and removing systemd service..."
    
    # Stop service
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        systemctl stop ${SERVICE_NAME}
        log_info "Service stopped"
    fi
    
    # Disable service
    if systemctl is-enabled --quiet ${SERVICE_NAME}; then
        systemctl disable ${SERVICE_NAME}
        log_info "Service disabled"
    fi
    
    # Remove service file
    if [[ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]]; then
        rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
        log_info "Service file removed"
    fi
    
    # Reload systemd
    systemctl daemon-reload
    systemctl reset-failed ${SERVICE_NAME} 2>/dev/null || true
    
    log_success "Systemd service removed"
}

# Remove installation directory
remove_installation() {
    log_info "Removing installation directory: $INSTALL_DIR"
    
    if [[ -d "$INSTALL_DIR" ]]; then
        rm -rf "$INSTALL_DIR"
        log_success "Installation directory removed"
    else
        log_warning "Installation directory not found"
    fi
}

# Remove service user
remove_user() {
    log_info "Removing service user: $SERVICE_USER"
    
    if id "$SERVICE_USER" &>/dev/null; then
        # Kill any remaining processes
        pkill -u "$SERVICE_USER" 2>/dev/null || true
        sleep 2
        
        # Remove user
        userdel "$SERVICE_USER" 2>/dev/null || true
        log_success "Service user removed"
    else
        log_warning "Service user not found"
    fi
}

# Remove logs from journal
clean_logs() {
    log_info "Cleaning systemd journal logs..."
    journalctl --vacuum-time=1s --identifier=${SERVICE_NAME} 2>/dev/null || true
}

# Main uninstallation flow
main() {
    check_root
    confirm_uninstall
    
    echo
    log_info "Starting uninstallation..."
    
    backup_data
    remove_service
    remove_installation
    remove_user
    clean_logs
    
    echo
    echo "=================================="
    log_success "Devopin Backend has been completely removed!"
    echo "=================================="
    echo
    
    if [[ -n "$BACKUP_DIR" ]]; then
        echo "Your data backup is available at: $BACKUP_DIR"
        echo
    fi
    
    echo "Thank you for using Devopin Community Backend!"
}

# Run main function
main "$@"