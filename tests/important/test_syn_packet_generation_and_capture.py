#!/usr/bin/env python3
"""
Comprehensive SYN Packet Generation and Capture Test
Generates SYN packets and verifies they are captured and analyzed by the SCADA-IDS-KC system.
"""

import time
import threading
import subprocess
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from scapy.all import *
from scada_ids.capture import PacketSniffer
from scada_ids.controller import IDSController
from scada_ids.settings import AppSettings

class SynTrafficGenerator:
    """Generates SYN packets for testing packet capture."""
    
    def __init__(self, target_port=80, packet_count=50):
        self.target_port = target_port
        self.packet_count = packet_count
        self.packets_sent = 0
        self.running = False
        
    def generate_syn_packets(self):
        """Generate SYN packets to loopback interface."""
        print(f"Starting SYN packet generation: {self.packet_count} packets to port {self.target_port}")
        
        self.running = True
        for i in range(self.packet_count):
            if not self.running:
                break
                
            # Create SYN packet
            packet = IP(src="127.0.0.1", dst="127.0.0.1") / TCP(
                sport=random.randint(1024, 65535),
                dport=self.target_port,
                flags="S",  # SYN flag
                seq=random.randint(1000, 100000)
            )
            
            try:
                send(packet, verbose=0)
                self.packets_sent += 1
                print(f"Sent SYN packet {i+1}/{self.packet_count} (sport={packet[TCP].sport}, dport={packet[TCP].dport})")
                time.sleep(0.1)  # Small delay between packets
                
            except Exception as e:
                print(f"Error sending packet {i+1}: {e}")
                
        print(f"SYN packet generation complete. Total sent: {self.packets_sent}")
        self.running = False
        
    def stop(self):
        """Stop packet generation."""
        self.running = False

class PacketCaptureTest:
    """Test packet capture with real packet analysis."""
    
    def __init__(self):
        self.settings = None
        self.packet_sniffer = None
        self.controller = None
        self.captured_packets = []
        self.ml_analyses = []
        
    def setup(self):
        """Setup the packet capture system."""
        print("Setting up packet capture test...")
        
        # Load settings
        self.settings = AppSettings.load_from_yaml()
        print(f"BPF Filter: {self.settings.network.bpf_filter}")
        print(f"Interface: {self.settings.network.interface}")
        
        # Create IDS controller for full ML analysis pipeline
        self.controller = IDSController()
        
        # Get the packet sniffer from controller (already configured with ML callback)
        self.packet_sniffer = self.controller.packet_sniffer
        
        # Override packet handler to track packets AND call ML processing
        original_handler = self.packet_sniffer._packet_handler
        
        def tracking_handler(packet):
            """Track packets and call original handler."""
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            packet_info = {
                "timestamp": timestamp,
                "src": packet[IP].src if IP in packet else "unknown",
                "dst": packet[IP].dst if IP in packet else "unknown",
                "sport": packet[TCP].sport if TCP in packet else 0,
                "dport": packet[TCP].dport if TCP in packet else 0,
                "flags": str(packet[TCP].flags) if TCP in packet else "0",
                "packet_length": len(packet)
            }
            self.captured_packets.append(packet_info)
            print(f"CAPTURED PACKET: {packet_info}")
            
            # Call original handler for ML processing
            try:
                original_handler(packet)
            except Exception as e:
                print(f"Error in original packet handler: {e}")
        
        # Set our tracking handler
        self.packet_sniffer._packet_handler = tracking_handler
        
        # Hook into the controller to track ML analyses
        original_processing_loop = self.controller._processing_loop
        
        def tracking_processing_loop():
            """Track ML analyses and call original processing loop."""
            print("ML PROCESSING LOOP STARTED!")
            try:
                original_processing_loop()
            except Exception as e:
                print(f"Error in processing loop: {e}")
        
        self.controller._processing_loop = tracking_processing_loop
        
        print("Packet capture test setup complete.")
        
    def start_capture(self):
        """Start packet capture and ML processing."""
        print("Starting IDS controller with ML processing...")
        try:
            success = self.controller.start()
            if success:
                print("IDS controller started successfully (includes packet capture + ML analysis)")
                return True
            else:
                print("Failed to start IDS controller")
                return False
        except Exception as e:
            print(f"Error starting IDS controller: {e}")
            return False
            
    def stop_capture(self):
        """Stop packet capture and ML processing."""
        print("Stopping IDS controller...")
        try:
            self.controller.stop()
            print("IDS controller stopped")
        except Exception as e:
            print(f"Error stopping IDS controller: {e}")
            
    def generate_test_report(self):
        """Generate test report with packet capture and ML analysis results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"logs/packet_analysis/syn_test_report_{timestamp}.log"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        report = {
            "test_timestamp": datetime.now().isoformat(),
            "test_type": "SYN_PACKET_GENERATION_AND_CAPTURE",
            "configuration": {
                "bpf_filter": self.settings.network.bpf_filter,
                "interface": self.settings.network.interface,
                "detection_threshold": self.settings.detection.prob_threshold
            },
            "results": {
                "packets_captured": len(self.captured_packets),
                "ml_analyses_performed": len(self.ml_analyses),
                "capture_success": len(self.captured_packets) > 0,
                "ml_success": len(self.ml_analyses) > 0
            },
            "captured_packets": self.captured_packets,
            "ml_analyses": self.ml_analyses
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"Test report generated: {report_file}")
        print(f"Packets captured: {len(self.captured_packets)}")
        print(f"ML analyses: {len(self.ml_analyses)}")
        
        return report_file

def main():
    """Main test function."""
    print("=== SCADA-IDS-KC SYN Packet Generation and Capture Test ===")
    print(f"Test started at: {datetime.now()}")
    
    # Initialize test components
    test = PacketCaptureTest()
    generator = SynTrafficGenerator(target_port=80, packet_count=30)
    
    try:
        # Setup packet capture
        test.setup()
        
        # Start packet capture
        if not test.start_capture():
            print("FAILED: Could not start packet capture")
            return 1
            
        # Wait a moment for capture to stabilize
        print("Waiting 2 seconds for capture to stabilize...")
        time.sleep(2)
        
        # Generate SYN packets in background thread
        print("Starting SYN packet generation thread...")
        generator_thread = threading.Thread(target=generator.generate_syn_packets)
        generator_thread.daemon = True
        generator_thread.start()
        
        # Let packets generate and capture for 10 seconds
        print("Running packet capture for 10 seconds...")
        time.sleep(10)
        
        # Stop packet generation
        generator.stop()
        generator_thread.join(timeout=2)
        
        # Wait a bit more for any pending packets
        print("Waiting for pending packets...")
        time.sleep(3)
        
        # Stop packet capture
        test.stop_capture()
        
        # Generate test report
        report_file = test.generate_test_report()
        
        # Print summary
        print("\n=== TEST SUMMARY ===")
        print(f"SYN packets sent: {generator.packets_sent}")
        print(f"Packets captured: {len(test.captured_packets)}")
        print(f"ML analyses: {len(test.ml_analyses)}")
        print(f"Report file: {report_file}")
        
        if len(test.captured_packets) > 0:
            print("✅ SUCCESS: Packets were captured!")
            print("Sample captured packet:")
            print(json.dumps(test.captured_packets[0], indent=2))
        else:
            print("❌ FAILURE: No packets were captured")
            
        return 0 if len(test.captured_packets) > 0 else 1
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Cleanup
        try:
            generator.stop()
            test.stop_capture()
        except:
            pass

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)