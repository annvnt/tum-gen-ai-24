# Financial Analysis Platform - Troubleshooting Guide

## Common Issues and Solutions

### 1. Port Conflicts

#### Issue: "bind: address already in use"

**Symptoms:**
- Docker fails to start with port binding errors
- Error: `ports are not available: exposing port TCP 0.0.0.0:3000`

**Solutions:**

1. **Use the startup script** (recommended):
   ```bash
   ./start-platform.sh
   ```
   This automatically finds available ports and configures the platform.

2. **Manual port configuration**:
   ```bash
   export FRONTEND_PORT=3001
   export API_PORT=8001
   export QDRANT_PORT=6334
   docker-compose up
   ```

3. **Check what's using the port**:
   ```bash
   # On macOS/Linux:
   lsof -i :3000
   
   # On Windows:
   netstat -ano | findstr :3000
   ```

### 2. Next.js Build Warnings

#### Issue: "Dynamic server usage" warnings

**Symptoms:**
- Build warnings about routes not being statically optimized
- Messages about `nextUrl.searchParams` preventing static rendering

**Solution:**
This has been resolved by adding `export const dynamic = 'force-dynamic'` to all API routes that use dynamic parameters.

### 3. Service Startup Issues

#### API Service Won't Start

**Checklist:**
1. Verify environment variables are set:
   ```bash
   cat .env
   ```

2. Check Python dependencies:
   ```bash
   docker-compose logs financial-report-api
   ```

3. Verify GCS credentials:
   ```bash
   ls -la gcs-credentials.json
   ```

#### Frontend Service Won't Start

**Checklist:**
1. Check Node.js version compatibility
2. Verify API connectivity:
   ```bash
   curl http://localhost:8000/health
   ```
3. Check frontend logs:
   ```bash
   docker-compose logs frontend
   ```

### 4. Environment Variable Issues

#### Required Environment Variables:
- `OPENAI_API_KEY` or `API_KEY`
- `JINA_API_KEY`
- `GCS_BUCKET_NAME`
- `GCS_CREDENTIALS_FILE` (path to your GCS credentials)

#### Optional Environment Variables:
- `FRONTEND_PORT` (default: 3000)
- `API_PORT` (default: 8000)
- `QDRANT_PORT` (default: 6333)

### 5. Quick Start Commands

#### Standard startup:
```bash
./start-platform.sh
```

#### Check ports only:
```bash
./start-platform.sh --check-ports
```

#### Manual port setup:
```bash
export FRONTEND_PORT=3001
export API_PORT=8001
docker-compose up --build
```

### 6. Debug Mode

#### Enable verbose logging:
```bash
docker-compose up --build --verbose
```

#### View specific service logs:
```bash
docker-compose logs -f [service-name]
```

### 7. Common Docker Commands

#### Clean rebuild:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

#### Reset volumes (⚠️ deletes data):
```bash
docker-compose down -v
```

### 8. Network Issues

#### Check container connectivity:
```bash
docker network ls
docker network inspect [network-name]
```

#### Test API from frontend container:
```bash
docker exec -it financial-frontend sh
# Inside container:
curl http://financial-report-api:8000/health
```

## Getting Help

If you continue to experience issues:

1. Check the logs:
   ```bash
   docker-compose logs > platform-logs.txt
   ```

2. Create an issue with:
   - Platform (macOS/Linux/Windows)
   - Docker version: `docker --version`
   - Relevant log output
   - Environment (dev/prod)

3. Verify installation:
   ```bash
   ./start-platform.sh --check-ports
   ```
EOF < /dev/null