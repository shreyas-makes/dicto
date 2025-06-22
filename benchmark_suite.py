#!/usr/bin/env python3
"""
Benchmark Suite - Comprehensive performance testing for Dicto
This module provides benchmarking tools to test system performance,
hotkey response times, transcription speed, and memory usage.
"""

import os
import sys
import time
import threading
import logging
import psutil
import tempfile
import statistics
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import json
import subprocess
from datetime import datetime


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    test_name: str
    duration: float
    cpu_usage: List[float]
    memory_usage: List[float]
    success_rate: float
    error_count: int
    latency_stats: Dict[str, float]  # min, max, avg, p95, p99
    additional_metrics: Dict[str, Any]


class SystemBenchmark:
    """System-level performance benchmarks."""
    
    def __init__(self):
        self.logger = logging.getLogger("Dicto.SystemBenchmark")
    
    def run_cpu_stress_test(self, duration: int = 30) -> BenchmarkResult:
        """Run CPU stress test to measure performance under load."""
        self.logger.info(f"Running CPU stress test for {duration} seconds")
        
        start_time = time.time()
        cpu_readings = []
        memory_readings = []
        
        # CPU stress function
        def cpu_stress():
            end_time = time.time() + duration
            while time.time() < end_time:
                # Perform CPU-intensive operations
                [x**2 for x in range(10000)]
        
        # Start stress test
        stress_thread = threading.Thread(target=cpu_stress)
        stress_thread.start()
        
        # Monitor system resources
        monitor_end = time.time() + duration
        while time.time() < monitor_end:
            cpu_readings.append(psutil.cpu_percent(interval=0.1))
            memory_readings.append(psutil.virtual_memory().percent)
            time.sleep(0.5)
        
        stress_thread.join()
        
        return BenchmarkResult(
            test_name="CPU Stress Test",
            duration=time.time() - start_time,
            cpu_usage=cpu_readings,
            memory_usage=memory_readings,
            success_rate=1.0,
            error_count=0,
            latency_stats={
                "avg_cpu": statistics.mean(cpu_readings),
                "max_cpu": max(cpu_readings),
                "avg_memory": statistics.mean(memory_readings),
                "max_memory": max(memory_readings)
            },
            additional_metrics={}
        )
    
    def run_memory_stress_test(self, target_mb: int = 500) -> BenchmarkResult:
        """Run memory stress test to measure performance under memory pressure."""
        self.logger.info(f"Running memory stress test with {target_mb}MB allocation")
        
        start_time = time.time()
        cpu_readings = []
        memory_readings = []
        
        try:
            # Allocate memory in chunks
            memory_chunks = []
            chunk_size = 10 * 1024 * 1024  # 10MB chunks
            chunks_needed = target_mb // 10
            
            for i in range(chunks_needed):
                memory_chunks.append(bytearray(chunk_size))
                
                # Monitor during allocation
                cpu_readings.append(psutil.cpu_percent(interval=0.1))
                memory_readings.append(psutil.virtual_memory().percent)
                
                # Small delay between allocations
                time.sleep(0.1)
            
            # Hold memory for a few seconds while monitoring
            for _ in range(20):
                cpu_readings.append(psutil.cpu_percent(interval=0.1))
                memory_readings.append(psutil.virtual_memory().percent)
                time.sleep(0.1)
            
            success_rate = 1.0
            error_count = 0
            
        except MemoryError:
            success_rate = 0.0
            error_count = 1
            self.logger.error("Memory allocation failed")
        
        return BenchmarkResult(
            test_name="Memory Stress Test",
            duration=time.time() - start_time,
            cpu_usage=cpu_readings,
            memory_usage=memory_readings,
            success_rate=success_rate,
            error_count=error_count,
            latency_stats={
                "avg_cpu": statistics.mean(cpu_readings) if cpu_readings else 0,
                "avg_memory": statistics.mean(memory_readings) if memory_readings else 0,
                "peak_memory": max(memory_readings) if memory_readings else 0
            },
            additional_metrics={"target_mb": target_mb}
        )


