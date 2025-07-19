# SCADA-IDS-KC Configuration Templates

This directory contains pre-configured templates for different deployment scenarios of SCADA-IDS-KC.

## Available Templates

### 1. Development Template (`development.cfg`)
**Use Case**: Development, testing, and debugging environments
- **Detection Sensitivity**: High (threshold 0.01) for catching edge cases
- **Logging**: Verbose DEBUG level logging
- **Performance**: Optimized for responsiveness over efficiency
- **Security**: Relaxed settings for development convenience
- **Features**: All debugging and experimental features enabled

**Best For**:
- Software development and testing
- Feature validation
- Performance tuning
- Debug troubleshooting

### 2. Production Template (`production.cfg`)
**Use Case**: Standard production deployments
- **Detection Sensitivity**: Balanced (threshold 0.05) for reliable operation
- **Logging**: INFO level with comprehensive error tracking
- **Performance**: Optimized for sustained operation
- **Security**: Balanced security with operational requirements
- **Features**: Stable features only, performance optimized

**Best For**:
- General production deployments
- Standard enterprise networks
- Balanced security and performance needs
- Long-term operational stability

### 3. High Security Template (`high-security.cfg`)
**Use Case**: Critical infrastructure and maximum security environments
- **Detection Sensitivity**: Very high (threshold 0.02) for maximum protection
- **Logging**: Comprehensive logging with extended retention
- **Performance**: High-performance settings for critical monitoring
- **Security**: Maximum security settings and validation
- **Features**: Conservative feature set focused on reliability

**Best For**:
- Critical infrastructure protection
- High-value network assets
- Compliance-heavy environments
- Maximum threat detection requirements

## Using Templates

### Quick Setup
1. Choose the appropriate template for your environment
2. Copy the template to the project root directory as `SIKC.cfg`:
   ```bash
   # For development
   cp config/templates/development.cfg SIKC.cfg
   
   # For production
   cp config/templates/production.cfg SIKC.cfg
   
   # For high security
   cp config/templates/high-security.cfg SIKC.cfg
   ```
3. Customize the configuration for your specific needs
4. Start SCADA-IDS-KC normally

### Customization Guide

#### Network Interface Configuration
```ini
[network]
# Set your specific network interface
interface = eth0  # Replace with your interface name

# Customize packet filter if needed
bpf_filter = tcp and tcp[13]=2  # SYN packets only (recommended)
```

#### Detection Threshold Tuning
```ini
[detection]
# Adjust based on your environment:
# 0.01 = Very sensitive (more false positives, catches subtle attacks)
# 0.05 = Balanced (recommended for most environments)
# 0.10 = Less sensitive (fewer false positives, may miss subtle attacks)
prob_threshold = 0.05
```

#### Performance Optimization
```ini
[performance]
# Adjust worker threads based on CPU cores
worker_threads = 4  # Recommended: CPU cores / 2

# Increase batch size for high-traffic networks
batch_size = 200  # Higher = better throughput, more memory usage
```

#### Logging Configuration
```ini
[logging]
# Adjust log levels based on needs:
# DEBUG = Verbose (development)
# INFO = Standard (production)
# WARNING = Minimal (high-performance)
log_level = INFO

# Configure log rotation
max_log_size = 10485760  # 10MB
backup_count = 30        # Keep 30 backup files
```

## Configuration Validation

After customizing any template, validate your configuration:

```bash
# Validate configuration
python main.py --cli --config-validate

# Get detailed configuration information
python main.py --cli --config-info

# Test with your settings
python main.py --cli --test-ml
python main.py --cli --test-notifications
```

## Environment-Specific Considerations

### Development Environment
- Use localhost or VM interfaces
- Enable debug logging and experimental features
- Lower resource limits for development machines
- Faster refresh rates for immediate feedback

### Production Environment
- Use dedicated network interfaces (preferably SPAN ports)
- Optimize for sustained 24/7 operation
- Configure appropriate alert thresholds
- Enable comprehensive logging for incident response

### High Security Environment
- Use dedicated, isolated monitoring infrastructure
- Implement strict access controls
- Enable all security validation features
- Configure redundant logging and alerting

## Template Comparison

| Feature | Development | Production | High Security |
|---------|-------------|------------|---------------|
| Detection Threshold | 0.01 (Very Sensitive) | 0.05 (Balanced) | 0.02 (Highly Sensitive) |
| Log Level | DEBUG | INFO | DEBUG (Security) |
| Worker Threads | 2 | 4 | 8 |
| Auto-start Monitoring | No | Yes | Yes |
| Experimental Features | Yes | No | No |
| Alert Cooldown | 10s | 30s | 15s |
| Backup Retention | 10 | 15 | 25 |
| Performance Profiling | Yes | No | Yes |

## Best Practices

### Before Deployment
1. **Test thoroughly** with your specific network traffic
2. **Validate performance** under expected load
3. **Configure monitoring** for the SCADA-IDS-KC system itself
4. **Set up alerting** for system health and security events
5. **Create configuration backups** before going live

### After Deployment
1. **Monitor false positive rates** and adjust thresholds accordingly
2. **Review logs regularly** for system health and security insights
3. **Update ML models** as new attack patterns emerge
4. **Maintain configuration backups** and document all changes
5. **Test disaster recovery** procedures periodically

### Security Considerations
1. **Protect configuration files** with appropriate file permissions
2. **Use secure channels** for configuration management
3. **Audit configuration changes** and maintain change logs
4. **Regular security reviews** of detection thresholds and rules
5. **Implement defense in depth** - SCADA-IDS-KC is one layer

## Troubleshooting

### Common Issues
- **High CPU usage**: Reduce worker threads or increase batch size
- **Too many false positives**: Increase detection threshold
- **Missing attacks**: Decrease detection threshold or review ML model
- **Log file growth**: Reduce log level or increase rotation frequency
- **Interface not found**: Check interface name and permissions

### Performance Optimization
- **High traffic networks**: Increase batch size and worker threads
- **Resource-constrained systems**: Reduce worker threads and batch size
- **Storage limitations**: Increase log rotation frequency
- **Memory issues**: Reduce tracking limits and enable aggressive cleanup

For additional support, refer to the main configuration documentation and system logs.