# SCADA-IDS-KC Docker Configuration

This directory contains Docker-related files for containerized deployment and building of the SCADA-IDS-KC system.

## 📁 Files

### Docker Configuration Files
- **`Dockerfile.windows-build`** - Dockerfile for building SCADA-IDS-KC on Windows containers
- **`docker-compose.yml`** - Docker Compose configuration for multi-container deployment

## 🐳 Docker Usage

### Building with Docker

#### Windows Build Container
```bash
# Build the Windows build container
docker build -f docker/Dockerfile.windows-build -t scada-ids-kc-builder .

# Run the build process
docker run --rm -v ${PWD}:/workspace scada-ids-kc-builder
```

#### Docker Compose
```bash
# Start the complete SCADA-IDS-KC stack
docker-compose -f docker/docker-compose.yml up -d

# Stop the stack
docker-compose -f docker/docker-compose.yml down

# View logs
docker-compose -f docker/docker-compose.yml logs -f
```

## 🔧 Configuration

### Environment Variables
The Docker containers support the following environment variables:

- `SCADA_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `SCADA_INTERFACE` - Network interface to monitor
- `SCADA_THRESHOLD` - ML detection threshold (0.0-1.0)
- `SCADA_CONFIG_PATH` - Path to configuration file

### Volume Mounts
Recommended volume mounts for persistent data:

```yaml
volumes:
  - ./config:/app/config          # Configuration files
  - ./logs:/app/logs              # Log files
  - ./models:/app/models          # ML models
```

## 🚀 Deployment Scenarios

### Development Environment
```bash
# Quick development setup
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up
```

### Production Environment
```bash
# Production deployment with resource limits
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d
```

## 📋 Requirements

### Docker Requirements
- Docker Engine 20.10+
- Docker Compose 2.0+
- Windows containers (for Windows builds)

### Host Requirements
- Network interface access for packet capture
- Sufficient memory for ML models (minimum 2GB)
- Storage for logs and configuration

## 🔒 Security Considerations

### Network Access
- Container requires privileged access for packet capture
- Consider using host networking mode for full interface access
- Limit container capabilities to minimum required

### Data Protection
- Mount configuration and logs as volumes
- Use secrets management for sensitive configuration
- Regular backup of persistent data

## 🛠️ Troubleshooting

### Common Issues

#### Permission Denied for Packet Capture
```bash
# Run with privileged mode
docker run --privileged scada-ids-kc

# Or use specific capabilities
docker run --cap-add=NET_RAW --cap-add=NET_ADMIN scada-ids-kc
```

#### Network Interface Not Found
```bash
# Use host networking
docker run --network=host scada-ids-kc

# Or map specific interfaces
docker run --device=/dev/net/tun scada-ids-kc
```

## 📝 Notes

- Windows containers require Windows Docker host
- Linux containers provide better performance for packet capture
- Consider using Docker Swarm or Kubernetes for production scaling
- Monitor container resource usage during operation

## 🔄 Maintenance

- Regularly update base images for security patches
- Monitor container logs for performance issues
- Backup persistent volumes regularly
- Test container updates in staging environment first