class AudioBenchmark:
    """Audio processing performance benchmarks."""
    
    def __init__(self, audio_recorder=None, transcription_engine=None):
        self.logger = logging.getLogger("Dicto.AudioBenchmark")
        self.audio_recorder = audio_recorder
        self.transcription_engine = transcription_engine
    
    def run_recording_latency_test(self, iterations: int = 10) -> BenchmarkResult:
        """Test audio recording start/stop latency."""
        self.logger.info(f"Running recording latency test with {iterations} iterations")
        
        if not self.audio_recorder:
            return BenchmarkResult(
                test_name="Recording Latency Test",
                duration=0,
                cpu_usage=[],
                memory_usage=[],
                success_rate=0.0,
                error_count=1,
                latency_stats={},
                additional_metrics={"error": "Audio recorder not available"}
            )
        
        start_time = time.time()
        latencies = []
        cpu_readings = []
        memory_readings = []
        errors = 0
        
        for i in range(iterations):
            try:
                # Measure recording start latency
                start_latency_time = time.time()
                recording_file = self.audio_recorder.start_recording(duration=1.0)
                start_latency = (time.time() - start_latency_time) * 1000  # ms
                
                if recording_file:
                    # Wait for recording to complete
                    time.sleep(1.1)
                    
                    # Measure stop latency
                    stop_latency_time = time.time()
                    result_file = self.audio_recorder.stop_recording()
                    stop_latency = (time.time() - stop_latency_time) * 1000  # ms
                    
                    total_latency = start_latency + stop_latency
                    latencies.append(total_latency)
                    
                    # Clean up
                    if result_file and os.path.exists(result_file):
                        os.remove(result_file)
                else:
                    errors += 1
                
                # Monitor system resources
                cpu_readings.append(psutil.cpu_percent(interval=0.1))
                memory_readings.append(psutil.virtual_memory().percent)
                
            except Exception as e:
                self.logger.error(f"Recording test iteration {i} failed: {e}")
                errors += 1
            
            # Small delay between iterations
            time.sleep(0.5)
        
        success_rate = (iterations - errors) / iterations if iterations > 0 else 0
        
        latency_stats = {}
        if latencies:
            latency_stats = {
                "min": min(latencies),
                "max": max(latencies),
                "avg": statistics.mean(latencies),
                "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
                "p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
            }
        
        return BenchmarkResult(
            test_name="Recording Latency Test",
            duration=time.time() - start_time,
            cpu_usage=cpu_readings,
            memory_usage=memory_readings,
            success_rate=success_rate,
            error_count=errors,
            latency_stats=latency_stats,
            additional_metrics={"iterations": iterations}
        )
    
    def run_transcription_speed_test(self, test_files: List[str] = None) -> BenchmarkResult:
        """Test transcription processing speed with various audio files."""
        self.logger.info("Running transcription speed test")
        
        if not self.transcription_engine:
            return BenchmarkResult(
                test_name="Transcription Speed Test",
                duration=0,
                cpu_usage=[],
                memory_usage=[],
                success_rate=0.0,
                error_count=1,
                latency_stats={},
                additional_metrics={"error": "Transcription engine not available"}
            )
        
        # If no test files provided, create a simple test recording
        if not test_files:
            test_files = self._create_test_audio_files()
        
        start_time = time.time()
        transcription_times = []
        cpu_readings = []
        memory_readings = []
        errors = 0
        
        for test_file in test_files:
            try:
                if not os.path.exists(test_file):
                    continue
                
                # Monitor resources before transcription
                cpu_before = psutil.cpu_percent(interval=0.1)
                memory_before = psutil.virtual_memory().percent
                
                # Perform transcription
                transcription_start = time.time()
                result = self.transcription_engine.transcribe_file(test_file)
                transcription_time = time.time() - transcription_start
                
                if result.get("success", False):
                    transcription_times.append(transcription_time)
                else:
                    errors += 1
                
                # Monitor resources after transcription
                cpu_after = psutil.cpu_percent(interval=0.1)
                memory_after = psutil.virtual_memory().percent
                
                cpu_readings.extend([cpu_before, cpu_after])
                memory_readings.extend([memory_before, memory_after])
                
            except Exception as e:
                self.logger.error(f"Transcription test failed for {test_file}: {e}")
                errors += 1
        
        success_rate = (len(test_files) - errors) / len(test_files) if test_files else 0
        
        latency_stats = {}
        if transcription_times:
            latency_stats = {
                "min": min(transcription_times),
                "max": max(transcription_times),
                "avg": statistics.mean(transcription_times),
                "p95": statistics.quantiles(transcription_times, n=20)[18] if len(transcription_times) >= 20 else max(transcription_times),
                "p99": statistics.quantiles(transcription_times, n=100)[98] if len(transcription_times) >= 100 else max(transcription_times)
            }
        
        return BenchmarkResult(
            test_name="Transcription Speed Test",
            duration=time.time() - start_time,
            cpu_usage=cpu_readings,
            memory_usage=memory_readings,
            success_rate=success_rate,
            error_count=errors,
            latency_stats=latency_stats,
            additional_metrics={"test_files_count": len(test_files)}
        )
    
    def _create_test_audio_files(self) -> List[str]:
        """Create simple test audio files for benchmarking."""
        test_files = []
        
        try:
            # Create a simple silent WAV file for testing
            import wave
            import struct
            
            temp_dir = Path(tempfile.gettempdir()) / "dicto_benchmark"
            temp_dir.mkdir(exist_ok=True)
            
            # Create different duration test files
            durations = [1, 5, 10]  # seconds
            
            for duration in durations:
                filename = temp_dir / f"test_{duration}s.wav"
                
                with wave.open(str(filename), 'w') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(16000)  # 16kHz
                    
                    # Generate silence
                    frames = 16000 * duration
                    for _ in range(frames):
                        wav_file.writeframes(struct.pack('<h', 0))
                
                test_files.append(str(filename))
                self.logger.info(f"Created test file: {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to create test audio files: {e}")
        
        return test_files


