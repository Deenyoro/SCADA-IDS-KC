#!/usr/bin/env python3
"""
Test SYN flood detection by simulating SYN packets
"""

import sys
import time
import threading
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from scapy.all import *
from scada_ids.controller import get_controller

def generate_syn_packets():
    """Generate some SYN packets for testing"""
    try:
        print("Generating SYN packets for testing...")
        target_ip = "192.168.1.100"  # Test target
        src_ip = "192.168.1.200"     # Test source
        
        # Create SYN packets to different ports
        for i in range(10):
            pkt = IP(src=src_ip, dst=target_ip) / TCP(sport=1000+i, dport=80, flags="S")
            send(pkt, verbose=0)
            time.sleep(0.1)
            
        print("Generated 10 SYN packets")
    except Exception as e:
        print(f"Error generating SYN packets: {e}")

def test_syn_detection():
    """Test the complete SYN flood detection system"""
    print("=== Testing SYN Flood Detection ===")
    
    # Initialize controller
    controller = get_controller()
    
    # Check ML status
    status = controller.get_status()
    print(f"ML model loaded: {status.get('ml_model_loaded', False)}")
    print(f"Available interfaces: {len(status.get('interfaces', []))}")
    
    # Start monitoring
    print("Starting monitoring...")
    if controller.start():
        print("✓ Monitoring started successfully")
        
        # Monitor for a few seconds first
        print("Monitoring baseline for 3 seconds...")
        for i in range(3):
            time.sleep(1)
            stats = controller.get_statistics()
            print(f"  Baseline [{i+1}s]: Packets={stats.get('packets_captured', 0)}, Threats={stats.get('threats_detected', 0)}")
        
        # Generate SYN packets in a separate thread
        syn_thread = threading.Thread(target=generate_syn_packets)
        syn_thread.start()
        
        # Monitor during and after SYN generation
        print("Monitoring during SYN packet generation...")
        for i in range(8):
            time.sleep(1)
            stats = controller.get_statistics()
            packets = stats.get('packets_captured', 0)
            threats = stats.get('threats_detected', 0)
            print(f"  Test [{i+1}s]: Packets={packets}, Threats={threats}")
            
        syn_thread.join()
        
        # Final statistics
        controller.stop()
        final_stats = controller.get_statistics()
        
        print("\n=== Final Results ===")
        print(f"Total packets captured: {final_stats.get('packets_captured', 0)}")
        print(f"Total threats detected: {final_stats.get('threats_detected', 0)}")
        print(f"Alerts sent: {final_stats.get('alerts_sent', 0)}")
        
        if final_stats.get('packets_captured', 0) > 0:
            print("✓ SUCCESS: Packet capture is working")
        else:
            print("⚠ INFO: No packets captured (might need admin privileges)")
            
        if final_stats.get('threats_detected', 0) > 0:
            print("✓ SUCCESS: Threat detection is working!")
        else:
            print("ℹ INFO: No threats detected (generated packets might not trigger detection)")
            
    else:
        print("✗ ERROR: Failed to start monitoring")

if __name__ == "__main__":
    test_syn_detection()