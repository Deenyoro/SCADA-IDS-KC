"""
Tests for feature extraction module
"""

import pytest
import time
from unittest.mock import patch

from scada_ids.features import SlidingWindowCounter, FeatureExtractor


class TestSlidingWindowCounter:
    """Test SlidingWindowCounter class."""
    
    def test_initialization(self):
        """Test counter initialization."""
        counter = SlidingWindowCounter(60)
        assert counter.window_seconds == 60
        assert len(counter.events) == 0
    
    def test_add_event(self):
        """Test adding events to counter."""
        counter = SlidingWindowCounter(60)
        timestamp = time.time()
        
        counter.add_event(timestamp, 1.0)
        assert counter.get_count(timestamp) == 1
        assert counter.get_sum(timestamp) == 1.0
    
    def test_window_cleanup(self):
        """Test that old events are cleaned up."""
        counter = SlidingWindowCounter(60)
        current_time = time.time()
        
        # Add old event (outside window)
        counter.add_event(current_time - 120, 1.0)
        # Add recent event (inside window)
        counter.add_event(current_time - 30, 2.0)
        
        # Only recent event should remain
        assert counter.get_count(current_time) == 1
        assert counter.get_sum(current_time) == 2.0
    
    def test_get_rate(self):
        """Test rate calculation."""
        counter = SlidingWindowCounter(60)
        current_time = time.time()
        
        # Add 3 events in window
        counter.add_event(current_time - 30, 1.0)
        counter.add_event(current_time - 20, 1.0)
        counter.add_event(current_time - 10, 1.0)
        
        rate = counter.get_rate(current_time)
        assert rate == 3.0 / 60.0  # 3 events per 60 seconds


class TestFeatureExtractor:
    """Test FeatureExtractor class."""
    
    def test_initialization(self, mock_settings):
        """Test feature extractor initialization."""
        with patch('scada_ids.features.get_settings', return_value=mock_settings):
            extractor = FeatureExtractor()
            assert extractor.window_seconds == mock_settings.detection.window_seconds
    
    def test_extract_features_basic(self, mock_settings, mock_packet_info):
        """Test basic feature extraction."""
        with patch('scada_ids.features.get_settings', return_value=mock_settings):
            extractor = FeatureExtractor()
            features = extractor.extract_features(mock_packet_info)
            
            # Check that all expected features are present
            expected_features = extractor.get_feature_names()
            for feature_name in expected_features:
                assert feature_name in features
                assert isinstance(features[feature_name], (int, float))
    
    def test_extract_features_syn_packet(self, mock_settings, mock_packet_info):
        """Test feature extraction for SYN packet."""
        with patch('scada_ids.features.get_settings', return_value=mock_settings):
            extractor = FeatureExtractor()
            
            # Ensure packet has SYN flag
            mock_packet_info['flags'] = 0x02  # SYN flag
            features = extractor.extract_features(mock_packet_info)
            
            assert features['syn_flag'] == 1.0
            assert features['ack_flag'] == 0.0
            assert features['packet_size'] == float(mock_packet_info['packet_size'])
    
    def test_extract_features_multiple_packets(self, mock_settings, mock_packet_info):
        """Test feature extraction with multiple packets."""
        with patch('scada_ids.features.get_settings', return_value=mock_settings):
            extractor = FeatureExtractor()
            
            # Process multiple packets
            for i in range(5):
                packet = mock_packet_info.copy()
                packet['timestamp'] = time.time() + i
                packet['src_port'] = 12345 + i
                features = extractor.extract_features(packet)
            
            # Rates should increase with more packets
            assert features['global_syn_rate'] > 0
            assert features['src_syn_rate'] > 0
    
    def test_feature_names_consistency(self, mock_settings):
        """Test that feature names are consistent."""
        with patch('scada_ids.features.get_settings', return_value=mock_settings):
            extractor = FeatureExtractor()
            feature_names = extractor.get_feature_names()
            
            # Check expected number of features
            assert len(feature_names) == 20
            
            # Check some key features are present
            assert 'global_syn_rate' in feature_names
            assert 'src_syn_rate' in feature_names
            assert 'dst_syn_rate' in feature_names
            assert 'syn_flag' in feature_names
            assert 'packet_size' in feature_names
    
    def test_reset_counters(self, mock_settings):
        """Test counter reset functionality."""
        with patch('scada_ids.features.get_settings', return_value=mock_settings):
            extractor = FeatureExtractor()
            
            # Add some data
            packet_info = {
                'timestamp': time.time(),
                'src_ip': '192.168.1.100',
                'dst_ip': '192.168.1.1',
                'src_port': 12345,
                'dst_port': 80,
                'flags': 0x02,
                'packet_size': 64
            }
            extractor.extract_features(packet_info)
            
            # Reset counters
            extractor.reset_counters()
            
            # Verify counters are reset
            features = extractor.extract_features(packet_info)
            # After reset, rates should be low (only one packet)
            assert features['global_syn_rate'] <= 1.0 / mock_settings.detection.window_seconds
    
    def test_port_diversity_tracking(self, mock_settings):
        """Test port diversity feature tracking."""
        with patch('scada_ids.features.get_settings', return_value=mock_settings):
            extractor = FeatureExtractor()
            
            src_ip = '192.168.1.100'
            dst_ip = '192.168.1.1'
            current_time = time.time()
            
            # Send packets to different ports from same source
            for port in [80, 443, 8080, 3389]:
                packet_info = {
                    'timestamp': current_time,
                    'src_ip': src_ip,
                    'dst_ip': dst_ip,
                    'src_port': 12345,
                    'dst_port': port,
                    'flags': 0x02,
                    'packet_size': 64
                }
                features = extractor.extract_features(packet_info)
            
            # Should track unique destination ports
            assert features['unique_dst_ports'] == 4
    
    def test_flag_analysis(self, mock_settings):
        """Test TCP flag analysis."""
        with patch('scada_ids.features.get_settings', return_value=mock_settings):
            extractor = FeatureExtractor()
            
            # Test different flag combinations
            flag_tests = [
                (0x02, {'syn_flag': 1.0, 'ack_flag': 0.0, 'fin_flag': 0.0, 'rst_flag': 0.0}),  # SYN
                (0x10, {'syn_flag': 0.0, 'ack_flag': 1.0, 'fin_flag': 0.0, 'rst_flag': 0.0}),  # ACK
                (0x01, {'syn_flag': 0.0, 'ack_flag': 0.0, 'fin_flag': 1.0, 'rst_flag': 0.0}),  # FIN
                (0x04, {'syn_flag': 0.0, 'ack_flag': 0.0, 'fin_flag': 0.0, 'rst_flag': 1.0}),  # RST
                (0x12, {'syn_flag': 1.0, 'ack_flag': 1.0, 'fin_flag': 0.0, 'rst_flag': 0.0}),  # SYN+ACK
            ]
            
            for flags, expected in flag_tests:
                packet_info = {
                    'timestamp': time.time(),
                    'src_ip': '192.168.1.100',
                    'dst_ip': '192.168.1.1',
                    'src_port': 12345,
                    'dst_port': 80,
                    'flags': flags,
                    'packet_size': 64
                }
                features = extractor.extract_features(packet_info)
                
                for flag_name, expected_value in expected.items():
                    assert features[flag_name] == expected_value
