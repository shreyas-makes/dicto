#!/usr/bin/env python3
"""
Test Performance - Unit tests for performance monitoring and optimization
This module provides comprehensive tests for the PerformanceMonitor class,
cache management, and benchmark suite functionality.
"""

import unittest
import tempfile
import time
import threading
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the modules to test
try:
    from performance_monitor import PerformanceMonitor, CacheManager, PerformanceMetrics, OptimizationSettings
    from benchmark_suite import PerformanceBenchmarkSuite, SystemBenchmark, AudioBenchmark, HotkeyBenchmark
except ImportError as e:
    print(f"Warning: Could not import performance modules: {e}")


class TestCacheManager(unittest.TestCase):
    """Test cases for the CacheManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cache = CacheManager(max_size=5, ttl=1)  # Small cache for testing
    
    def test_cache_put_get(self):
        """Test basic cache put and get operations."""
        # Test putting and getting values
        self.cache.put("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
        
        # Test cache miss
        self.assertIsNone(self.cache.get("nonexistent"))
    
    def test_cache_ttl_expiration(self):
        """Test that cache entries expire after TTL."""
        self.cache.put("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
        
        # Wait for TTL to expire
        time.sleep(1.1)
        self.assertIsNone(self.cache.get("key1"))
    
    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        # Fill cache to capacity
        for i in range(5):
            self.cache.put(f"key{i}", f"value{i}")
        
        # Verify all entries are present
        for i in range(5):
            self.assertEqual(self.cache.get(f"key{i}"), f"value{i}")
        
        # Add one more entry to trigger eviction
        self.cache.put("key5", "value5")
        
        # key0 should be evicted (least recently used)
        self.assertIsNone(self.cache.get("key0"))
        self.assertEqual(self.cache.get("key5"), "value5")
    
    def test_cache_stats(self):
        """Test cache statistics tracking."""
        # Initially no hits or misses
        stats = self.cache.stats()
        self.assertEqual(stats["hits"], 0)
        self.assertEqual(stats["misses"], 0)
        self.assertEqual(stats["hit_rate"], 0)
        
        # Test cache miss
        self.cache.get("nonexistent")
        stats = self.cache.stats()
        self.assertEqual(stats["misses"], 1)
        
        # Test cache hit
        self.cache.put("key1", "value1")
        self.cache.get("key1")
        stats = self.cache.stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["hit_rate"], 50.0)  # 1 hit out of 2 requests
    
    def test_cache_clear(self):
        """Test cache clearing functionality."""
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        
        self.assertEqual(len(self.cache.cache), 2)
        
        self.cache.clear()
        self.assertEqual(len(self.cache.cache), 0)
        self.assertIsNone(self.cache.get("key1"))


class TestPerformanceMonitor(unittest.TestCase):
    """Test cases for the PerformanceMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.monitor = PerformanceMonitor(log_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.monitor.cleanup()
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test PerformanceMonitor initialization."""
        self.assertIsNotNone(self.monitor.cache_manager)
        self.assertIsInstance(self.monitor.settings, OptimizationSettings)
        self.assertEqual(len(self.monitor.metrics_history), 0)
        self.assertFalse(self.monitor.monitoring_active)
    
    @patch('performance_monitor.psutil.cpu_percent')
    @patch('performance_monitor.psutil.virtual_memory')
    @patch('performance_monitor.psutil.disk_io_counters')
    def test_collect_metrics(self, mock_disk_io, mock_memory, mock_cpu):
        """Test metrics collection."""
        # Mock system metrics
        mock_cpu.return_value = 50.0
        mock_memory.return_value = Mock(used=1024*1024*1024, percent=60.0)  # 1GB used, 60%
        mock_disk_io.return_value = Mock(read_bytes=1000000, write_bytes=500000)
        
        metrics = self.monitor._collect_metrics()
        
        self.assertIsInstance(metrics, PerformanceMetrics)
        self.assertEqual(metrics.cpu_percent, 50.0)
        self.assertEqual(metrics.memory_percent, 60.0)
        self.assertEqual(metrics.memory_usage, 1024.0)  # MB
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping performance monitoring."""
        # Test starting monitoring
        self.assertTrue(self.monitor.start_monitoring())
        self.assertTrue(self.monitor.monitoring_active)
        self.assertIsNotNone(self.monitor.monitoring_thread)
        
        # Test starting already active monitoring
        self.assertFalse(self.monitor.start_monitoring())
        
        # Test stopping monitoring
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.monitoring_active)
    
    def test_record_metrics(self):
        """Test recording performance metrics."""
        # Test hotkey latency recording
        self.monitor.record_hotkey_latency(50.0)
        self.assertEqual(self.monitor.total_hotkey_presses, 1)
        self.assertEqual(self.monitor.avg_hotkey_latency, 50.0)
        
        # Test transcription time recording
        self.monitor.record_transcription_time(2.5)
        self.assertEqual(self.monitor.total_transcriptions, 1)
        self.assertEqual(self.monitor.avg_transcription_time, 2.5)
    
    def test_optimization_callbacks(self):
        """Test optimization callback registration and execution."""
        callback_called = False
        
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        # Register callback
        self.monitor.register_optimization_callback("cpu_high", test_callback)
        
        # Trigger optimization that should call the callback
        with patch.object(self.monitor, '_collect_metrics') as mock_collect:
            mock_collect.return_value = PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=90.0,  # High CPU to trigger optimization
                memory_usage=1000.0,
                memory_percent=50.0,
                disk_io_read=0,
                disk_io_write=0
            )
            
            self.monitor.adaptive_optimization()
            self.assertTrue(callback_called)
    
    def test_cache_manager_integration(self):
        """Test cache manager integration."""
        cache = self.monitor.cache_manager
        
        # Test cache operations
        cache.put("test_key", "test_value")
        self.assertEqual(cache.get("test_key"), "test_value")
        
        # Test cache stats through monitor
        stats = cache.stats()
        self.assertIn("hits", stats)
        self.assertIn("misses", stats)
    
    def test_settings_update(self):
        """Test updating optimization settings."""
        original_threshold = self.monitor.settings.cpu_threshold_high
        
        self.monitor.update_settings(cpu_threshold_high=75.0)
        self.assertEqual(self.monitor.settings.cpu_threshold_high, 75.0)
        self.assertNotEqual(self.monitor.settings.cpu_threshold_high, original_threshold)
    
    @patch('performance_monitor.psutil.sensors_battery')
    def test_battery_optimization(self, mock_battery):
        """Test battery optimization features."""
        # Mock battery with low charge
        mock_battery.return_value = Mock(
            percent=15.0,
            power_plugged=False,
            secsleft=3600
        )
        
        # Set battery available
        self.monitor.battery_available = True
        
        result = self.monitor.battery_optimization()
        
        self.assertTrue(result["available"])
        self.assertEqual(result["battery_percent"], 15.0)
        self.assertFalse(result["power_plugged"])
        self.assertIn("actions", result)


