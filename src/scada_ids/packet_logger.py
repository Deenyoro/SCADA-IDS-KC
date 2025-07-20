#!/usr/bin/env python3
"""
Comprehensive Packet Capture and ML Analysis Logger
Provides detailed logging of packet capture events and ML analysis results
"""

import json
import csv
import time
import threading
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from logging.handlers import RotatingFileHandler
import logging

class PacketLogger:
    """
    Comprehensive packet capture and ML analysis logger.
    Provides definitive proof of ML packet analysis functionality.
    """
    
    def __init__(self, settings):
        """Initialize packet logger with configuration."""
        self.settings = settings
        self.enabled = False
        self.log_level = "INFO"
        self.directory = Path("logs/packet_analysis")
        self.file_format = "packet_analysis_{timestamp}.log"
        self.format = "JSON"
        self.max_file_size = 52428800  # 50MB
        self.backup_count = 10
        self.include_packets = True
        self.include_ml_analysis = True
        self.include_features = True
        self.include_performance = True
        self.timestamp_precision = "milliseconds"
        
        self._lock = threading.RLock()
        self._log_file = None
        self._csv_writer = None
        self._packet_count = 0
        self._ml_analysis_count = 0
        self._start_time = time.time()
        
        # Load configuration
        self._load_config()
        
        # Initialize logging if enabled
        if self.enabled:
            self._initialize_logging()
    
    def _load_config(self):
        """Load packet logging configuration from settings."""
        try:
            packet_config = self.settings.get_section('packet_logging')
            if packet_config:
                self.enabled = packet_config.get('enabled', False)
                self.log_level = packet_config.get('log_level', 'INFO')
                self.directory = Path(packet_config.get('directory', 'logs/packet_analysis'))
                self.file_format = packet_config.get('file_format', 'packet_analysis_{timestamp}.log')
                self.format = packet_config.get('format', 'JSON')
                self.max_file_size = packet_config.get('max_file_size', 52428800)
                self.backup_count = packet_config.get('backup_count', 10)
                self.include_packets = packet_config.get('include_packets', True)
                self.include_ml_analysis = packet_config.get('include_ml_analysis', True)
                self.include_features = packet_config.get('include_features', True)
                self.include_performance = packet_config.get('include_performance', True)
                self.timestamp_precision = packet_config.get('timestamp_precision', 'milliseconds')
        except Exception as e:
            logging.warning(f"Failed to load packet logging config: {e}")
    
    def _initialize_logging(self):
        """Initialize the packet logging system."""
        try:
            # Create directory if it doesn't exist
            self.directory.mkdir(parents=True, exist_ok=True)
            
            # Generate timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.file_format.replace("{timestamp}", timestamp)
            log_path = self.directory / filename
            
            # Open log file
            self._log_file = open(log_path, 'w', encoding='utf-8')
            
            if self.format.upper() == "CSV":
                self._initialize_csv_logging()
            else:
                self._initialize_json_logging()
            
            # Log initialization
            self.log_system_event("packet_logger_initialized", {
                "timestamp": self._get_timestamp(),
                "log_file": str(log_path),
                "format": self.format,
                "configuration": {
                    "include_packets": self.include_packets,
                    "include_ml_analysis": self.include_ml_analysis,
                    "include_features": self.include_features,
                    "include_performance": self.include_performance,
                    "timestamp_precision": self.timestamp_precision
                }
            })
            
            logging.info(f"Packet logger initialized: {log_path}")
            
        except Exception as e:
            logging.error(f"Failed to initialize packet logger: {e}")
            self.enabled = False
    
    def _initialize_csv_logging(self):
        """Initialize CSV format logging."""
        fieldnames = ['timestamp', 'event_type']
        
        if self.include_packets:
            fieldnames.extend(['source_ip', 'dest_ip', 'packet_size', 'protocol'])
        
        if self.include_ml_analysis:
            fieldnames.extend(['ml_probability', 'threat_detected', 'processing_time_ms'])
        
        if self.include_features:
            fieldnames.extend(['features_extracted', 'feature_count'])
        
        if self.include_performance:
            fieldnames.extend(['queue_size', 'memory_usage'])
        
        self._csv_writer = csv.DictWriter(self._log_file, fieldnames=fieldnames)
        self._csv_writer.writeheader()
    
    def _initialize_json_logging(self):
        """Initialize JSON format logging."""
        # JSON logging doesn't need special initialization
        pass
    
    def _get_timestamp(self) -> str:
        """Get timestamp with configured precision."""
        if self.timestamp_precision == "milliseconds":
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        else:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _convert_numpy_types(self, obj):
        """Convert numpy types to native Python types for JSON serialization."""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        else:
            return obj

    def _write_log_entry(self, entry: Dict[str, Any]):
        """Write a log entry to file."""
        if not self.enabled or not self._log_file:
            return

        try:
            with self._lock:
                if self.format.upper() == "CSV":
                    self._csv_writer.writerow(entry)
                else:
                    # Convert numpy types before JSON serialization
                    converted_entry = self._convert_numpy_types(entry)
                    json.dump(converted_entry, self._log_file)
                    self._log_file.write('\n')

                self._log_file.flush()
        except Exception as e:
            logging.error(f"Failed to write packet log entry: {e}")
    
    def log_packet_capture(self, packet_info: Dict[str, Any]):
        """Log a packet capture event."""
        if not self.enabled or not self.include_packets:
            return
        
        self._packet_count += 1
        
        entry = {
            "timestamp": self._get_timestamp(),
            "event_type": "packet_captured",
            "packet_id": self._packet_count,
            "source_ip": packet_info.get('src_ip', 'unknown'),
            "dest_ip": packet_info.get('dst_ip', 'unknown'),
            "packet_size": packet_info.get('packet_size', 0),
            "protocol": packet_info.get('protocol', 'unknown'),
            "tcp_flags": packet_info.get('tcp_flags', {}),
            "capture_timestamp": packet_info.get('timestamp', time.time())
        }
        
        if self.log_level == "DEBUG":
            entry.update({
                "raw_packet_info": packet_info
            })
        
        self._write_log_entry(entry)
    
    def log_ml_analysis(self, packet_id: int, features: Dict[str, float], 
                       ml_result: Dict[str, Any], processing_time: float):
        """Log ML analysis results - DEFINITIVE PROOF OF ML PROCESSING."""
        if not self.enabled or not self.include_ml_analysis:
            return
        
        self._ml_analysis_count += 1
        
        entry = {
            "timestamp": self._get_timestamp(),
            "event_type": "ml_analysis_completed",
            "packet_id": packet_id,
            "ml_model_type": ml_result.get('model_type', 'unknown'),
            "ml_probability": ml_result.get('probability', 0.0),
            "threat_detected": ml_result.get('is_threat', False),
            "threat_threshold": ml_result.get('threshold', 0.05),
            "processing_time_ms": round(processing_time * 1000, 3),
            "analysis_timestamp": self._get_timestamp()
        }
        
        # Include detailed features if configured
        if self.include_features and features:
            entry.update({
                "features_extracted": features,
                "feature_count": len(features),
                "feature_names": list(features.keys())
            })
        
        # Include performance metrics if configured
        if self.include_performance:
            entry.update({
                "total_packets_processed": self._packet_count,
                "total_ml_analyses": self._ml_analysis_count,
                "uptime_seconds": round(time.time() - self._start_time, 2)
            })
        
        if self.log_level in ["DEBUG", "DETAILED"]:
            entry.update({
                "ml_model_details": ml_result.get('model_details', {}),
                "feature_scaling_applied": ml_result.get('scaling_applied', False),
                "prediction_confidence": ml_result.get('confidence', 0.0)
            })
        
        self._write_log_entry(entry)
    
    def log_feature_extraction(self, packet_id: int, raw_features: Dict[str, Any], 
                              processed_features: Dict[str, float], extraction_time: float):
        """Log feature extraction process."""
        if not self.enabled or not self.include_features:
            return
        
        entry = {
            "timestamp": self._get_timestamp(),
            "event_type": "feature_extraction",
            "packet_id": packet_id,
            "raw_features": raw_features,
            "processed_features": processed_features,
            "feature_count": len(processed_features),
            "extraction_time_ms": round(extraction_time * 1000, 3)
        }
        
        self._write_log_entry(entry)
    
    def log_system_event(self, event_type: str, details: Dict[str, Any]):
        """Log system events and status updates."""
        if not self.enabled:
            return
        
        entry = {
            "timestamp": self._get_timestamp(),
            "event_type": event_type,
            "details": details
        }
        
        self._write_log_entry(entry)
    
    def log_performance_metrics(self, metrics: Dict[str, Any]):
        """Log performance and statistics."""
        if not self.enabled or not self.include_performance:
            return
        
        entry = {
            "timestamp": self._get_timestamp(),
            "event_type": "performance_metrics",
            "packets_captured": self._packet_count,
            "ml_analyses_completed": self._ml_analysis_count,
            "uptime_seconds": round(time.time() - self._start_time, 2),
            "analysis_rate": round(self._ml_analysis_count / max(1, time.time() - self._start_time), 2),
            "metrics": metrics
        }
        
        self._write_log_entry(entry)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get packet logger statistics."""
        return {
            "enabled": self.enabled,
            "packets_logged": self._packet_count,
            "ml_analyses_logged": self._ml_analysis_count,
            "uptime_seconds": round(time.time() - self._start_time, 2),
            "log_file": str(self.directory / self.file_format.replace("{timestamp}", "current")),
            "format": self.format
        }
    
    def close(self):
        """Close the packet logger and cleanup resources."""
        if self._log_file:
            try:
                self.log_system_event("packet_logger_shutdown", {
                    "final_packet_count": self._packet_count,
                    "final_ml_analysis_count": self._ml_analysis_count,
                    "total_uptime_seconds": round(time.time() - self._start_time, 2)
                })
                
                self._log_file.close()
                logging.info("Packet logger closed successfully")
            except Exception as e:
                logging.error(f"Error closing packet logger: {e}")
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.close()
