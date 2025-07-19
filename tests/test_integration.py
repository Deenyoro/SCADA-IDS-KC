"""
Integration tests for SCADA-IDS-KC components
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from queue import Queue

from scada_ids.controller import IDSController
from scada_ids.capture import PacketSniffer
from scada_ids.features import FeatureExtractor
from scada_ids.ml import MLDetector


@pytest.mark.integration
class TestIDSControllerIntegration:
    """Integration tests for IDS Controller."""
    
    @pytest.fixture
    def mock_dependencies(self, mock_settings, mock_scapy, mock_ml_models, mock_notifications):
        """Mock all external dependencies for integration testing."""
        with patch('scada_ids.controller.get_settings', return_value=mock_settings), \
             patch('scada_ids.capture.scapy', mock_scapy), \
             patch('scada_ids.ml.joblib') as mock_joblib:
            
            # Mock joblib to return our test models
            mock_joblib.load.side_effect = [mock_ml_models['classifier'], mock_ml_models['scaler']]
            
            yield {
                'settings': mock_settings,
                'scapy': mock_scapy,
                'ml_models': mock_ml_models,
                'notifications': mock_notifications,
                'joblib': mock_joblib
            }
    
    def test_controller_initialization(self, mock_dependencies):
        """Test that controller initializes all components correctly."""
        controller = IDSController()
        
        assert controller.packet_sniffer is not None
        assert controller.feature_extractor is not None
        assert controller.ml_detector is not None
        assert controller.notification_manager is not None
        assert controller.is_running is False
    
    def test_start_stop_workflow(self, mock_dependencies):
        """Test complete start-stop workflow."""
        controller = IDSController()
        
        # Mock system ready state
        with patch.object(controller, 'is_system_ready', return_value=True):
            # Start monitoring
            result = controller.start('test_interface')
            assert result is True
            assert controller.is_running is True
            
            # Give it a moment to start
            time.sleep(0.1)
            
            # Stop monitoring
            controller.stop()
            assert controller.is_running is False
    
    def test_packet_processing_pipeline(self, mock_dependencies):
        """Test the complete packet processing pipeline."""
        status_updates = []
        
        def status_callback(event_type, data):
            status_updates.append((event_type, data))
        
        controller = IDSController(status_callback=status_callback)
        
        # Mock high-probability attack prediction
        mock_dependencies['ml_models']['classifier'].predict_proba.return_value = [[0.1, 0.9]]
        
        # Simulate packet processing
        packet_info = {
            'timestamp': time.time(),
            'src_ip': '192.168.1.100',
            'dst_ip': '192.168.1.1',
            'src_port': 12345,
            'dst_port': 80,
            'flags': 0x02,
            'packet_size': 64
        }
        
        # Process packet through the pipeline
        controller._handle_packet(packet_info)
        
        # Extract features
        features = controller.feature_extractor.extract_features(packet_info)
        
        # Make prediction
        probability, is_attack = controller.ml_detector.predict(features)
        
        assert probability == 0.9
        assert is_attack is True
        
        # Simulate attack handling
        controller._handle_attack(packet_info, probability, features)
        
        # Verify statistics were updated
        stats = controller.get_statistics()
        assert stats['packets_captured'] == 1
        assert stats['attacks_detected'] == 1
    
    def test_statistics_tracking(self, mock_dependencies):
        """Test statistics tracking across multiple packets."""
        controller = IDSController()
        
        # Process multiple packets
        for i in range(10):
            packet_info = {
                'timestamp': time.time() + i * 0.1,
                'src_ip': f'192.168.1.{100 + i}',
                'dst_ip': '192.168.1.1',
                'src_port': 12345 + i,
                'dst_port': 80,
                'flags': 0x02,
                'packet_size': 64
            }
            controller._handle_packet(packet_info)
        
        stats = controller.get_statistics()
        assert stats['packets_captured'] == 10
        assert 'runtime_seconds' in stats
        assert 'current_interface' in stats
    
    def test_interface_management(self, mock_dependencies):
        """Test network interface management."""
        controller = IDSController()
        
        # Get available interfaces
        interfaces = controller.get_available_interfaces()
        assert 'test_interface' in interfaces
        
        # Set interface
        result = controller.set_interface('test_interface')
        assert result is True
        
        # Try invalid interface
        result = controller.set_interface('invalid_interface')
        assert result is False


@pytest.mark.integration
class TestPacketCaptureIntegration:
    """Integration tests for packet capture component."""
    
    def test_packet_sniffer_with_callback(self, mock_scapy):
        """Test packet sniffer with callback integration."""
        captured_packets = []
        
        def packet_callback(packet_info):
            captured_packets.append(packet_info)
        
        sniffer = PacketSniffer(packet_callback=packet_callback)
        
        # Mock packet data
        mock_packet_info = {
            'timestamp': time.time(),
            'src_ip': '192.168.1.100',
            'dst_ip': '192.168.1.1',
            'src_port': 12345,
            'dst_port': 80,
            'flags': 0x02,
            'packet_size': 64
        }
        
        # Simulate packet capture
        sniffer._packet_handler(Mock())  # Mock scapy packet
        
        # Manually add to queue for testing
        sniffer.packet_queue.put(mock_packet_info)
        
        # Verify packet was queued
        assert sniffer.get_packet_count() == 1


@pytest.mark.integration
class TestFeatureMLIntegration:
    """Integration tests for feature extraction and ML components."""
    
    def test_feature_extraction_to_ml_prediction(self, mock_settings, mock_ml_models):
        """Test complete feature extraction to ML prediction pipeline."""
        with patch('scada_ids.features.get_settings', return_value=mock_settings), \
             patch('scada_ids.ml.get_settings', return_value=mock_settings), \
             patch('scada_ids.ml.joblib.load') as mock_load:
            
            # Setup ML models
            mock_load.side_effect = [mock_ml_models['classifier'], mock_ml_models['scaler']]
            
            # Create components
            feature_extractor = FeatureExtractor()
            ml_detector = MLDetector()
            
            # Process packet
            packet_info = {
                'timestamp': time.time(),
                'src_ip': '192.168.1.100',
                'dst_ip': '192.168.1.1',
                'src_port': 12345,
                'dst_port': 80,
                'flags': 0x02,
                'packet_size': 64
            }
            
            # Extract features
            features = feature_extractor.extract_features(packet_info)
            
            # Verify all expected features are present
            expected_features = feature_extractor.get_feature_names()
            for feature_name in expected_features:
                assert feature_name in features
            
            # Make ML prediction
            probability, is_attack = ml_detector.predict(features)
            
            # Verify prediction was made
            assert isinstance(probability, float)
            assert isinstance(is_attack, bool)
            assert 0.0 <= probability <= 1.0


@pytest.mark.integration
@pytest.mark.slow
class TestEndToEndWorkflow:
    """End-to-end integration tests."""
    
    def test_complete_detection_workflow(self, mock_settings, mock_scapy, mock_ml_models, mock_notifications):
        """Test complete detection workflow from packet to alert."""
        with patch('scada_ids.controller.get_settings', return_value=mock_settings), \
             patch('scada_ids.capture.scapy', mock_scapy), \
             patch('scada_ids.ml.joblib') as mock_joblib:
            
            # Setup ML models to detect attack
            mock_ml_models['classifier'].predict_proba.return_value = [[0.1, 0.9]]
            mock_joblib.load.side_effect = [mock_ml_models['classifier'], mock_ml_models['scaler']]
            
            alerts = []
            
            def status_callback(event_type, data):
                if event_type == 'attack_detected':
                    alerts.append(data)
            
            # Create controller
            controller = IDSController(status_callback=status_callback)
            
            # Simulate attack packet
            attack_packet = {
                'timestamp': time.time(),
                'src_ip': '10.0.0.100',  # Attacker IP
                'dst_ip': '192.168.1.1',  # Target IP
                'src_port': 54321,
                'dst_port': 80,
                'flags': 0x02,  # SYN flag
                'packet_size': 64
            }
            
            # Process through complete pipeline
            controller._handle_packet(attack_packet)
            
            # Extract features
            features = controller.feature_extractor.extract_features(attack_packet)
            
            # Make prediction
            probability, is_attack = controller.ml_detector.predict(features)
            
            # Handle attack if detected
            if is_attack:
                controller._handle_attack(attack_packet, probability, features)
            
            # Verify attack was detected and handled
            assert is_attack is True
            assert probability == 0.9
            assert len(alerts) == 1
            assert alerts[0]['src_ip'] == '10.0.0.100'
            assert alerts[0]['probability'] == 0.9
            
            # Verify statistics
            stats = controller.get_statistics()
            assert stats['packets_captured'] == 1
            assert stats['attacks_detected'] == 1
    
    def test_normal_traffic_workflow(self, mock_settings, mock_scapy, mock_ml_models, mock_notifications):
        """Test workflow with normal traffic (no alerts)."""
        with patch('scada_ids.controller.get_settings', return_value=mock_settings), \
             patch('scada_ids.capture.scapy', mock_scapy), \
             patch('scada_ids.ml.joblib') as mock_joblib:
            
            # Setup ML models to detect normal traffic
            mock_ml_models['classifier'].predict_proba.return_value = [[0.9, 0.1]]
            mock_joblib.load.side_effect = [mock_ml_models['classifier'], mock_ml_models['scaler']]
            
            alerts = []
            
            def status_callback(event_type, data):
                if event_type == 'attack_detected':
                    alerts.append(data)
            
            # Create controller
            controller = IDSController(status_callback=status_callback)
            
            # Simulate normal packet
            normal_packet = {
                'timestamp': time.time(),
                'src_ip': '192.168.1.50',
                'dst_ip': '192.168.1.1',
                'src_port': 45678,
                'dst_port': 80,
                'flags': 0x02,  # SYN flag
                'packet_size': 64
            }
            
            # Process through pipeline
            controller._handle_packet(normal_packet)
            features = controller.feature_extractor.extract_features(normal_packet)
            probability, is_attack = controller.ml_detector.predict(features)
            
            # Should not trigger attack handling
            assert is_attack is False
            assert probability == 0.1
            assert len(alerts) == 0
            
            # Verify statistics
            stats = controller.get_statistics()
            assert stats['packets_captured'] == 1
            assert stats['attacks_detected'] == 0