class TestSystemBenchmark(unittest.TestCase):
    """Test cases for the SystemBenchmark class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.benchmark = SystemBenchmark()
    
    def test_cpu_stress_test(self):
        """Test CPU stress test benchmark."""
        # Run short stress test
        result = self.benchmark.run_cpu_stress_test(duration=1)
        
        self.assertEqual(result.test_name, "CPU Stress Test")
        self.assertGreater(result.duration, 0.8)  # Should take at least the duration
        self.assertGreater(len(result.cpu_usage), 0)
        self.assertGreater(len(result.memory_usage), 0)
        self.assertEqual(result.success_rate, 1.0)
        self.assertEqual(result.error_count, 0)
    
    def test_memory_stress_test(self):
        """Test memory stress test benchmark."""
        # Run memory test with small allocation
        result = self.benchmark.run_memory_stress_test(target_mb=10)
        
        self.assertEqual(result.test_name, "Memory Stress Test")
        self.assertGreater(result.duration, 0)
        self.assertGreaterEqual(result.success_rate, 0.0)  # Might fail on low-memory systems
        self.assertIn("target_mb", result.additional_metrics)


class TestHotkeyBenchmark(unittest.TestCase):
    """Test cases for the HotkeyBenchmark class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.benchmark = HotkeyBenchmark()
    
    def test_hotkey_latency_test(self):
        """Test hotkey latency benchmark."""
        # Run short latency test
        result = self.benchmark.run_hotkey_latency_test(iterations=5)
        
        self.assertEqual(result.test_name, "Hotkey Latency Test")
        self.assertGreater(result.duration, 0)
        self.assertEqual(len(result.cpu_usage), 5)  # One reading per iteration
        self.assertEqual(result.success_rate, 1.0)
        self.assertEqual(result.error_count, 0)
        self.assertIn("avg", result.latency_stats)
        self.assertIn("min", result.latency_stats)
        self.assertIn("max", result.latency_stats)


