# Generate Network Traffic for SCADA-IDS Testing
# This script generates various types of network traffic to test packet capture

Write-Host "=== Generating Network Traffic for SCADA-IDS Testing ===" -ForegroundColor Green
Write-Host "Target Interface: Ethernet (10.10.11.109)" -ForegroundColor Yellow
Write-Host "Duration: 60 seconds" -ForegroundColor Yellow
Write-Host ""

$startTime = Get-Date
$endTime = $startTime.AddSeconds(60)
$counter = 0

Write-Host "Starting traffic generation..." -ForegroundColor Green

while ((Get-Date) -lt $endTime) {
    $counter++
    
    # Generate different types of traffic
    try {
        # HTTP requests to generate TCP traffic
        if ($counter % 3 -eq 0) {
            Write-Host "[$counter] Generating HTTP traffic..." -ForegroundColor Cyan
            Invoke-WebRequest -Uri "http://httpbin.org/get" -TimeoutSec 2 -ErrorAction SilentlyContinue | Out-Null
        }
        
        # DNS queries
        if ($counter % 2 -eq 0) {
            Write-Host "[$counter] Generating DNS traffic..." -ForegroundColor Cyan
            nslookup google.com 8.8.8.8 | Out-Null
        }
        
        # ICMP ping traffic
        Write-Host "[$counter] Generating ICMP traffic..." -ForegroundColor Cyan
        ping -n 1 8.8.8.8 | Out-Null
        
        # HTTPS traffic
        if ($counter % 4 -eq 0) {
            Write-Host "[$counter] Generating HTTPS traffic..." -ForegroundColor Cyan
            Invoke-WebRequest -Uri "https://httpbin.org/get" -TimeoutSec 2 -ErrorAction SilentlyContinue | Out-Null
        }
        
        # Small delay between requests
        Start-Sleep -Milliseconds 500
        
    } catch {
        # Continue on errors
    }
    
    # Progress update every 10 iterations
    if ($counter % 10 -eq 0) {
        $elapsed = (Get-Date) - $startTime
        Write-Host "Progress: $counter requests sent, $($elapsed.TotalSeconds.ToString('F1'))s elapsed" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== Traffic Generation Complete ===" -ForegroundColor Green
Write-Host "Total requests: $counter" -ForegroundColor Yellow
Write-Host "Duration: $((Get-Date) - $startTime | Select-Object -ExpandProperty TotalSeconds) seconds" -ForegroundColor Yellow
