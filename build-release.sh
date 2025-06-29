#!/bin/bash

# Devopin Community Backend Release Builder
# This script builds executables for multiple platforms and creates release packages

set -e

# Configuration
PROJECT_NAME="devopin-backend"
VERSION=${1:-$(date +%Y%m%d-%H%M%S)}
DIST_DIR="dist"
RELEASE_DIR="release"

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

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    if ! python3 -c "import PyInstaller" 2>/dev/null; then
        log_info "Installing PyInstaller..."
        pip install pyinstaller
    fi
    
    log_success "Dependencies check passed"
}

# Clean previous builds
clean_build() {
    log_info "Cleaning previous builds..."
    
    rm -rf "$DIST_DIR"
    rm -rf "$RELEASE_DIR"
    rm -rf build/
    rm -rf __pycache__/
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    mkdir -p "$RELEASE_DIR"
    
    log_success "Build directory cleaned"
}

# Build executable for specific platform
build_executable() {
    local platform=$1
    local arch=$2
    local output_name="${PROJECT_NAME}-${platform}-${arch}"
    
    log_info "Building executable for $platform-$arch..."
    
    # Build with PyInstaller
    pyinstaller build.spec \
        --name "$output_name" \
        --distpath "$DIST_DIR" \
        --clean \
        --noconfirm
    
    if [[ -f "$DIST_DIR/$output_name" ]]; then
        log_success "Built: $output_name"
        
        # Copy to release directory
        cp "$DIST_DIR/$output_name" "$RELEASE_DIR/"
        
        # Make executable
        chmod +x "$RELEASE_DIR/$output_name"
    else
        log_error "Failed to build $output_name"
        return 1
    fi
}

# Create release package
create_release_package() {
    log_info "Creating release package..."
    
    cd "$RELEASE_DIR"
    
    # Create release info
    cat > release-info.txt << EOF
Devopin Community Backend Release
Version: $VERSION
Built: $(date)
Platform: Multi-platform (Linux x64, ARM64)

Files included:
- devopin-backend-linux-amd64    # Executable for Linux x64
- devopin-backend-linux-arm64    # Executable for Linux ARM64
- install.sh                     # Auto-installer script
- uninstall.sh                   # Uninstaller script
- README.md                      # Documentation
- DEPLOYMENT.md                  # Deployment guide

Installation:
curl -sSL https://your-domain.com/install.sh | sudo bash

Or manual installation:
1. Download appropriate executable for your platform
2. Make it executable: chmod +x devopin-backend-*
3. Run: ./devopin-backend-*
EOF
    
    # Copy additional files
    cp ../install.sh .
    cp ../uninstall.sh .
    cp ../README.md .
    cp ../DEPLOYMENT.md .
    cp ../devopin.db . 2>/dev/null || touch devopin.db
    
    # Make scripts executable
    chmod +x install.sh uninstall.sh
    
    # Create tarball
    tar -czf "${PROJECT_NAME}-${VERSION}.tar.gz" *
    
    log_success "Release package created: ${PROJECT_NAME}-${VERSION}.tar.gz"
    
    cd ..
}

# Generate checksums
generate_checksums() {
    log_info "Generating checksums..."
    
    cd "$RELEASE_DIR"
    
    # Generate SHA256 checksums
    sha256sum * > SHA256SUMS
    
    log_success "Checksums generated: SHA256SUMS"
    
    cd ..
}

# Display build summary
display_summary() {
    echo
    echo "=================================="
    echo "  Build Summary"
    echo "=================================="
    echo
    echo "Version: $VERSION"
    echo "Release directory: $RELEASE_DIR"
    echo
    echo "Files created:"
    ls -la "$RELEASE_DIR"
    echo
    echo "Release package: $RELEASE_DIR/${PROJECT_NAME}-${VERSION}.tar.gz"
    echo
    echo "To publish release:"
    echo "1. Upload files to GitHub releases"
    echo "2. Update install.sh URL in documentation"
    echo "3. Test installation on clean system"
    echo
}

# Main build flow
main() {
    echo "=================================="
    echo "  Devopin Community Backend       "
    echo "  Release Builder                 "
    echo "=================================="
    echo
    
    log_info "Building version: $VERSION"
    
    check_dependencies
    clean_build
    
    # Build for different platforms
    # Note: Cross-compilation might require additional setup
    build_executable "linux" "amd64"
    
    # For ARM64, you might need to build on ARM64 system
    # or use cross-compilation tools
    if command -v aarch64-linux-gnu-gcc &> /dev/null; then
        build_executable "linux" "arm64"
    else
        log_warning "ARM64 cross-compilation tools not available"
        log_warning "Build on ARM64 system or install cross-compilation tools"
    fi
    
    create_release_package
    generate_checksums
    display_summary
    
    log_success "Release build completed successfully!"
}

# Handle script arguments
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Usage: $0 [VERSION]"
    echo
    echo "Arguments:"
    echo "  VERSION    Release version (default: current timestamp)"
    echo
    echo "Examples:"
    echo "  $0                    # Build with timestamp version"
    echo "  $0 v1.0.0            # Build with specific version"
    echo "  $0 v1.0.0-beta       # Build beta version"
    echo
    exit 0
fi

# Run main function
main "$@"