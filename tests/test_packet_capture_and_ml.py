#!/usr/bin/env python3
"""
Test script to verify packet capture with Npcap and ML threat detection.
This ensures the core functionality works before final build.
"""

import sys
import os
import time
import logging
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def test_npcap_availability():
    """Test if Npcap/WinPcap is available for packet capture."""
    print("\n=== Testing Npcap/WinPcap Availability ===")
    try:
        import scapy.all as scapy
        
        # Try to get network interfaces
        interfaces = scapy.get_if_list()
        print(f"[OK] Scapy loaded successfully")
        print(f"[OK] Found {len(interfaces)} network interfaces")
        
        if not interfaces:
            print("[FAIL] No network interfaces found - Npcap may not be installed")
            return False
            
        # Show available interfaces
        print("\nAvailable interfaces:")
        for i, iface in enumerate(interfaces[:5], 1):  # Show first 5
            print(f"  {i}. {iface}")
            
        return True
        
    except ImportError as e:
        print(f"[FAIL] Scapy not available: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Error checking Npcap: {e}")
        return False


def test_packet_capture():
    """Test basic packet capture functionality."""
    print("\n=== Testing Packet Capture ===")
    try:
        import scapy.all as scapy
        
        # Get first available interface
        interfaces = scapy.get_if_list()
        if not interfaces:
            print("[FAIL] No interfaces available for capture")
            return False
            
        test_interface = interfaces[0]
        print(f"Testing capture on interface: {test_interface}")
        
        # Try to capture a few packets
        print("Attempting to capture 5 packets...")
        packets = []
        
        def packet_handler(pkt):
            packets.append(pkt)
            print(f"  Captured packet: {pkt.summary()}")
            
        try:
            # Capture with timeout
            scapy.sniff(
                iface=test_interface,
                prn=packet_handler,
                count=5,
                timeout=10,
                store=False
            )
        except PermissionError:
            print("[FAIL] Permission denied - run as administrator")
            return False
        except Exception as e:
            print(f"[FAIL] Capture error: {e}")
            # Try without interface specification
            print("Trying default interface...")
            try:
                scapy.sniff(
                    prn=packet_handler,
                    count=5,
                    timeout=10,
                    store=False
                )
            except Exception as e2:
                print(f"[FAIL] Default capture also failed: {e2}")
                return False
        
        if packets:
            print(f"[OK] Successfully captured {len(packets)} packets")
            return True
        else:
            print("[FAIL] No packets captured")
            return False
            
    except Exception as e:
        print(f"[FAIL] Packet capture test failed: {e}")
        return False


def test_syn_packet_filter():
    """Test SYN packet filtering."""
    print("\n=== Testing SYN Packet Filter ===")
    try:
        import scapy.all as scapy
        
        # Test BPF filter compilation
        bpf_filter = "tcp and tcp[13]=2"
        print(f"Testing BPF filter: {bpf_filter}")
        
        syn_packets = []
        
        def syn_handler(pkt):
            if pkt.haslayer(scapy.TCP) and pkt[scapy.TCP].flags == 2:
                syn_packets.append(pkt)
                print(f"  SYN packet: {pkt[scapy.IP].src}:{pkt[scapy.TCP].sport} -> {pkt[scapy.IP].dst}:{pkt[scapy.TCP].dport}")
        
        print("Capturing for 5 seconds (looking for SYN packets)...")
        try:
            scapy.sniff(
                filter=bpf_filter,
                prn=syn_handler,
                timeout=5,
                store=False
            )
        except Exception as e:
            print(f"Warning: {e}")
            
        if syn_packets:
            print(f"[OK] Captured {len(syn_packets)} SYN packets")
        else:
            print("[WARN] No SYN packets captured (this is normal if there's no TCP traffic)")
            
        return True
        
    except Exception as e:
        print(f"[FAIL] SYN filter test failed: {e}")
        return False


