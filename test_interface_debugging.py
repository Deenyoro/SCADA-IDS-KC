#!/usr/bin/env python3
"""
Test script for enhanced interface debugging functionality.
Tests the specific failing interface GUID: {0B10AE12-DD02-4872-8CFF-BCAB42628D17}
"""

import sys
import logging
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from scada_ids.capture import PacketSniffer
from scada_ids.settings import get_settings

def setup_debug_logging():
    """Setup DEBUG level logging to see all interface debugging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('interface_debug_test.log', mode='w')
        ]
    )

def test_interface_debugging():
    """Test the enhanced interface debugging functionality."""
    print("=== SCADA-IDS-KC Interface Debugging Test ===")
    print("Testing interface GUID: {0B10AE12-DD02-4872-8CFF-BCAB42628D17}")
    print()
    
    # Setup debug logging
    setup_debug_logging()
    
    # Create packet sniffer
    print("1. Creating PacketSniffer instance...")
    sniffer = PacketSniffer()
    
    print(f"2. Available interfaces found: {len(sniffer.interfaces)}")
    for i, iface in enumerate(sniffer.interfaces):
        print(f"   {i+1}. {iface}")
    
    print("\n3. Getting interfaces with friendly names...")
    interfaces_with_names = sniffer.get_interfaces_with_names()
    for iface_info in interfaces_with_names:
        print(f"   GUID: {iface_info['guid']}")
        print(f"   Name: {iface_info['name']}")
        print()
    
    # Test the specific failing interface
    test_interface = "{0B10AE12-DD02-4872-8CFF-BCAB42628D17}"
    print(f"4. Testing specific interface: {test_interface}")
    
    # Test interface validation
    print("5. Validating interface capabilities...")
    validation_result = sniffer.validate_interface_capabilities(test_interface)
    
    print("Validation Results:")
    print(f"   Exists: {validation_result['exists']}")
    print(f"   Accessible: {validation_result['accessible']}")
    print(f"   Has Address: {validation_result['has_address']}")
    print(f"   Address: {validation_result['address']}")
    print(f"   Supports Promiscuous: {validation_result['supports_promiscuous']}")
    print(f"   Can Capture: {validation_result['can_capture']}")
    
    if validation_result['errors']:
        print("   Errors:")
        for error in validation_result['errors']:
            print(f"     - {error}")
    
    if validation_result['warnings']:
        print("   Warnings:")
        for warning in validation_result['warnings']:
            print(f"     - {warning}")
    
    # Test setting the interface
    print(f"\n6. Testing set_interface with: {test_interface}")
    success = sniffer.set_interface(test_interface)
    print(f"   Set interface result: {success}")
    
    # Test variations of the interface GUID
    print("\n7. Testing GUID variations...")
    variations = [
        "{0B10AE12-DD02-4872-8CFF-BCAB42628D17}",  # Original
        "0B10AE12-DD02-4872-8CFF-BCAB42628D17",    # No braces
        "{0b10ae12-dd02-4872-8cff-bcab42628d17}",  # Lowercase with braces
        "0b10ae12-dd02-4872-8cff-bcab42628d17",    # Lowercase no braces
    ]
    
    for variation in variations:
        print(f"   Testing variation: {variation}")
        result = sniffer.set_interface(variation)
        print(f"   Result: {result}")
    
    print("\n8. Test complete. Check 'interface_debug_test.log' for detailed debug output.")

if __name__ == "__main__":
    test_interface_debugging()
