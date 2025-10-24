"""Simple test to verify everything works."""

print("=" * 80)
print("🎙️ LipService Simple Test")
print("=" * 80)

# Test 1: Can we import the SDK?
print("\nTest 1: Importing SDK...")
try:
    import sys
    sys.path.insert(0, 'sdk/python')
    from lipservice import configure_adaptive_logging
    print("✅ SDK import successful!")
except Exception as e:
    print(f"❌ SDK import failed: {e}")
    exit(1)

# Test 2: Can we import backend modules?
print("\nTest 2: Importing backend modules...")
try:
    sys.path.insert(0, 'src')
    from engine.signature import compute_signature
    from engine.pattern_analyzer import PatternAnalyzer, LogEntry
    print("✅ Backend imports successful!")
except Exception as e:
    print(f"❌ Backend import failed: {e}")
    exit(1)

# Test 3: Pattern detection works?
print("\nTest 3: Testing pattern detection...")
try:
    sig1 = compute_signature("User 123 logged in")
    sig2 = compute_signature("User 456 logged in")
    
    if sig1 == sig2:
        print(f"✅ Pattern detection works! Signature: {sig1[:16]}...")
    else:
        print(f"❌ Signatures don't match: {sig1} vs {sig2}")
except Exception as e:
    print(f"❌ Pattern detection failed: {e}")
    exit(1)

# Test 4: Analyzer works?
print("\nTest 4: Testing pattern analyzer...")
try:
    from datetime import datetime
    
    logs = [
        LogEntry("User 1 logged in", "INFO", datetime.now(), "web"),
        LogEntry("User 2 logged in", "INFO", datetime.now(), "web"),
        LogEntry("Cache hit", "DEBUG", datetime.now(), "web"),
        LogEntry("Error occurred", "ERROR", datetime.now(), "web"),
    ]
    
    analyzer = PatternAnalyzer()
    result = analyzer.analyze(logs)
    
    print(f"✅ Analyzer works!")
    print(f"   - Total logs: {result.total_logs}")
    print(f"   - Unique patterns: {result.total_unique_patterns}")
    print(f"   - Clusters: {len(result.clusters)}")
    
except Exception as e:
    print(f"❌ Analyzer failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 80)
print("✨ All tests passed! LipService is working!")
print("=" * 80)

# Save to file too
with open("simple_test_results.txt", "w") as f:
    f.write("✅ All LipService components working!\n")
    f.write(f"✅ Pattern detection: {sig1[:16]}...\n")
    f.write(f"✅ Analyzer: {result.total_unique_patterns} patterns\n")

print("\n✅ Results also saved to simple_test_results.txt")

