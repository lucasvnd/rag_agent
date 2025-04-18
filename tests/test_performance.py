import pytest
import asyncio
import time
from pathlib import Path
from typing import List
from fastapi.testclient import TestClient
import statistics
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from main import app
from models.users import UserCreate

@pytest.fixture
def test_client():
    return TestClient(app)

class PerformanceMetrics:
    def __init__(self):
        self.response_times = []
        self.start_time = None
        self.end_time = None
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
    
    def add_response_time(self, time_ms: float, success: bool):
        self.response_times.append(time_ms)
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
    
    def start(self):
        self.start_time = time.time()
    
    def end(self):
        self.end_time = time.time()
    
    @property
    def total_duration(self) -> float:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0
    
    @property
    def requests_per_second(self) -> float:
        if self.total_duration > 0:
            return self.total_requests / self.total_duration
        return 0
    
    @property
    def success_rate(self) -> float:
        if self.total_requests > 0:
            return (self.successful_requests / self.total_requests) * 100
        return 0
    
    @property
    def avg_response_time(self) -> float:
        if self.response_times:
            return statistics.mean(self.response_times)
        return 0
    
    @property
    def p95_response_time(self) -> float:
        if self.response_times:
            return np.percentile(self.response_times, 95)
        return 0
    
    def __str__(self) -> str:
        return f"""
Performance Test Results:
------------------------
Total Requests: {self.total_requests}
Successful Requests: {self.successful_requests}
Failed Requests: {self.failed_requests}
Success Rate: {self.success_rate:.2f}%
Total Duration: {self.total_duration:.2f}s
Requests/Second: {self.requests_per_second:.2f}
Average Response Time: {self.avg_response_time:.2f}ms
95th Percentile Response Time: {self.p95_response_time:.2f}ms
"""

async def measure_response_time(func, *args, **kwargs) -> tuple[float, bool]:
    """Measure response time of an async function in milliseconds."""
    start = time.time()
    try:
        await func(*args, **kwargs)
        success = True
    except Exception:
        success = False
    end = time.time()
    return (end - start) * 1000, success

@pytest.mark.asyncio
async def test_document_upload_performance(
    test_client: TestClient,
    auth_token: str,
    sample_pdf_content: bytes,
    temp_dir: Path
):
    """Test document upload performance under load."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    metrics = PerformanceMetrics()
    
    # Prepare test files
    num_files = 50
    test_files = []
    for i in range(num_files):
        test_file = temp_dir / f"test_{i}.pdf"
        test_file.write_bytes(sample_pdf_content)
        test_files.append(test_file)
    
    async def upload_file(file_path: Path):
        with open(file_path, "rb") as f:
            return test_client.post(
                "/documents/upload",
                files={"file": (file_path.name, f, "application/pdf")},
                headers=headers
            )
    
    # Test concurrent uploads
    metrics.start()
    upload_tasks = [measure_response_time(upload_file, f) for f in test_files]
    results = await asyncio.gather(*upload_tasks)
    metrics.end()
    
    # Record metrics
    for response_time, success in results:
        metrics.add_response_time(response_time, success)
    
    print(metrics)
    
    # Performance assertions
    assert metrics.success_rate > 95  # At least 95% success rate
    assert metrics.avg_response_time < 1000  # Average response time under 1 second
    assert metrics.p95_response_time < 2000  # 95th percentile under 2 seconds

@pytest.mark.asyncio
async def test_search_performance(
    test_client: TestClient,
    auth_token: str
):
    """Test search performance under load."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    metrics = PerformanceMetrics()
    
    async def perform_search(query: str):
        return test_client.post(
            "/search",
            json={"query": query, "limit": 5},
            headers=headers
        )
    
    # Generate test queries
    queries = [f"test query {i}" for i in range(100)]
    
    # Test concurrent searches
    metrics.start()
    search_tasks = [measure_response_time(perform_search, q) for q in queries]
    results = await asyncio.gather(*search_tasks)
    metrics.end()
    
    # Record metrics
    for response_time, success in results:
        metrics.add_response_time(response_time, success)
    
    print(metrics)
    
    # Performance assertions
    assert metrics.success_rate > 95  # At least 95% success rate
    assert metrics.avg_response_time < 500  # Average response time under 500ms
    assert metrics.p95_response_time < 1000  # 95th percentile under 1 second

@pytest.mark.asyncio
async def test_template_generation_performance(
    test_client: TestClient,
    auth_token: str
):
    """Test template generation performance under load."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    metrics = PerformanceMetrics()
    
    # Create a test template first
    template_data = {
        "name": "Performance Test Template",
        "description": "Template for performance testing",
        "content": "Template with {{var1}}, {{var2}}, {{var3}}"
    }
    response = test_client.post(
        "/templates",
        json=template_data,
        headers=headers
    )
    assert response.status_code == 200
    template_id = response.json()["id"]
    
    async def generate_from_template(variables: dict):
        return test_client.post(
            f"/templates/{template_id}/generate",
            json={"variables": variables},
            headers=headers
        )
    
    # Generate test data
    test_data = [
        {
            "var1": f"value1_{i}",
            "var2": f"value2_{i}",
            "var3": f"value3_{i}"
        }
        for i in range(100)
    ]
    
    # Test concurrent template generation
    metrics.start()
    generation_tasks = [measure_response_time(generate_from_template, data) for data in test_data]
    results = await asyncio.gather(*generation_tasks)
    metrics.end()
    
    # Record metrics
    for response_time, success in results:
        metrics.add_response_time(response_time, success)
    
    print(metrics)
    
    # Performance assertions
    assert metrics.success_rate > 95  # At least 95% success rate
    assert metrics.avg_response_time < 200  # Average response time under 200ms
    assert metrics.p95_response_time < 500  # 95th percentile under 500ms

@pytest.mark.asyncio
async def test_system_load_performance(
    test_client: TestClient,
    auth_token: str,
    sample_pdf_content: bytes,
    temp_dir: Path
):
    """Test system performance under mixed workload."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    metrics = PerformanceMetrics()
    
    # Prepare test data
    num_operations = 50
    test_files = []
    for i in range(num_operations):
        test_file = temp_dir / f"test_{i}.pdf"
        test_file.write_bytes(sample_pdf_content)
        test_files.append(test_file)
    
    search_queries = [f"test query {i}" for i in range(num_operations)]
    
    async def mixed_operation(index: int):
        # Randomly choose between upload and search
        if index % 2 == 0:
            # Upload document
            with open(test_files[index // 2], "rb") as f:
                return test_client.post(
                    "/documents/upload",
                    files={"file": (test_files[index // 2].name, f, "application/pdf")},
                    headers=headers
                )
        else:
            # Perform search
            return test_client.post(
                "/search",
                json={"query": search_queries[index // 2], "limit": 5},
                headers=headers
            )
    
    # Test mixed operations
    metrics.start()
    operation_tasks = [measure_response_time(mixed_operation, i) for i in range(num_operations * 2)]
    results = await asyncio.gather(*operation_tasks)
    metrics.end()
    
    # Record metrics
    for response_time, success in results:
        metrics.add_response_time(response_time, success)
    
    print(metrics)
    
    # Performance assertions
    assert metrics.success_rate > 90  # At least 90% success rate under mixed load
    assert metrics.avg_response_time < 1500  # Average response time under 1.5 seconds
    assert metrics.p95_response_time < 3000  # 95th percentile under 3 seconds 