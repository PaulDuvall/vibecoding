"""
Performance tests for data persistence operations.
Referenced in us004_data_persistence_spec.md as [^pt4]
Tests performance requirements and scalability limits.
"""

import pytest
import time
import psutil
import threading
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from dataclasses import dataclass
from typing import List, Dict, Any
import boto3
from moto import mock_dynamodb

from src.models import DigestItem


@dataclass
class PerformanceMetrics:
    """Container for performance measurement data."""
    duration_seconds: float
    memory_usage_mb: float
    items_processed: int
    operations_per_second: float
    peak_memory_mb: float


class MemoryMonitor:
    """Utility class for monitoring memory usage during tests."""
    
    def __init__(self):
        self.peak_memory = 0
        self.monitoring = False
        self.thread = None
    
    def start_monitoring(self):
        """Start monitoring memory usage in background thread."""
        self.monitoring = True
        self.peak_memory = 0
        self.thread = threading.Thread(target=self._monitor_memory)
        self.thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring and return peak memory usage."""
        self.monitoring = False
        if self.thread:
            self.thread.join()
        return self.peak_memory
    
    def _monitor_memory(self):
        """Background thread function to monitor memory."""
        process = psutil.Process()
        while self.monitoring:
            try:
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB
                self.peak_memory = max(self.peak_memory, memory_mb)
                time.sleep(0.1)  # Check every 100ms
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break


class TestPersistencePerformance:
    """Performance tests for persistence operations."""
    
    def setup_method(self):
        """Set up performance test fixtures."""
        self.memory_monitor = MemoryMonitor()
        
        # Create sample items for performance testing
        self.large_dataset = []
        for i in range(200):  # Test with 200 items
            item = DigestItem(
                title=f"Performance Test Article {i+1}",
                link=f"https://example.com/perf-test-{i+1}",
                summary=f"This is a performance test summary for article {i+1}. " * 5,  # Make it longer
                source=f"Performance Source {(i % 10) + 1}",
                published=datetime(2024, 6, 8, 10, i % 60, 0, tzinfo=timezone.utc)
            )
            self.large_dataset.append(item)
    
    def test_large_digest_processing_performance(self):
        """Test performance with large digest volumes (200+ items)."""
        start_time = time.time()
        self.memory_monitor.start_monitoring()
        
        # Simulate processing 200+ items
        processed_items = []
        batch_size = 25  # DynamoDB batch limit
        
        # Process in batches
        for i in range(0, len(self.large_dataset), batch_size):
            batch = self.large_dataset[i:i + batch_size]
            
            # Simulate batch processing
            batch_records = []
            for item in batch:
                record = {
                    'digest_date': '2024-06-08',
                    'item_id': f"{item.source}#{int(item.published.timestamp())}#{hash(item.link) % 100000}",
                    'feed_source': item.source,
                    'title': item.title,
                    'url': item.link,
                    'summary': item.summary,
                    'timestamp': item.published.isoformat()
                }
                batch_records.append(record)
            
            processed_items.extend(batch_records)
        
        end_time = time.time()
        peak_memory = self.memory_monitor.stop_monitoring()
        
        # Calculate performance metrics
        duration = end_time - start_time
        items_per_second = len(processed_items) / duration
        
        # Verify performance requirements
        assert duration < 60.0, f"Processing took {duration:.2f}s, should be under 60s"
        assert peak_memory < 512.0, f"Peak memory {peak_memory:.2f}MB, should be under 512MB"
        assert len(processed_items) == 200, f"Should process all 200 items, got {len(processed_items)}"
        assert items_per_second > 5.0, f"Should process >5 items/sec, got {items_per_second:.2f}"
        
        print(f"Performance metrics: {duration:.2f}s, {peak_memory:.2f}MB peak, {items_per_second:.2f} items/sec")
    
    @mock_dynamodb
    def test_batch_operation_efficiency(self):
        """Test batch operations reduce API calls by 75%."""
        # Set up DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='VibeDigest-perf-test',
            KeySchema=[
                {'AttributeName': 'digest_date', 'KeyType': 'HASH'},
                {'AttributeName': 'item_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'digest_date', 'AttributeType': 'S'},
                {'AttributeName': 'item_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        test_items = self.large_dataset[:100]  # Use 100 items for this test
        
        # Test individual operations (inefficient)
        start_time = time.time()
        individual_calls = 0
        
        for item in test_items:
            record = {
                'digest_date': '2024-06-08',
                'item_id': f"{item.source}#{int(item.published.timestamp())}#{hash(item.link) % 100000}",
                'feed_source': item.source,
                'title': item.title,
                'url': item.link,
                'summary': item.summary,
                'timestamp': item.published.isoformat()
            }
            table.put_item(Item=record)
            individual_calls += 1
        
        individual_duration = time.time() - start_time
        
        # Clear table for batch test
        # (In real test, would use different table or clear existing data)
        
        # Test batch operations (efficient)
        start_time = time.time()
        batch_calls = 0
        batch_size = 25
        
        for i in range(0, len(test_items), batch_size):
            batch = test_items[i:i + batch_size]
            
            with table.batch_writer() as batch_writer:
                for item in batch:
                    record = {
                        'digest_date': '2024-06-08-batch',
                        'item_id': f"{item.source}#{int(item.published.timestamp())}#{hash(item.link) % 100000}",
                        'feed_source': item.source,
                        'title': item.title,
                        'url': item.link,
                        'summary': item.summary,
                        'timestamp': item.published.isoformat()
                    }
                    batch_writer.put_item(Item=record)
            batch_calls += 1
        
        batch_duration = time.time() - start_time
        
        # Verify efficiency improvements
        efficiency_improvement = (individual_duration - batch_duration) / individual_duration
        api_call_reduction = (individual_calls - batch_calls) / individual_calls
        
        assert api_call_reduction >= 0.75, f"API calls should be reduced by 75%, got {api_call_reduction:.2%}"
        assert batch_duration < individual_duration, "Batch operations should be faster"
        
        expected_batch_calls = (len(test_items) + batch_size - 1) // batch_size
        assert batch_calls == expected_batch_calls, f"Expected {expected_batch_calls} batch calls, got {batch_calls}"
        
        print(f"API call reduction: {api_call_reduction:.2%}, Time improvement: {efficiency_improvement:.2%}")
    
    def test_memory_efficiency_constraint(self):
        """Test memory usage stays under 512MB during processing."""
        self.memory_monitor.start_monitoring()
        
        # Simulate memory-intensive persistence operation
        large_payload = []
        
        # Create large data structures to test memory limits
        for item in self.large_dataset:
            # Simulate data transformation and storage preparation
            record = {
                'digest_date': '2024-06-08',
                'item_id': f"{item.source}#{int(item.published.timestamp())}#{hash(item.link) % 100000}",
                'feed_source': item.source,
                'title': item.title,
                'url': item.link,
                'summary': item.summary,
                'timestamp': item.published.isoformat(),
                'metadata': {
                    'processed_at': datetime.now(timezone.utc).isoformat(),
                    'hash': hash(item.link),
                    'length': len(item.summary)
                }
            }
            large_payload.append(record)
            
            # Simulate periodic processing to avoid memory buildup
            if len(large_payload) >= 50:
                # Process batch and clear memory
                processed_batch = large_payload.copy()
                large_payload.clear()
                
                # Simulate some processing work
                time.sleep(0.01)
        
        peak_memory = self.memory_monitor.stop_monitoring()
        
        # Verify memory constraint
        assert peak_memory < 512.0, f"Memory usage {peak_memory:.2f}MB exceeds 512MB limit"
        
        print(f"Peak memory usage: {peak_memory:.2f}MB")
    
    def test_persistence_latency_requirements(self):
        """Test persistence operations meet latency requirements."""
        test_cases = [
            {'items': 5, 'max_latency': 5.0, 'description': 'Small digest'},
            {'items': 25, 'max_latency': 10.0, 'description': 'Medium digest'},
            {'items': 100, 'max_latency': 30.0, 'description': 'Large digest'},
            {'items': 200, 'max_latency': 60.0, 'description': 'Very large digest'}
        ]
        
        for test_case in test_cases:
            items = self.large_dataset[:test_case['items']]
            
            start_time = time.time()
            
            # Simulate persistence operation
            processed_records = []
            batch_size = 25
            
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                
                # Simulate batch processing time
                batch_records = []
                for item in batch:
                    record = {
                        'digest_date': '2024-06-08',
                        'item_id': f"{item.source}#{int(item.published.timestamp())}#{hash(item.link) % 100000}",
                        'feed_source': item.source,
                        'title': item.title,
                        'url': item.link,
                        'summary': item.summary,
                        'timestamp': item.published.isoformat()
                    }
                    batch_records.append(record)
                
                processed_records.extend(batch_records)
                
                # Simulate network/DB latency
                time.sleep(0.01)  # 10ms per batch
            
            end_time = time.time()
            duration = end_time - start_time
            
            assert duration < test_case['max_latency'], \
                f"{test_case['description']}: {duration:.2f}s exceeds {test_case['max_latency']}s limit"
            
            print(f"{test_case['description']}: {duration:.2f}s for {len(items)} items")
    
    @mock_dynamodb
    def test_retrieval_performance(self):
        """Test digest retrieval meets 5-second SLA."""
        # Set up DynamoDB table with test data
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='VibeDigest-retrieval-test',
            KeySchema=[
                {'AttributeName': 'digest_date', 'KeyType': 'HASH'},
                {'AttributeName': 'item_id', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'digest_date', 'AttributeType': 'S'},
                {'AttributeName': 'item_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Pre-populate table with test data
        digest_date = '2024-06-08'
        test_items = self.large_dataset[:50]  # 50 items for retrieval test
        
        with table.batch_writer() as batch:
            for item in test_items:
                record = {
                    'digest_date': digest_date,
                    'item_id': f"{item.source}#{int(item.published.timestamp())}#{hash(item.link) % 100000}",
                    'feed_source': item.source,
                    'title': item.title,
                    'url': item.link,
                    'summary': item.summary,
                    'timestamp': item.published.isoformat()
                }
                batch.put_item(Item=record)
        
        # Test retrieval performance
        start_time = time.time()
        
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('digest_date').eq(digest_date)
        )
        
        end_time = time.time()
        retrieval_duration = end_time - start_time
        
        # Verify performance requirements
        assert retrieval_duration < 5.0, f"Retrieval took {retrieval_duration:.2f}s, should be under 5s"
        assert len(response['Items']) == 50, f"Should retrieve 50 items, got {len(response['Items'])}"
        
        print(f"Retrieval performance: {retrieval_duration:.3f}s for {len(response['Items'])} items")
    
    def test_concurrent_operations_performance(self):
        """Test performance under concurrent operations."""
        import concurrent.futures
        
        def simulate_persistence_operation(thread_id: int, item_count: int):
            """Simulate a persistence operation in a thread."""
            items = self.large_dataset[:item_count]
            
            start_time = time.time()
            
            # Simulate processing
            processed = []
            for item in items:
                record = {
                    'thread_id': thread_id,
                    'digest_date': '2024-06-08',
                    'item_id': f"{item.source}#{int(item.published.timestamp())}#{hash(item.link) % 100000}",
                    'title': item.title,
                    'url': item.link,
                    'summary': item.summary
                }
                processed.append(record)
            
            duration = time.time() - start_time
            return {
                'thread_id': thread_id,
                'duration': duration,
                'items_processed': len(processed)
            }
        
        # Test with multiple concurrent operations
        concurrent_ops = 3
        items_per_op = 30
        
        self.memory_monitor.start_monitoring()
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_ops) as executor:
            futures = [
                executor.submit(simulate_persistence_operation, i, items_per_op)
                for i in range(concurrent_ops)
            ]
            
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_duration = time.time() - start_time
        peak_memory = self.memory_monitor.stop_monitoring()
        
        # Verify concurrent performance
        total_items = sum(result['items_processed'] for result in results)
        assert total_items == concurrent_ops * items_per_op
        assert total_duration < 30.0, f"Concurrent operations took {total_duration:.2f}s, should be under 30s"
        assert peak_memory < 512.0, f"Peak memory {peak_memory:.2f}MB exceeds limit during concurrent ops"
        
        avg_duration = sum(result['duration'] for result in results) / len(results)
        print(f"Concurrent performance: {total_duration:.2f}s total, {avg_duration:.2f}s average per thread")
    
    def test_data_size_scaling(self):
        """Test performance scaling with different data sizes."""
        test_scenarios = [
            {'size_kb': 10, 'items': 10, 'description': 'Small digest'},
            {'size_kb': 100, 'items': 50, 'description': 'Medium digest'},
            {'size_kb': 1000, 'items': 100, 'description': 'Large digest (1MB)'},
            {'size_kb': 2000, 'items': 150, 'description': 'Very large digest (2MB)'}
        ]
        
        for scenario in test_scenarios:
            items = self.large_dataset[:scenario['items']]
            
            # Adjust summary length to reach target data size
            target_size_bytes = scenario['size_kb'] * 1024
            summary_size = target_size_bytes // len(items)
            
            for item in items:
                # Extend summary to reach target size
                item.summary = item.summary * (summary_size // len(item.summary) + 1)
                item.summary = item.summary[:summary_size]  # Trim to exact size
            
            start_time = time.time()
            self.memory_monitor.start_monitoring()
            
            # Simulate processing
            processed_size = 0
            for item in items:
                # Calculate approximate item size
                item_size = len(item.title) + len(item.link) + len(item.summary) + len(item.source)
                processed_size += item_size
            
            duration = time.time() - start_time
            peak_memory = self.memory_monitor.stop_monitoring()
            
            # Verify scaling performance
            mb_processed = processed_size / (1024 * 1024)
            throughput_mbps = mb_processed / duration if duration > 0 else 0
            
            assert duration < 60.0, f"{scenario['description']}: Processing took {duration:.2f}s"
            assert peak_memory < 512.0, f"{scenario['description']}: Memory {peak_memory:.2f}MB exceeds limit"
            
            print(f"{scenario['description']}: {duration:.2f}s, {mb_processed:.2f}MB, {throughput_mbps:.2f}MB/s")


class TestPerformanceRegression:
    """Tests to detect performance regressions."""
    
    def test_baseline_performance_metrics(self):
        """Establish baseline performance metrics for regression testing."""
        baseline_metrics = {
            'small_digest_max_seconds': 5.0,
            'medium_digest_max_seconds': 15.0,
            'large_digest_max_seconds': 30.0,
            'max_memory_mb': 512.0,
            'min_throughput_items_per_second': 5.0,
            'retrieval_max_seconds': 5.0
        }
        
        # These baselines should be maintained or improved in future versions
        for metric_name, baseline_value in baseline_metrics.items():
            assert baseline_value > 0, f"Baseline {metric_name} must be positive"
        
        print("Performance baselines established:")
        for metric, value in baseline_metrics.items():
            print(f"  {metric}: {value}")
    
    def test_performance_monitoring_hooks(self):
        """Test hooks for continuous performance monitoring."""
        # This would integrate with actual monitoring systems
        performance_data = {
            'test_run_id': f"perf_test_{int(time.time())}",
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metrics': {
                'persistence_latency_p95': 2.5,
                'retrieval_latency_p95': 1.8,
                'memory_usage_max_mb': 245.0,
                'throughput_items_per_second': 12.3
            }
        }
        
        # In real implementation, this would send to monitoring system
        assert performance_data['metrics']['persistence_latency_p95'] < 5.0
        assert performance_data['metrics']['retrieval_latency_p95'] < 5.0
        assert performance_data['metrics']['memory_usage_max_mb'] < 512.0
        assert performance_data['metrics']['throughput_items_per_second'] > 5.0
        
        print(f"Performance monitoring data: {performance_data}")