#!/bin/bash

# Financial Report API Docker Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if .env file exists
check_env() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        print_warning "Please create a .env file with your API_KEY:"
        echo "API_KEY=your_openai_api_key_here"
        exit 1
    fi
    print_status ".env file found"
}

# Function to check if required directories exist
check_directories() {
    if [ ! -d "excel_ocr/input" ]; then
        print_warning "excel_ocr/input directory not found, creating it..."
        mkdir -p excel_ocr/input
    fi

    if [ ! -d "excel_ocr/output" ]; then
        print_warning "excel_ocr/output directory not found, creating it..."
        mkdir -p excel_ocr/output
    fi

    if [ ! -f "excel_ocr/api_server.py" ]; then
        print_error "excel_ocr/api_server.py not found!"
        print_error "Please run this script from the project root directory"
        exit 1
    fi

    print_status "Directory structure verified"
}

# Function to start the container
start() {
    print_status "Building and starting Financial Report API container..."
    docker compose up --build -d
    print_status "Container started successfully"
    print_status "API is available at: http://localhost:8000"
    print_status "API documentation at: http://localhost:8000/docs"
}

# Function to stop the container
stop() {
    print_status "Stopping Financial Report API container..."
    docker compose down
    print_status "Container stopped successfully"
}

# Function to restart the container
restart() {
    stop
    start
}

# Function to view logs
logs() {
    print_status "Showing container logs..."
    docker-compose logs -f financial-report-api
}

# Function to check status
status() {
    print_status "Checking container status..."
    docker compose ps
}

# Function to run tests
test() {
    print_status "Running API tests..."
    if [ -f "excel_ocr/test_api.py" ]; then
        cd excel_ocr && python test_api.py
    else
        print_error "excel_ocr/test_api.py not found"
        exit 1
    fi
}

# Function to clean up
clean() {
    print_status "Cleaning up Docker resources..."
    docker compose down --volumes --remove-orphans
    docker system prune -f
    print_status "Cleanup completed"
}

# Main script logic
case "${1:-start}" in
    start)
        check_env
        check_directories
        start
        ;;
    stop)
        stop
        ;;
    restart)
        check_env
        check_directories
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    test)
        test
        ;;
    clean)
        clean
        ;;
    *)
        echo "Financial Report API Docker Management"
        echo "Usage: $0 {start|stop|restart|logs|status|test|clean}"
        echo ""
        echo "Commands:"
        echo "  start   - Build and start the container"
        echo "  stop    - Stop the container"
        echo "  restart - Restart the container"
        echo "  logs    - View container logs"
        echo "  status  - Check container status"
        echo "  test    - Run API tests"
        echo "  clean   - Clean up Docker resources"
        echo ""
        echo "Example: $0 start"
        exit 1
        ;;
esac