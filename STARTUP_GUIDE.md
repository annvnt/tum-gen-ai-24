# Financial Analysis Platform - Startup Guide

## Quick Start

### 1. Automated Startup (Recommended)
Use the provided startup script for automatic port conflict resolution:

```bash
./start-platform.sh
```

### 2. Manual Startup
If you prefer manual control:

```bash
# Set your preferred ports
export API_PORT=8000
export FRONTEND_PORT=3000
export QDRANT_PORT=6333

# Start the platform
docker-compose up --build
```

## Startup Script Features

### Automatic Port Conflict Resolution
The startup script automatically detects and resolves port conflicts:
- Checks if ports 8000, 3000, and 6333 are available
- Finds the next available ports if conflicts exist
- Updates configuration files automatically
- Provides clear feedback on port usage

### Usage Examples

```bash
# Basic usage - auto-resolve conflicts
./start-platform.sh

# Use specific ports
./start-platform.sh -p 8001,3001,6334

# Development mode with logs
./start-platform.sh -d -l

# Skip port resolution (use defaults)
./start-platform.sh -s

# Show help
./start-platform.sh -h
```

### Script Options
- `-h, --help`: Show help message
- `-p, --ports`: Use specific ports (format: API,Frontend,Qdrant)
- `-d, --dev`: Start in development mode
- `-s, --skip`: Skip port conflict resolution
- `-l, --logs`: Show logs after startup

## Environment Configuration

### Environment Variables
The platform uses these environment variables:

- `API_PORT`: Backend API port (default: 8000)
- `FRONTEND_PORT`: Next.js frontend port (default: 3000)
- `QDRANT_PORT`: Qdrant vector database port (default: 6333)
- `OPENAI_API_KEY`: Your OpenAI API key
- `GCS_BUCKET_NAME`: Google Cloud Storage bucket name
- `GCS_PROJECT_ID`: Google Cloud project ID

### .env File Setup
Create a `.env` file in the project root:

```bash
# Copy from example
cp .env.example .env

# Edit with your configuration
nano .env
```

## Port Configuration

### Default Ports
- **API**: 8000 (FastAPI backend)
- **Frontend**: 3000 (Next.js)
- **Qdrant**: 6333 (Vector database)

### Custom Ports
Set custom ports using environment variables:

```bash
export API_PORT=8001
export FRONTEND_PORT=3001
export QDRANT_PORT=6334
./start-platform.sh
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   
   # Use the startup script to auto-resolve
   ./start-platform.sh
   ```

2. **Docker Issues**
   ```bash
   # Check Docker status
   docker ps
   
   # View logs
   docker-compose logs
   
   # Rebuild containers
   docker-compose build --no-cache
   ```

3. **Environment Variables**
   ```bash
   # Check current environment
   env | grep -E "(API|FRONTEND|QDRANT)"
   
   # Reload environment
   source .env
   ```

### Service Health Checks

The platform includes health check endpoints:
- API: `http://localhost:8000/health`
- Frontend: `http://localhost:3000/api/health`
- Qdrant: `http://localhost:6333/health`

### Log Management

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs financial-report-api
docker-compose logs frontend
docker-compose logs qdrant

# Follow logs in real-time
docker-compose logs -f
```

## Development Workflow

### 1. First Time Setup
```bash
# Clone repository
git clone <repository-url>
cd financial-analysis-platform

# Make startup script executable
chmod +x start-platform.sh

# Start platform
./start-platform.sh
```

### 2. Daily Development
```bash
# Start platform with logs
./start-platform.sh -l

# Make changes to code
# The platform supports hot-reload in development mode

# Stop platform
docker-compose down
```

### 3. Production Deployment
```bash
# Use specific ports for production
./start-platform.sh -p 8000,3000,6333

# Or use environment variables
export API_PORT=8000
export FRONTEND_PORT=3000
export QDRANT_PORT=6333
docker-compose up -d
```

## Advanced Configuration

### Docker Compose Overrides
Create `docker-compose.override.yml` for local development:

```yaml
version: '3.8'
services:
  financial-report-api:
    volumes:
      - ./src:/app/src:ro
    environment:
      - DEBUG=true
  
  frontend:
    volumes:
      - ./web:/app:ro
      - /app/node_modules
    environment:
      - NODE_ENV=development
```

### Network Configuration
For custom networks or external access:

```bash
# Allow external access
export NEXT_PUBLIC_API_URL=http://0.0.0.0:8000
./start-platform.sh
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review service logs: `docker-compose logs`
3. Verify port availability: `lsof -i :PORT`
4. Check environment configuration: `cat .env`
EOF < /dev/null