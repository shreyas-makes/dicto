#!/usr/bin/env python3
"""
Performance Monitor - Comprehensive performance monitoring and optimization for Dicto
This module provides the PerformanceMonitor class that tracks system resources,
implements adaptive optimization, manages battery usage, and provides intelligent caching.
"""

import os
import sys
import time
import threading
import logging
import psutil
import gc
import weakref
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import pickle
from datetime import datetime, timedelta
import hashlib


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    timestamp: float
    cpu_percent: float
    memory_usage: float  # MB
    memory_percent: float
    disk_io_read: int
    disk_io_write: int
    battery_percent: Optional[float] = None
    battery_time_left: Optional[int] = None  # seconds
    power_plugged: Optional[bool] = None
    hotkey_latency: Optional[float] = None  # milliseconds
    transcription_latency: Optional[float] = None  # seconds
    model_load_time: Optional[float] = None  # seconds
    cache_hits: int = 0
    cache_misses: int = 0


@dataclass
class OptimizationSettings:
    """Container for optimization settings."""
    cpu_threshold_high: float = 80.0  # %
    cpu_threshold_low: float = 20.0   # %
    memory_threshold_high: float = 85.0  # %
    memory_threshold_low: float = 50.0   # %
    battery_threshold_low: float = 20.0  # %
    battery_threshold_critical: float = 10.0  # %
    hotkey_latency_threshold: float = 100.0  # ms
    transcription_timeout: float = 300.0  # seconds
    cache_max_size: int = 100  # entries
    cache_ttl: int = 3600  # seconds
    gc_threshold: int = 50  # MB memory increase before GC
    
    # Adaptive settings
    model_preload_enabled: bool = True
    aggressive_caching: bool = False
    battery_optimization: bool = True
    background_optimization: bool = True


class CacheManager:
    """Intelligent caching system for models and transcriptions."""
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Tuple[Any, float]] = {}  # key -> (value, timestamp)
        self.access_times: Dict[str, float] = {}
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                # Check TTL
                if time.time() - timestamp < self.ttl:
                    self.access_times[key] = time.time()
                    self.hits += 1
                    return value
                else:
                    # Expired
                    del self.cache[key]
                    if key in self.access_times:
                        del self.access_times[key]
            
            self.misses += 1
            return None
    
    def put(self, key: str, value: Any) -> None:
        """Put value in cache."""
        with self.lock:
            current_time = time.time()
            
            # Remove expired entries
            self._cleanup_expired()
            
            # If at capacity, remove LRU
            if len(self.cache) >= self.max_size:
                self._remove_lru()
            
            self.cache[key] = (value, current_time)
            self.access_times[key] = current_time
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if current_time - timestamp >= self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
    
    def _remove_lru(self) -> None:
        """Remove least recently used entry."""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[lru_key]
        del self.access_times[lru_key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "ttl": self.ttl
            }