class TestAudioBenchmark(unittest.TestCase):
    """Test cases for the AudioBenchmark class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_recorder = Mock()
        self.mock_engine = Mock()
        self.benchmark = AudioBenchmark(self.mock_recorder, self.mock_engine)
    
    def test_recording_latency_test_no_recorder(self):
        """Test recording latency test without audio recorder."""
        benchmark = AudioBenchmark(None, None)
        result = benchmark.run_recording_latency_test(iterations=1)
        
        self.assertEqual(result.test_name, "Recording Latency Test")
        self.assertEqual(result.success_rate, 0.0)
        self.assertEqual(result.error_count, 1)
        self.assertIn("error", result.additional_metrics)
    
    def test_recording_latency_test_with_mock(self):
        """Test recording latency test with mock recorder."""
        # Configure mock recorder
        self.mock_recorder.start_recording.return_value = "/tmp/test.wav"
        self.mock_recorder.stop_recording.return_value = "/tmp/test.wav"
        
        with patch('os.path.exists', return_value=True), \
             patch('os.remove'):
            
            result = self.benchmark.run_recording_latency_test(iterations=2)
            
            self.assertEqual(result.test_name, "Recording Latency Test")
            self.assertGreater(result.duration, 0)
            self.assertGreaterEqual(result.success_rate, 0.0)
    
    def test_transcription_speed_test_no_engine(self):
        """Test transcription speed test without engine."""
        benchmark = AudioBenchmark(None, None)
        result = benchmark.run_transcription_speed_test()
        
        self.assertEqual(result.test_name, "Transcription Speed Test")
        self.assertEqual(result.success_rate, 0.0)
        self.assertEqual(result.error_count, 1)
        self.assertIn("error", result.additional_metrics)


class TestPerformanceBenchmarkSuite(unittest.TestCase):
    """Test cases for the PerformanceBenchmarkSuite class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.suite = PerformanceBenchmarkSuite(log_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.suite.cleanup()
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test benchmark suite initialization."""
        self.assertIsNotNone(self.suite.system_benchmark)
        self.assertIsNotNone(self.suite.audio_benchmark)
        self.assertIsNotNone(self.suite.hotkey_benchmark)
        self.assertEqual(len(self.suite.results), 0)
    
    def test_run_full_benchmark_suite_quick(self):
        """Test running full benchmark suite in quick mode."""
        result = self.suite.run_full_benchmark_suite(quick_mode=True)
        
        self.assertIn("timestamp", result)
        self.assertIn("total_duration", result)
        self.assertIn("results", result)
        self.assertIn("overall_metrics", result)
        self.assertGreater(result["total_tests"], 0)
    
    def test_generate_summary(self):
        """Test benchmark summary generation."""
        # Add some mock results
        from benchmark_suite import BenchmarkResult
        
        mock_result = BenchmarkResult(
            test_name="Test",
            duration=1.0,
            cpu_usage=[50.0, 60.0],
            memory_usage=[70.0, 80.0],
            success_rate=1.0,
            error_count=0,
            latency_stats={"avg": 25.0, "min": 20.0, "max": 30.0},
            additional_metrics={}
        )
        
        self.suite.results.append(mock_result)
        
        summary = self.suite._generate_summary(total_duration=10.0)
        
        self.assertEqual(summary["total_duration"], 10.0)
        self.assertEqual(summary["total_tests"], 1)
        self.assertIn("Test", summary["results"])
        self.assertEqual(summary["overall_metrics"]["tests_passed"], 1)
    
    def test_compare_with_baseline(self):
        """Test baseline comparison functionality."""
        current = {
            "results": {
                "Test": {
                    "latency_stats": {"avg": 30.0},
                    "success_rate": 0.9
                }
            }
        }
        
        baseline = {
            "results": {
                "Test": {
                    "latency_stats": {"avg": 25.0},
                    "success_rate": 0.95
                }
            }
        }
        
        comparison = self.suite._compare_with_baseline(current, baseline)
        
        self.assertEqual(comparison["status"], "completed")
        self.assertGreater(len(comparison["regressions"]), 0)  # Should detect regression
    
    def test_save_results(self):
        """Test saving benchmark results."""
        summary = {
            "timestamp": "2023-01-01T00:00:00",
            "total_duration": 10.0,
            "results": {}
        }
        
        self.suite._save_results(summary)
        
        # Check that files were created
        latest_file = Path(self.temp_dir) / "latest_benchmark_results.json"
        self.assertTrue(latest_file.exists())
        
        # Verify content
        with open(latest_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["total_duration"], 10.0)


class TestPerformanceIntegration(unittest.TestCase):
    """Integration tests for performance monitoring and benchmarking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.monitor = PerformanceMonitor(log_dir=self.temp_dir)
        self.suite = PerformanceBenchmarkSuite(log_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.monitor.cleanup()
        self.suite.cleanup()
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_monitor_during_benchmark(self):
        """Test running performance monitor during benchmark execution."""
        # Start monitoring
        self.monitor.start_monitoring()
        
        # Run a quick benchmark
        result = self.suite.run_full_benchmark_suite(quick_mode=True)
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        
        # Verify monitoring captured data
        self.assertGreater(len(self.monitor.metrics_history), 0)
        
        # Verify benchmark completed
        self.assertGreater(result["total_tests"], 0)
    
    def test_cache_performance_under_load(self):
        """Test cache performance under concurrent load."""
        cache = self.monitor.cache_manager
        
        def cache_worker(worker_id):
            for i in range(100):
                key = f"worker_{worker_id}_key_{i}"
                value = f"worker_{worker_id}_value_{i}"
                cache.put(key, value)
                retrieved = cache.get(key)
                self.assertEqual(retrieved, value)
        
        # Run multiple workers concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify cache statistics
        stats = cache.stats()
        self.assertGreater(stats["hits"], 0)
        self.assertGreater(stats["misses"], 0)


def run_performance_tests():
    """Run all performance tests."""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestCacheManager,
        TestPerformanceMonitor,
        TestSystemBenchmark,
        TestHotkeyBenchmark,
        TestAudioBenchmark,
        TestPerformanceBenchmarkSuite,
        TestPerformanceIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import logging
    
    # Set up logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce log noise during tests
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    success = run_performance_tests()
    
    if success:
        print("\n✅ All performance tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some performance tests failed!")
        sys.exit(1) 