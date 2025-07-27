#\!/bin/bash

# Financial Analysis Platform Startup Script
# Automatically handles port conflicts and provides flexible configuration

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default ports
DEFAULT_API_PORT=8000
DEFAULT_FRONTEND_PORT=3000
DEFAULT_QDRANT_PORT=6333

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_port() {
    local port=$1
    local service=$2
    if lsof -i :"$port" >/dev/null 2>&1; then
        print_warning "Port $port is already in use by another service"
        return 1
    else
        print_status "Port $port is available for $service"
        return 0
    fi
}

find_available_port() {
    local base_port=$1
    local service=$2
    local port=$base_port
    while \! check_port $port "$service"; do
        port=$((port + 1))
        if [ $port -gt $((base_port + 100)) ]; then
            print_error "Could not find available port for $service after 100 attempts"
            exit 1
        fi
    done
    echo $port
}

check_dependencies() {
    print_status "Checking dependencies..."
    for cmd in docker docker-compose curl; do
        if \! command -v $cmd >/dev/null 2>&1; then
            print_error "$cmd is not installed. Please install $cmd and try again."
            exit 1
        fi
    done
    print_success "All dependencies are available"
}

check_env_file() {
    if [ \! -f .env ]; then
        print_warning ".env file not found. Creating basic .env file..."
        cat > .env << 'ENV_EOF'
# API Configuration
OPENAI_API_KEY=your_openai_api_key_here
GCS_BUCKET_NAME=your_gcs_bucket_name
GCS_PROJECT_ID=your_gcs_project_id

# Port Configuration
API_PORT=8000
FRONTEND_PORT=3000
QDRANT_PORT=6333

# Backend Configuration
QDRANT_HOST=qdrant
BACKEND_URL=http://127.0.0.1:8000
ENV_EOF
        print_success "Created basic .env file"
    fi
}

load_env() {
    if [ -f .env ]; then
        export $(cat .env | grep -v '^#' | xargs 2>/dev/null || true)
    fi
}

main() {
    print_status "Starting Financial Analysis Platform..."
    
    check_dependencies
    check_env_file
    load_env
    
    api_port=$(find_available_port $DEFAULT_API_PORT "API")
    frontend_port=$(find_available_port $DEFAULT_FRONTEND_PORT "Frontend")
    qdrant_port=$(find_available_port $DEFAULT_QDRANT_PORT "Qdrant")
    
    sed -i.bak "s/API_PORT=.*/API_PORT=$api_port/" .env
    sed -i.bak "s/FRONTEND_PORT=.*/FRONTEND_PORT=$frontend_port/" .env
    sed -i.bak "s/QDRANT_PORT=.*/QDRANT_PORT=$qdrant_port/" .env
    
    export API_PORT=$api_port
    export FRONTEND_PORT=$frontend_port
    export QDRANT_PORT=$qdrant_port
    
    print_success "Using ports: API=$api_port, Frontend=$frontend_port, Qdrant=$qdrant_port"
    
    docker-compose up --build -d
    
    print_success "Platform started successfully\!"
    echo ""
    echo "Access your services at:"
    echo "  API: http://localhost:$api_port"
    echo "  Frontend: http://localhost:$frontend_port"
    echo "  Qdrant: http://localhost:$qdrant_port"
}

main "$@"
EOF < /dev/null