class HotkeyBenchmark:
    """Hotkey response performance benchmarks."""
    
    def __init__(self):
        self.logger = logging.getLogger("Dicto.HotkeyBenchmark")
    
    def run_hotkey_latency_test(self, iterations: int = 50) -> BenchmarkResult:
        """Test hotkey response latency simulation."""
        self.logger.info(f"Running hotkey latency test with {iterations} iterations")
        
        start_time = time.time()
        latencies = []
        cpu_readings = []
        memory_readings = []
        
        for i in range(iterations):
            # Simulate hotkey processing time
            hotkey_start = time.time()
            
            # Simulate hotkey handler work
            time.sleep(0.001)  # 1ms base processing time
            
            # Simulate variable system load impact
            cpu_load = psutil.cpu_percent(interval=0.01)
            if cpu_load > 50:
                time.sleep(0.002)  # Additional delay under high CPU load
            
            hotkey_latency = (time.time() - hotkey_start) * 1000  # ms
            latencies.append(hotkey_latency)
            
            # Monitor system resources
            cpu_readings.append(psutil.cpu_percent(interval=0.01))
            memory_readings.append(psutil.virtual_memory().percent)
            
            # Small delay between iterations
            time.sleep(0.01)
        
        latency_stats = {
            "min": min(latencies),
            "max": max(latencies),
            "avg": statistics.mean(latencies),
            "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies),
            "p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies)
        }
        
        return BenchmarkResult(
            test_name="Hotkey Latency Test",
            duration=time.time() - start_time,
            cpu_usage=cpu_readings,
            memory_usage=memory_readings,
            success_rate=1.0,
            error_count=0,
            latency_stats=latency_stats,
            additional_metrics={"iterations": iterations}
        )