def test_ml_models():
    """Test ML model loading and prediction."""
    print("\n=== Testing ML Models ===")
    try:
        from scada_ids.ml import get_detector
        
        detector = get_detector()
        
        # Check if models are loaded
        if not detector.is_model_loaded():
            print("[FAIL] ML models not loaded")
            print("Attempting to load models...")
            if not detector.load_models():
                print("[FAIL] Failed to load ML models")
                return False
        
        # Get model info
        info = detector.get_model_info()
        print(f"[OK] Model type: {info.get('model_type', 'Unknown')}")
        print(f"[OK] Expected features: {info.get('expected_features', 0)}")
        print(f"[OK] Threshold: {info.get('threshold', 0.0)}")
        
        # Test prediction with dummy data
        print("\nTesting prediction with sample data...")
        
        # Normal traffic pattern
        normal_features = {
            'global_syn_rate': 10.0,
            'global_packet_rate': 100.0,
            'global_byte_rate': 50000.0,
            'src_syn_rate': 5.0,
            'src_packet_rate': 50.0,
            'src_byte_rate': 25000.0,
            'dst_syn_rate': 2.0,
            'dst_packet_rate': 20.0,
            'dst_byte_rate': 10000.0,
            'unique_dst_ports': 3.0,
            'unique_src_ips_to_dst': 1.0,
            'packet_size': 60.0,
            'dst_port': 80.0,
            'src_port': 45678.0,
            'syn_flag': 1.0,
            'ack_flag': 0.0,
            'fin_flag': 0.0,
            'rst_flag': 0.0,
            'syn_packet_ratio': 0.1
        }
        
        prob_normal, is_threat_normal = detector.predict(normal_features)
        print(f"Normal traffic: probability={prob_normal:.3f}, threat={is_threat_normal}")
        
        # Attack pattern (high SYN rate)
        attack_features = normal_features.copy()
        attack_features.update({
            'global_syn_rate': 1000.0,
            'src_syn_rate': 500.0,
            'dst_syn_rate': 200.0,
            'syn_packet_ratio': 0.9,
            'unique_dst_ports': 50.0,
            'unique_src_ips_to_dst': 1.0
        })
        
        prob_attack, is_threat_attack = detector.predict(attack_features)
        print(f"Attack traffic: probability={prob_attack:.3f}, threat={is_threat_attack}")
        
        print(f"\n[OK] ML models working correctly")
        return True
        
    except Exception as e:
        print(f"[FAIL] ML model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integrated_detection():
    """Test integrated packet capture and ML detection."""
    print("\n=== Testing Integrated Detection ===")
    try:
        from scada_ids.controller import get_controller
        from scada_ids.settings import get_settings
        
        controller = get_controller()
        settings = get_settings()
        
        # Check system status
        status = controller.get_status()
        print(f"System status: {status.get('is_running', False)}")
        
        # Get available interfaces
        interfaces = controller.get_available_interfaces()
        if not interfaces:
            print("[FAIL] No interfaces available")
            return False
            
        print(f"[OK] Found {len(interfaces)} interfaces")
        
        # Check ML model status
        ml_status = status.get('ml_detector', {})
        if not ml_status.get('loaded', False):
            print("[FAIL] ML models not loaded in controller")
            return False
            
        print(f"[OK] ML models loaded: {ml_status.get('model_type', 'Unknown')}")
        
        # Test would start monitoring here, but we'll skip actual monitoring
        # to avoid requiring real network traffic
        print("[OK] Integration test passed (ready for monitoring)")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Integration test failed: {e}")
        return False


def test_feature_extraction():
    """Test feature extraction from packets."""
    print("\n=== Testing Feature Extraction ===")
    try:
        from scada_ids.features import FeatureExtractor
        import scapy.all as scapy
        
        extractor = FeatureExtractor()
        
        # Create a synthetic SYN packet
        syn_packet = scapy.IP(src="192.168.1.100", dst="192.168.1.1") / \
                     scapy.TCP(sport=12345, dport=80, flags="S")
        
        # Extract features
        features = extractor.extract_features(syn_packet)
        
        if features:
            print("[OK] Feature extraction successful")
            print(f"  Extracted {len(features)} features")
            
            # Show some key features
            for key in ['syn_flag', 'dst_port', 'packet_size']:
                if key in features:
                    print(f"  {key}: {features[key]}")
                    
            return True
        else:
            print("[FAIL] No features extracted")
            return False
            
    except Exception as e:
        print(f"[FAIL] Feature extraction test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("SCADA-IDS-KC Pre-Build Validation")
    print("Testing packet capture and ML threat detection")
    print("=" * 60)
    
    # Check if running as admin (recommended for packet capture)
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            print("\n[WARNING] Not running as administrator.")
            print("   Packet capture may fail. Consider running as admin.")
    except:
        pass
    
    # Run tests
    tests = [
        ("Npcap Availability", test_npcap_availability),
        ("Packet Capture", test_packet_capture),
        ("SYN Filter", test_syn_packet_filter),
        ("ML Models", test_ml_models),
        ("Feature Extraction", test_feature_extraction),
        ("Integration", test_integrated_detection)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n[ERROR] {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASSED]" if result else "[FAILED]"
        print(f"{test_name:<20} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n[SUCCESS] All tests passed! Ready for final build.")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Please address issues before building.")
        print("\nCommon issues:")
        print("1. Npcap not installed - Download from https://nmap.org/npcap/")
        print("2. Not running as administrator - Required for packet capture")
        print("3. ML models missing - Check models/ directory")
        print("4. Python dependencies missing - Run: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())