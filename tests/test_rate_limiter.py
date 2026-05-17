"""
Unit tests for TokenBucket Rate Limiter.
"""

import time
import pytest
import threading
from src.utils.rate_limiter import TokenBucket

def test_token_bucket_basic():
    # Capacity: 10 tokens, Fill rate: 2 tokens per second
    bucket = TokenBucket(capacity=10.0, fill_rate=2.0)
    
    # Assert initial state
    assert bucket.get_tokens() == 10.0
    
    # Consume 4 tokens -> should succeed
    assert bucket.consume(4.0) is True
    assert bucket.get_tokens() <= 6.0
    
    # Try to consume 7 tokens -> should fail (only ~6 left)
    assert bucket.consume(7.0) is False
    
    # Consume 5 tokens -> should succeed
    assert bucket.consume(5.0) is True
    assert bucket.get_tokens() <= 1.0

def test_token_bucket_replenish():
    # Capacity: 5 tokens, Fill rate: 10 tokens per second
    bucket = TokenBucket(capacity=5.0, fill_rate=10.0)
    
    # Consume all tokens
    assert bucket.consume(5.0) is True
    assert bucket.get_tokens() < 0.1
    
    # Sleep 0.25 seconds -> should replenish 2.5 tokens
    time.sleep(0.25)
    assert bucket.get_tokens() >= 2.0
    
    # Consume 2 tokens -> should succeed
    assert bucket.consume(2.0) is True

def test_token_bucket_thread_safety():
    bucket = TokenBucket(capacity=100.0, fill_rate=0.0) # No replenishment during test
    
    def worker():
        for _ in range(10):
            bucket.consume(1.0)
            
    threads = [threading.Thread(target=worker) for _ in range(5)]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    # Total consumed: 5 * 10 = 50 tokens
    assert abs(bucket.get_tokens() - 50.0) < 0.001