class PerformanceMonitor:
    """
    Comprehensive performance monitor for the Dicto application.
    Tracks system resources, implements adaptive optimization, manages battery usage,
    and provides intelligent caching and analytics.
    """
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize the PerformanceMonitor.
        
        Args:
            log_dir: Directory for performance logs. If None, uses default location.
        """
        self.logger = logging.getLogger("Dicto.PerformanceMonitor")
        
        # Set up directories
        self.log_dir = Path(log_dir) if log_dir else Path.home() / "Library" / "Application Support" / "Dicto" / "performance"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Performance tracking
        self.metrics_history: deque = deque(maxlen=1000)
        self.settings = OptimizationSettings()
        self.cache_manager = CacheManager(self.settings.cache_max_size, self.settings.cache_ttl)
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_interval = 5.0  # seconds
        
        # Performance baseline
        self.baseline_metrics: Optional[PerformanceMetrics] = None
        self.last_gc_memory = 0
        
        # Callbacks for optimization actions
        self.optimization_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Analytics
        self.session_start_time = time.time()
        self.total_transcriptions = 0
        self.total_hotkey_presses = 0
        self.avg_transcription_time = 0.0
        self.avg_hotkey_latency = 0.0
        
        # Battery monitoring
        self.battery_available = hasattr(psutil, 'sensors_battery') and psutil.sensors_battery() is not None
        
        self.logger.info("PerformanceMonitor initialized")
    
    def start_monitoring(self) -> bool:
        """Start background performance monitoring."""
        if self.monitoring_active:
            self.logger.warning("Performance monitoring already active")
            return False
        
        try:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            # Establish baseline
            self.baseline_metrics = self._collect_metrics()
            
            self.logger.info("Performance monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start performance monitoring: {e}")
            self.monitoring_active = False
            return False
    
    def stop_monitoring(self) -> None:
        """Stop background performance monitoring."""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        self.logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Perform adaptive optimization
                self.adaptive_optimization(metrics)
                
                # Check for garbage collection need
                self._check_gc_need(metrics)
                
                # Save metrics periodically
                if len(self.metrics_history) % 10 == 0:
                    self._save_metrics()
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
            
            time.sleep(self.monitoring_interval)
    
    def monitor_system_resources(self) -> Dict[str, Any]:
        """
        Monitor and return current system resource usage.
        
        Returns:
            Dict containing current system resource metrics.
        """
        try:
            metrics = self._collect_metrics()
            
            return {
                "cpu_percent": metrics.cpu_percent,
                "memory_usage_mb": metrics.memory_usage,
                "memory_percent": metrics.memory_percent,
                "disk_io": {
                    "read_mb": metrics.disk_io_read / (1024 * 1024),
                    "write_mb": metrics.disk_io_write / (1024 * 1024)
                },
                "battery": {
                    "percent": metrics.battery_percent,
                    "time_left_minutes": metrics.battery_time_left / 60 if metrics.battery_time_left else None,
                    "power_plugged": metrics.power_plugged
                } if self.battery_available else None,
                "cache_stats": self.cache_manager.stats(),
                "timestamp": metrics.timestamp
            }
            
        except Exception as e:
            self.logger.error(f"Error monitoring system resources: {e}")
            return {}
    
    def adaptive_optimization(self, metrics: Optional[PerformanceMetrics] = None) -> Dict[str, Any]:
        """
        Perform adaptive optimization based on current system state.
        
        Args:
            metrics: Current metrics. If None, collects fresh metrics.
            
        Returns:
            Dict containing optimization actions taken.
        """
        if metrics is None:
            metrics = self._collect_metrics()
        
        actions_taken = {}
        
        try:
            # CPU optimization
            if metrics.cpu_percent > self.settings.cpu_threshold_high:
                actions_taken["cpu_high"] = self._optimize_cpu_usage()
            elif metrics.cpu_percent < self.settings.cpu_threshold_low:
                actions_taken["cpu_low"] = self._enable_background_tasks()
            
            # Memory optimization
            if metrics.memory_percent > self.settings.memory_threshold_high:
                actions_taken["memory_high"] = self._optimize_memory_usage()
            
            # Battery optimization
            if self.battery_available and metrics.battery_percent is not None:
                if metrics.battery_percent < self.settings.battery_threshold_critical:
                    actions_taken["battery_critical"] = self._critical_battery_mode()
                elif metrics.battery_percent < self.settings.battery_threshold_low:
                    actions_taken["battery_low"] = self._low_battery_mode()
            
            # Hotkey latency optimization
            if metrics.hotkey_latency and metrics.hotkey_latency > self.settings.hotkey_latency_threshold:
                actions_taken["latency_high"] = self._optimize_hotkey_latency()
            
            # Cache optimization
            cache_stats = self.cache_manager.stats()
            if cache_stats["hit_rate"] < 50:  # Less than 50% hit rate
                actions_taken["cache_low"] = self._optimize_cache_strategy()
            
            return actions_taken
            
        except Exception as e:
            self.logger.error(f"Error in adaptive optimization: {e}")
            return {"error": str(e)}
    
    def battery_optimization(self) -> Dict[str, Any]:
        """
        Implement battery-specific optimizations.
        
        Returns:
            Dict containing battery optimization status and actions.
        """
        if not self.battery_available:
            return {"available": False, "reason": "Battery monitoring not available"}
        
        try:
            battery = psutil.sensors_battery()
            if not battery:
                return {"available": False, "reason": "No battery detected"}
            
            optimization_actions = {}
            
            # Get current battery status
            percent = battery.percent
            plugged = battery.power_plugged
            time_left = battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
            
            if not plugged:
                # Running on battery
                if percent < self.settings.battery_threshold_critical:
                    # Critical battery mode
                    optimization_actions.update(self._critical_battery_mode())
                elif percent < self.settings.battery_threshold_low:
                    # Low battery mode
                    optimization_actions.update(self._low_battery_mode())
                else:
                    # Normal battery optimization
                    optimization_actions.update(self._normal_battery_mode())
            else:
                # Plugged in - can use full performance
                optimization_actions.update(self._plugged_in_mode())
            
            return {
                "available": True,
                "battery_percent": percent,
                "power_plugged": plugged,
                "time_left_minutes": time_left / 60 if time_left else None,
                "actions": optimization_actions
            }
            
        except Exception as e:
            self.logger.error(f"Error in battery optimization: {e}")
            return {"available": False, "error": str(e)}
    
    def cache_manager(self) -> CacheManager:
        """
        Get the cache manager instance for intelligent data caching.
        
        Returns:
            CacheManager instance.
        """
        return self.cache_manager
    
    def performance_analytics(self) -> Dict[str, Any]:
        """
        Analyze usage patterns and provide performance insights.
        
        Returns:
            Dict containing performance analytics and recommendations.
        """
        try:
            current_time = time.time()
            session_duration = current_time - self.session_start_time
            
            # Analyze metrics history
            if not self.metrics_history:
                return {"error": "No metrics data available"}
            
            recent_metrics = list(self.metrics_history)
            
            # Calculate averages
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
            
            # Identify peak usage times
            cpu_peaks = [m for m in recent_metrics if m.cpu_percent > self.settings.cpu_threshold_high]
            memory_peaks = [m for m in recent_metrics if m.memory_percent > self.settings.memory_threshold_high]
            
            # Cache performance
            cache_stats = self.cache_manager.stats()
            
            # Recommendations
            recommendations = []
            
            if avg_cpu > 60:
                recommendations.append("Consider reducing background processes during recording")
            
            if avg_memory > 70:
                recommendations.append("Memory usage is high - consider restarting the app periodically")
            
            if cache_stats["hit_rate"] < 50:
                recommendations.append("Cache hit rate is low - consider adjusting cache settings")
            
            if len(cpu_peaks) > len(recent_metrics) * 0.3:
                recommendations.append("Frequent CPU spikes detected - consider enabling background optimization")
            
            return {
                "session_duration_minutes": session_duration / 60,
                "total_transcriptions": self.total_transcriptions,
                "total_hotkey_presses": self.total_hotkey_presses,
                "average_metrics": {
                    "cpu_percent": avg_cpu,
                    "memory_percent": avg_memory,
                    "transcription_time": self.avg_transcription_time,
                    "hotkey_latency": self.avg_hotkey_latency
                },
                "peak_usage": {
                    "cpu_peaks": len(cpu_peaks),
                    "memory_peaks": len(memory_peaks)
                },
                "cache_performance": cache_stats,
                "recommendations": recommendations,
                "metrics_collected": len(recent_metrics)
            }
            
        except Exception as e:
            self.logger.error(f"Error in performance analytics: {e}")
            return {"error": str(e)}
    
    def record_hotkey_latency(self, latency_ms: float) -> None:
        """Record hotkey response latency."""
        self.total_hotkey_presses += 1
        
        # Update running average
        if self.avg_hotkey_latency == 0:
            self.avg_hotkey_latency = latency_ms
        else:
            # Exponential moving average
            alpha = 0.1
            self.avg_hotkey_latency = alpha * latency_ms + (1 - alpha) * self.avg_hotkey_latency
    
    def record_transcription_time(self, duration_seconds: float) -> None:
        """Record transcription processing time."""
        self.total_transcriptions += 1
        
        # Update running average
        if self.avg_transcription_time == 0:
            self.avg_transcription_time = duration_seconds
        else:
            # Exponential moving average
            alpha = 0.1
            self.avg_transcription_time = alpha * duration_seconds + (1 - alpha) * self.avg_transcription_time
    
    def register_optimization_callback(self, event: str, callback: Callable) -> None:
        """Register a callback for optimization events."""
        self.optimization_callbacks[event].append(callback)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current system metrics."""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read = disk_io.read_bytes if disk_io else 0
            disk_write = disk_io.write_bytes if disk_io else 0
            
            # Battery (if available)
            battery_percent = None
            battery_time_left = None
            power_plugged = None
            
            if self.battery_available:
                battery = psutil.sensors_battery()
                if battery:
                    battery_percent = battery.percent
                    battery_time_left = battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None
                    power_plugged = battery.power_plugged
            
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_usage=memory.used / (1024 * 1024),  # MB
                memory_percent=memory.percent,
                disk_io_read=disk_read,
                disk_io_write=disk_write,
                battery_percent=battery_percent,
                battery_time_left=battery_time_left,
                power_plugged=power_plugged,
                cache_hits=self.cache_manager.hits,
                cache_misses=self.cache_manager.misses
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            # Return default metrics
            return PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_usage=0.0,
                memory_percent=0.0,
                disk_io_read=0,
                disk_io_write=0
            )
    
    def _optimize_cpu_usage(self) -> Dict[str, Any]:
        """Optimize for high CPU usage."""
        actions = {}
        
        # Reduce monitoring frequency
        self.monitoring_interval = min(10.0, self.monitoring_interval * 1.5)
        actions["monitoring_interval"] = self.monitoring_interval
        
        # Trigger callbacks
        for callback in self.optimization_callbacks.get("cpu_high", []):
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in CPU optimization callback: {e}")
        
        self.logger.info("Applied CPU usage optimizations")
        return actions
    
    def _enable_background_tasks(self) -> Dict[str, Any]:
        """Enable background tasks when CPU is low."""
        actions = {}
        
        # Increase monitoring frequency
        self.monitoring_interval = max(2.0, self.monitoring_interval * 0.8)
        actions["monitoring_interval"] = self.monitoring_interval
        
        # Enable model preloading if disabled
        if not self.settings.model_preload_enabled:
            self.settings.model_preload_enabled = True
            actions["model_preload"] = True
        
        # Trigger callbacks
        for callback in self.optimization_callbacks.get("cpu_low", []):
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in background task callback: {e}")
        
        return actions
    
    def _optimize_memory_usage(self) -> Dict[str, Any]:
        """Optimize for high memory usage."""
        actions = {}
        
        # Force garbage collection
        gc.collect()
        actions["garbage_collection"] = True
        
        # Reduce cache size
        old_size = self.cache_manager.max_size
        self.cache_manager.max_size = max(10, old_size // 2)
        actions["cache_size_reduced"] = f"{old_size} -> {self.cache_manager.max_size}"
        
        # Clear cache if very high memory usage
        if psutil.virtual_memory().percent > 90:
            self.cache_manager.clear()
            actions["cache_cleared"] = True
        
        # Trigger callbacks
        for callback in self.optimization_callbacks.get("memory_high", []):
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in memory optimization callback: {e}")
        
        self.logger.info("Applied memory usage optimizations")
        return actions
    
    def _critical_battery_mode(self) -> Dict[str, Any]:
        """Apply critical battery optimizations."""
        actions = {}
        
        # Minimal monitoring
        self.monitoring_interval = 15.0
        actions["monitoring_interval"] = self.monitoring_interval
        
        # Disable non-essential features
        self.settings.model_preload_enabled = False
        self.settings.aggressive_caching = False
        actions["features_disabled"] = ["model_preload", "aggressive_caching"]
        
        # Clear cache to save memory
        self.cache_manager.clear()
        actions["cache_cleared"] = True
        
        # Force garbage collection
        gc.collect()
        actions["garbage_collection"] = True
        
        self.logger.warning("Critical battery mode activated")
        return actions
    
    def _low_battery_mode(self) -> Dict[str, Any]:
        """Apply low battery optimizations."""
        actions = {}
        
        # Reduced monitoring
        self.monitoring_interval = 10.0
        actions["monitoring_interval"] = self.monitoring_interval
        
        # Reduce cache size
        self.cache_manager.max_size = max(10, self.cache_manager.max_size // 2)
        actions["cache_size_reduced"] = self.cache_manager.max_size
        
        # Disable aggressive caching
        self.settings.aggressive_caching = False
        actions["aggressive_caching"] = False
        
        self.logger.info("Low battery mode activated")
        return actions
    
    def _normal_battery_mode(self) -> Dict[str, Any]:
        """Apply normal battery optimizations."""
        actions = {}
        
        # Standard monitoring
        self.monitoring_interval = 7.0
        actions["monitoring_interval"] = self.monitoring_interval
        
        # Moderate cache settings
        self.cache_manager.max_size = 50
        actions["cache_size"] = self.cache_manager.max_size
        
        return actions
    
    def _plugged_in_mode(self) -> Dict[str, Any]:
        """Apply optimizations for plugged-in operation."""
        actions = {}
        
        # Full performance monitoring
        self.monitoring_interval = 5.0
        actions["monitoring_interval"] = self.monitoring_interval
        
        # Enable all features
        self.settings.model_preload_enabled = True
        self.settings.aggressive_caching = True
        actions["full_performance"] = True
        
        # Restore full cache size
        self.cache_manager.max_size = self.settings.cache_max_size
        actions["cache_size"] = self.cache_manager.max_size
        
        return actions
    
    def _optimize_hotkey_latency(self) -> Dict[str, Any]:
        """Optimize for high hotkey latency."""
        actions = {}
        
        # Increase monitoring frequency to detect issues faster
        self.monitoring_interval = max(2.0, self.monitoring_interval * 0.8)
        actions["monitoring_interval"] = self.monitoring_interval
        
        # Trigger callbacks
        for callback in self.optimization_callbacks.get("latency_high", []):
            try:
                callback()
            except Exception as e:
                self.logger.error(f"Error in latency optimization callback: {e}")
        
        return actions
    
    def _optimize_cache_strategy(self) -> Dict[str, Any]:
        """Optimize cache strategy for better performance."""
        actions = {}
        
        # Increase cache TTL for better hit rates
        old_ttl = self.cache_manager.ttl
        self.cache_manager.ttl = min(7200, old_ttl * 1.5)  # Max 2 hours
        actions["cache_ttl_increased"] = f"{old_ttl} -> {self.cache_manager.ttl}"
        
        # Enable aggressive caching if system can handle it
        if psutil.virtual_memory().percent < 70:
            self.settings.aggressive_caching = True
            actions["aggressive_caching"] = True
        
        return actions
    
    def _check_gc_need(self, metrics: PerformanceMetrics) -> None:
        """Check if garbage collection is needed."""
        memory_increase = metrics.memory_usage - self.last_gc_memory
        
        if memory_increase > self.settings.gc_threshold:
            gc.collect()
            self.last_gc_memory = metrics.memory_usage
            self.logger.debug(f"Garbage collection triggered after {memory_increase:.1f}MB increase")
    
    def _save_metrics(self) -> None:
        """Save metrics to disk for analytics."""
        try:
            metrics_file = self.log_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
            
            # Convert recent metrics to serializable format
            recent_metrics = list(self.metrics_history)[-10:]  # Last 10 entries
            
            metrics_data = []
            for metric in recent_metrics:
                metrics_data.append({
                    "timestamp": metric.timestamp,
                    "cpu_percent": metric.cpu_percent,
                    "memory_usage": metric.memory_usage,
                    "memory_percent": metric.memory_percent,
                    "battery_percent": metric.battery_percent,
                    "hotkey_latency": metric.hotkey_latency,
                    "transcription_latency": metric.transcription_latency,
                    "cache_hits": metric.cache_hits,
                    "cache_misses": metric.cache_misses
                })
            
            # Load existing data if file exists
            existing_data = []
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    existing_data = json.load(f)
            
            # Append new data
            existing_data.extend(metrics_data)
            
            # Keep only last 1000 entries to prevent file from growing too large
            if len(existing_data) > 1000:
                existing_data = existing_data[-1000:]
            
            # Save to file
            with open(metrics_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving metrics: {e}")
    
    def get_settings(self) -> OptimizationSettings:
        """Get current optimization settings."""
        return self.settings
    
    def update_settings(self, **kwargs) -> None:
        """Update optimization settings."""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
                self.logger.info(f"Updated setting {key} = {value}")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_monitoring()
        self.cache_manager.clear()
        self.logger.info("PerformanceMonitor cleaned up") 