# Test Circuit Breaker Right Now

## Issue: `docker-compose: command not found`

You're using Docker Compose V2 (`docker compose`) instead of V1 (`docker-compose`).

## ✅ Solution: Use the Fixed Script

The script has been updated to support both versions. Try again:

```bash
./test_circuit_breaker_live.sh
```

## 🚀 Alternative: Test Without Full Infrastructure

If you don't have all services running yet, you can test just the circuit breaker logic:

```bash
./test_circuit_breaker_simple.sh
```

This will run the unit tests that verify the circuit breaker state machine works correctly.

## 📋 Step-by-Step: Start Services First

If services aren't running, start them:

```bash
# Using Docker Compose V2 (your version)
docker compose up -d redis kafka postgres bridge

# Or using Docker Compose V1
docker-compose up -d redis kafka postgres bridge

# Verify services are running
docker compose ps
# or
docker-compose ps
```

Then run the test:

```bash
./test_circuit_breaker_live.sh
```

## 🎯 Quick Test (No Infrastructure Needed)

Want to test the circuit breaker logic right now without any services?

```bash
# Just run the Python unit test
python test_circuit_breaker.py
```

This tests the circuit breaker state machine logic and should complete in ~5 seconds.

Expected output:
```
============================================================
Circuit Breaker Test
============================================================

Test 1: Initial state should be CLOSED
✓ Circuit state: closed

Test 2: Successful calls keep circuit CLOSED
  Call 1: Success 0
  Call 2: Success 1
  Call 3: Success 2
✓ Circuit state: closed

Test 3: Consecutive failures should open circuit
  Call 1 failed: Failure 0
  Call 2 failed: Failure 1
  Call 3 failed: Failure 2
✓ Circuit state: open

Test 4: Calls should fail immediately when circuit is OPEN
  ✓ Call rejected: Circuit breaker is OPEN for agent 'TestAgent'

Test 5: Circuit should transition to HALF_OPEN after timeout
  Waiting 2 seconds...
  ✓ Test call succeeded: Test call
  Circuit state: half_open

Test 6: Successful test calls should close circuit
  Test call 1: Test success 0
  Test call 2: Test success 1
✓ Circuit state: closed

Test 7: Failed test call should reopen circuit
  Circuit opened again
  Test call failed: Test failure
✓ Circuit state: open

============================================================
All tests passed! ✓
============================================================
```

## 🔧 Troubleshooting

### Issue: Services not running

**Check what's running:**
```bash
docker compose ps
# or
docker-compose ps
```

**Start missing services:**
```bash
docker compose up -d redis
docker compose up -d kafka
docker compose up -d postgres
docker compose up -d bridge
```

### Issue: Docker Compose not found

**Check which version you have:**
```bash
# V2 (newer)
docker compose version

# V1 (older)
docker-compose version
```

**Install Docker Compose if needed:**
- V2 comes with Docker Desktop
- V1: https://docs.docker.com/compose/install/

### Issue: Port already in use

**Check what's using port 8090:**
```bash
lsof -i :8090
```

**Kill the process or use a different port:**
```bash
# Kill process
kill <PID>

# Or use different port in test
MOCK_AGENT_PORT=8091 ./test_circuit_breaker_live.sh
```

## 📊 What Each Test Does

### 1. Simple Python Test (`test_circuit_breaker.py`)
- ✅ No infrastructure needed
- ✅ Tests circuit breaker logic only
- ✅ Fast (~5 seconds)
- ❌ Doesn't test full integration

### 2. Simple Shell Test (`test_circuit_breaker_simple.sh`)
- ✅ Runs Python test with nice output
- ✅ Checks dependencies
- ✅ Fast (~5 seconds)
- ❌ Doesn't test full integration

### 3. Live Integration Test (`test_circuit_breaker_live.sh`)
- ✅ Tests full end-to-end flow
- ✅ Tests with real services
- ✅ Tests workflow execution
- ✅ Verifies Redis integration
- ⏱️ Slower (~2 minutes)
- ⚠️ Requires all services running

## 🎯 Recommended Testing Order

1. **First**: Test the logic
   ```bash
   python test_circuit_breaker.py
   ```

2. **Then**: Start services
   ```bash
   docker compose up -d redis kafka postgres bridge
   ```

3. **Finally**: Run full integration test
   ```bash
   ./test_circuit_breaker_live.sh
   ```

## ✅ Success Criteria

Your circuit breaker is working if:

- ✅ Python unit tests pass
- ✅ Circuit opens after failures
- ✅ Circuit closes after recovery
- ✅ Fast failure when circuit is open
- ✅ State transitions logged correctly

## 🆘 Still Having Issues?

Try the manual test from the documentation:

```bash
# 1. Start just Redis
docker compose up -d redis

# 2. Check circuit breaker state manually
docker exec redis redis-cli PING

# 3. Set a test value
docker exec redis redis-cli SET "test" "value"

# 4. Get it back
docker exec redis redis-cli GET "test"
```

If Redis works, the circuit breaker will work!

## 📚 More Help

- **Full Testing Guide**: [CIRCUIT_BREAKER_TESTING_GUIDE.md](CIRCUIT_BREAKER_TESTING_GUIDE.md)
- **Quick Start**: [CIRCUIT_BREAKER_TEST_QUICK_START.md](CIRCUIT_BREAKER_TEST_QUICK_START.md)
- **Usage Guide**: [examples/CIRCUIT_BREAKER_USAGE_GUIDE.md](examples/CIRCUIT_BREAKER_USAGE_GUIDE.md)