class PerformanceBenchmarkSuite:
    """Main benchmark suite coordinator."""
    
    def __init__(self, audio_recorder=None, transcription_engine=None, log_dir: Optional[str] = None):
        """
        Initialize the benchmark suite.
        
        Args:
            audio_recorder: AudioRecorder instance for audio tests
            transcription_engine: TranscriptionEngine instance for transcription tests
            log_dir: Directory for benchmark logs
        """
        self.logger = logging.getLogger("Dicto.BenchmarkSuite")
        
        # Set up logging directory
        self.log_dir = Path(log_dir) if log_dir else Path.home() / "Library" / "Application Support" / "Dicto" / "benchmarks"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize benchmark modules
        self.system_benchmark = SystemBenchmark()
        self.audio_benchmark = AudioBenchmark(audio_recorder, transcription_engine)
        self.hotkey_benchmark = HotkeyBenchmark()
        
        # Results storage
        self.results: List[BenchmarkResult] = []
    
    def run_full_benchmark_suite(self, quick_mode: bool = False) -> Dict[str, Any]:
        """
        Run the complete benchmark suite.
        
        Args:
            quick_mode: If True, runs shorter versions of tests
            
        Returns:
            Dict containing benchmark results and summary
        """
        self.logger.info(f"Starting full benchmark suite (quick_mode={quick_mode})")
        
        start_time = time.time()
        self.results.clear()
        
        # System benchmarks
        try:
            self.logger.info("Running system benchmarks...")
            
            cpu_duration = 10 if quick_mode else 30
            cpu_result = self.system_benchmark.run_cpu_stress_test(duration=cpu_duration)
            self.results.append(cpu_result)
            
            memory_mb = 100 if quick_mode else 500
            memory_result = self.system_benchmark.run_memory_stress_test(target_mb=memory_mb)
            self.results.append(memory_result)
            
        except Exception as e:
            self.logger.error(f"System benchmark failed: {e}")
        
        # Audio benchmarks
        try:
            self.logger.info("Running audio benchmarks...")
            
            recording_iterations = 5 if quick_mode else 10
            recording_result = self.audio_benchmark.run_recording_latency_test(iterations=recording_iterations)
            self.results.append(recording_result)
            
            transcription_result = self.audio_benchmark.run_transcription_speed_test()
            self.results.append(transcription_result)
            
        except Exception as e:
            self.logger.error(f"Audio benchmark failed: {e}")
        
        # Hotkey benchmarks
        try:
            self.logger.info("Running hotkey benchmarks...")
            
            hotkey_iterations = 25 if quick_mode else 50
            hotkey_result = self.hotkey_benchmark.run_hotkey_latency_test(iterations=hotkey_iterations)
            self.results.append(hotkey_result)
            
        except Exception as e:
            self.logger.error(f"Hotkey benchmark failed: {e}")
        
        total_duration = time.time() - start_time
        
        # Generate summary
        summary = self._generate_summary(total_duration)
        
        # Save results
        self._save_results(summary)
        
        self.logger.info(f"Benchmark suite completed in {total_duration:.2f} seconds")
        
        return summary
    
    def run_performance_regression_test(self, baseline_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Run performance regression test against baseline.
        
        Args:
            baseline_file: Path to baseline benchmark results
            
        Returns:
            Dict containing regression analysis
        """
        self.logger.info("Running performance regression test")
        
        # Run current benchmarks
        current_results = self.run_full_benchmark_suite(quick_mode=True)
        
        # Load baseline if provided
        baseline_results = None
        if baseline_file and os.path.exists(baseline_file):
            try:
                with open(baseline_file, 'r') as f:
                    baseline_results = json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load baseline file: {e}")
        
        # Compare results
        regression_analysis = self._compare_with_baseline(current_results, baseline_results)
        
        return regression_analysis
    
    def _generate_summary(self, total_duration: float) -> Dict[str, Any]:
        """Generate benchmark summary."""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": total_duration,
            "total_tests": len(self.results),
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "platform": sys.platform
            },
            "results": {},
            "overall_metrics": {}
        }
        
        # Process individual results
        total_errors = 0
        avg_success_rate = 0
        
        for result in self.results:
            summary["results"][result.test_name] = {
                "duration": result.duration,
                "success_rate": result.success_rate,
                "error_count": result.error_count,
                "latency_stats": result.latency_stats,
                "avg_cpu": statistics.mean(result.cpu_usage) if result.cpu_usage else 0,
                "max_cpu": max(result.cpu_usage) if result.cpu_usage else 0,
                "avg_memory": statistics.mean(result.memory_usage) if result.memory_usage else 0,
                "max_memory": max(result.memory_usage) if result.memory_usage else 0,
                "additional_metrics": result.additional_metrics
            }
            
            total_errors += result.error_count
            avg_success_rate += result.success_rate
        
        # Calculate overall metrics
        if self.results:
            summary["overall_metrics"] = {
                "average_success_rate": avg_success_rate / len(self.results),
                "total_errors": total_errors,
                "tests_passed": len([r for r in self.results if r.success_rate > 0.8]),
                "tests_failed": len([r for r in self.results if r.success_rate <= 0.8])
            }
        
        return summary
    
    def _compare_with_baseline(self, current: Dict[str, Any], baseline: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare current results with baseline."""
        if not baseline:
            return {"status": "no_baseline", "message": "No baseline provided for comparison"}
        
        comparison = {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "regressions": [],
            "improvements": [],
            "summary": {}
        }
        
        try:
            for test_name, current_result in current["results"].items():
                if test_name not in baseline.get("results", {}):
                    continue
                
                baseline_result = baseline["results"][test_name]
                
                # Compare key metrics
                current_latency = current_result.get("latency_stats", {}).get("avg", 0)
                baseline_latency = baseline_result.get("latency_stats", {}).get("avg", 0)
                
                if baseline_latency > 0:
                    latency_change = ((current_latency - baseline_latency) / baseline_latency) * 100
                    
                    if latency_change > 10:  # 10% regression threshold
                        comparison["regressions"].append({
                            "test": test_name,
                            "metric": "average_latency",
                            "change_percent": latency_change,
                            "current": current_latency,
                            "baseline": baseline_latency
                        })
                    elif latency_change < -10:  # 10% improvement threshold
                        comparison["improvements"].append({
                            "test": test_name,
                            "metric": "average_latency",
                            "change_percent": latency_change,
                            "current": current_latency,
                            "baseline": baseline_latency
                        })
                
                # Compare success rates
                current_success = current_result.get("success_rate", 0)
                baseline_success = baseline_result.get("success_rate", 0)
                
                if current_success < baseline_success - 0.1:  # 10% success rate drop
                    comparison["regressions"].append({
                        "test": test_name,
                        "metric": "success_rate",
                        "change_percent": ((current_success - baseline_success) / baseline_success) * 100,
                        "current": current_success,
                        "baseline": baseline_success
                    })
            
            # Generate summary
            comparison["summary"] = {
                "total_regressions": len(comparison["regressions"]),
                "total_improvements": len(comparison["improvements"]),
                "overall_status": "regression" if comparison["regressions"] else "stable"
            }
            
        except Exception as e:
            comparison["status"] = "error"
            comparison["error"] = str(e)
        
        return comparison
    
    def _save_results(self, summary: Dict[str, Any]) -> None:
        """Save benchmark results to file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = self.log_dir / f"benchmark_results_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            # Also save as latest
            latest_file = self.log_dir / "latest_benchmark_results.json"
            with open(latest_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            self.logger.info(f"Benchmark results saved to {results_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save benchmark results: {e}")
    
    def cleanup(self) -> None:
        """Clean up benchmark resources."""
        # Clean up any temporary test files
        try:
            temp_dir = Path(tempfile.gettempdir()) / "dicto_benchmark"
            if temp_dir.exists():
                for file in temp_dir.glob("*"):
                    file.unlink()
                temp_dir.rmdir()
                self.logger.info("Cleaned up benchmark temp files")
        except Exception as e:
            self.logger.warning(f"Failed to clean up temp files: {e}")


def main():
    """Command-line interface for running benchmarks."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dicto Performance Benchmark Suite")
    parser.add_argument("--quick", action="store_true", help="Run quick benchmarks")
    parser.add_argument("--baseline", type=str, help="Path to baseline results for regression testing")
    parser.add_argument("--output", type=str, help="Output directory for results")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize benchmark suite
    suite = PerformanceBenchmarkSuite(log_dir=args.output)
    
    try:
        if args.baseline:
            # Run regression test
            results = suite.run_performance_regression_test(args.baseline)
            print(f"Regression test completed. Status: {results.get('status')}")
            
            if results.get('regressions'):
                print(f"⚠️  Found {len(results['regressions'])} performance regressions")
                for regression in results['regressions']:
                    print(f"  - {regression['test']}: {regression['metric']} regressed by {regression['change_percent']:.1f}%")
            else:
                print("✅ No performance regressions detected")
                
        else:
            # Run full benchmark suite
            results = suite.run_full_benchmark_suite(quick_mode=args.quick)
            print(f"Benchmark suite completed in {results['total_duration']:.2f} seconds")
            print(f"Tests passed: {results['overall_metrics']['tests_passed']}")
            print(f"Tests failed: {results['overall_metrics']['tests_failed']}")
            print(f"Overall success rate: {results['overall_metrics']['average_success_rate']:.1%}")
    
    finally:
        suite.cleanup()


if __name__ == "__main__":
    main() 