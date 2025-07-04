#!/bin/bash

# Build for release - creates deployment-ready assets
VERSION=${1:-$(date +%Y%m%d-%H%M%S)}
RELEASE_DIR="release-assets"

log_info() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

main() {
    echo "Building release assets for deployment..."
    
    # Clean
    rm -rf dist/ build/ "$RELEASE_DIR"
    mkdir -p "$RELEASE_DIR"
    
    # Build executable
    log_info "Building executable..."
    pyinstaller build.spec \
        --name "devopin-app-linux-amd64" \
        --onefile --clean --noconfirm
    
    # Copy release assets
    log_info "Preparing release assets..."
    cp dist/devopin-app-linux-amd64 "$RELEASE_DIR/"
    cp install.sh "$RELEASE_DIR/"
    cp uninstall.sh "$RELEASE_DIR/"
    cp devopin.db "$RELEASE_DIR/"
    cp config.yaml.example "$RELEASE_DIR/"
    
    # Make executable
    chmod +x "$RELEASE_DIR"/*
    
    # Create tarball (optional)
    cd "$RELEASE_DIR"
    tar -czf "../devopin-release-${VERSION}.tar.gz" *
    cd ..
    
    echo "✅ Release assets ready in: $RELEASE_DIR"
    echo "✅ Upload these files to GitHub release"
    
    ls -la "$RELEASE_DIR"
}

main "$@"