# Circuit Breaker UI Documentation

## Overview

The Circuit Breaker UI allows users to configure circuit breaker settings for individual agents through the Agent Management interface. This provides fine-grained control over resilience behavior per agent.

## Features

### 1. Agent Form Integration

Circuit breaker configuration is integrated into the Agent Create/Edit form with the following fields:

#### Enable/Disable Toggle
- **Location**: Circuit Breaker section header
- **Default**: Enabled (true)
- **Description**: Master switch to enable/disable circuit breaker for this agent

#### Configuration Fields (when enabled)

1. **Failure Threshold**
   - **Type**: Number (integer)
   - **Default**: 5
   - **Description**: Number of consecutive failures before opening the circuit
   - **Validation**: Must be a positive integer
   - **Example**: 5 means circuit opens after 5 consecutive failures

2. **Failure Rate Threshold**
   - **Type**: Number (decimal)
   - **Default**: 0.5
   - **Range**: 0.0 to 1.0
   - **Description**: Failure rate percentage to trigger circuit opening
   - **Validation**: Must be between 0 and 1
   - **Example**: 0.5 means circuit opens when 50% of calls fail

3. **Timeout (seconds)**
   - **Type**: Number (integer)
   - **Default**: 60
   - **Description**: Time circuit stays open before attempting recovery
   - **Validation**: Must be a positive integer
   - **Example**: 60 means circuit stays open for 60 seconds

4. **Half-Open Max Calls**
   - **Type**: Number (integer)
   - **Default**: 3
   - **Description**: Number of test calls allowed during recovery testing
   - **Validation**: Must be a positive integer
   - **Example**: 3 means allow 3 test calls to verify recovery

5. **Window Size (seconds)**
   - **Type**: Number (integer)
   - **Default**: 120
   - **Description**: Sliding window size for failure rate calculation
   - **Validation**: Must be a positive integer
   - **Example**: 120 means calculate failure rate over last 2 minutes

## User Interface

### Agent Creation Flow

1. Navigate to **Agents** page
2. Click **Create Agent** button
3. Fill in basic information (name, URL, description)
4. Configure authentication if needed
5. Set timeout and retry configuration
6. **Circuit Breaker Section**:
   - Toggle **Enabled** checkbox (on by default)
   - Adjust thresholds based on agent characteristics
   - Review default values (suitable for most cases)
7. Click **Create Agent**

### Agent Editing Flow

1. Navigate to **Agents** page
2. Click **Edit** on an existing agent
3. Scroll to **Circuit Breaker** section
4. Modify configuration as needed
5. Click **Update Agent**

## Visual Design

### Circuit Breaker Section

```
┌─────────────────────────────────────────────────┐
│ Circuit Breaker                    [✓] Enabled  │
├─────────────────────────────────────────────────┤
│ Circuit breaker prevents cascading failures by  │
│ automatically stopping calls to failing agents. │
│                                                  │
│ ┌──────────────────┬──────────────────────────┐ │
│ │ Failure Threshold│ Failure Rate Threshold   │ │
│ │ [    5    ]      │ [   0.5   ]              │ │
│ │ Consecutive...   │ Rate (0.0-1.0) to...     │ │
│ └──────────────────┴──────────────────────────┘ │
│                                                  │
│ ┌──────────────────┬──────────────────────────┐ │
│ │ Timeout (seconds)│ Half-Open Max Calls      │ │
│ │ [   60    ]      │ [    3    ]              │ │
│ │ Time circuit...  │ Test calls during...     │ │
│ └──────────────────┴──────────────────────────┘ │
│                                                  │
│ ┌──────────────────────────────────────────────┐│
│ │ Window Size (seconds)                        ││
│ │ [   120   ]                                  ││
│ │ Sliding window for failure rate calculation ││
│ └──────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘
```

### Styling

- **Section Header**: Bold, with toggle on the right
- **Help Text**: Small, gray text explaining the feature
- **Fields**: Two-column grid layout for compact display
- **Field Labels**: Medium weight, dark gray
- **Field Hints**: Small, light gray text below each field
- **Validation Errors**: Red text with alert icon
- **Border**: Left border in blue when enabled

## Default Values

The UI provides sensible defaults suitable for most agents:

| Field | Default | Rationale |
|-------|---------|-----------|
| Enabled | true | Circuit breaker should be on by default for resilience |
| Failure Threshold | 5 | Allows some transient failures before opening |
| Failure Rate | 0.5 | Opens when half of calls fail |
| Timeout | 60s | One minute is reasonable for most services to recover |
| Half-Open Calls | 3 | Three test calls provide good confidence |
| Window Size | 120s | Two minutes captures recent behavior |

## Use Cases

### 1. Critical Production Agent

For agents that must be highly available:

```
Enabled: ✓
Failure Threshold: 3
Failure Rate: 0.7
Timeout: 30s
Half-Open Calls: 2
Window Size: 60s
```

**Rationale**: Lower thresholds and shorter timeout for faster failure detection and recovery.

### 2. Non-Critical Background Agent

For agents that can tolerate more failures:

```
Enabled: ✓
Failure Threshold: 10
Failure Rate: 0.3
Timeout: 120s
Half-Open Calls: 5
Window Size: 300s
```

**Rationale**: Higher thresholds and longer timeout to avoid unnecessary circuit opening.

### 3. Development/Testing Agent

For agents in development:

```
Enabled: ✗
```

**Rationale**: Disable circuit breaker during development to see all errors.

## Validation

The form validates all circuit breaker fields:

- **Failure Threshold**: Must be > 0
- **Failure Rate**: Must be between 0.0 and 1.0
- **Timeout**: Must be > 0
- **Half-Open Calls**: Must be > 0
- **Window Size**: Must be > 0

Error messages appear below invalid fields with a red alert icon.

## API Integration

When creating or updating an agent, the circuit breaker configuration is sent as:

```json
{
  "name": "MyAgent",
  "url": "https://api.example.com",
  "circuit_breaker_config": {
    "enabled": true,
    "failure_threshold": 5,
    "failure_rate_threshold": 0.5,
    "timeout_seconds": 60,
    "half_open_max_calls": 3,
    "window_size_seconds": 120
  }
}
```

## Future Enhancements

### 1. Circuit Breaker Status Display

Show real-time circuit breaker state in the agent list:

```
Agent Name          Status    Circuit Breaker
─────────────────────────────────────────────
DataFetcher         Active    🟢 CLOSED
UnreliableService   Active    🔴 OPEN (45s)
TestAgent           Active    🟡 HALF_OPEN
```

### 2. Circuit Breaker Metrics

Display circuit breaker metrics on agent detail page:

- Current state (CLOSED/OPEN/HALF_OPEN)
- Time in current state
- Recent failure rate
- Number of times opened (last 24h)
- Last state transition timestamp

### 3. Manual Circuit Control

Add buttons to manually control circuit state:

- **Force Open**: Manually open circuit for maintenance
- **Force Close**: Manually close circuit after fixing issues
- **Reset**: Clear circuit breaker history

### 4. Circuit Breaker History

Show timeline of circuit breaker state changes:

```
Timeline
────────
10:30 AM  Circuit OPENED (5 consecutive failures)
10:31 AM  Circuit HALF_OPEN (timeout elapsed)
10:31 AM  Circuit CLOSED (3 successful test calls)
```

### 5. Alerts and Notifications

Configure alerts for circuit breaker events:

- Email when circuit opens
- Slack notification for prolonged open state
- Dashboard widget showing all open circuits

## Accessibility

The circuit breaker UI follows accessibility best practices:

- **Labels**: All fields have associated labels
- **Help Text**: Descriptive text for each field
- **Validation**: Clear error messages
- **Keyboard Navigation**: Full keyboard support
- **Screen Readers**: Proper ARIA labels
- **Color Contrast**: Meets WCAG AA standards

## Testing

To test the circuit breaker UI:

1. **Create Agent with Circuit Breaker**:
   - Create new agent with default circuit breaker settings
   - Verify configuration is saved
   - Check API request includes circuit_breaker_config

2. **Edit Circuit Breaker Settings**:
   - Edit existing agent
   - Modify circuit breaker values
   - Verify changes are saved

3. **Disable Circuit Breaker**:
   - Uncheck "Enabled" toggle
   - Verify fields are hidden
   - Verify configuration still sent with enabled=false

4. **Validation**:
   - Enter invalid values (negative, out of range)
   - Verify error messages appear
   - Verify form cannot be submitted with errors

5. **Default Values**:
   - Create new agent
   - Verify default values are populated
   - Verify defaults are sensible

## Troubleshooting

### Issue: Circuit Breaker Settings Not Saved

**Solution**: Check browser console for API errors. Verify backend supports circuit_breaker_config field.

### Issue: Validation Errors Not Clearing

**Solution**: Ensure handleChange function clears errors for the modified field.

### Issue: Toggle Not Working

**Solution**: Verify handleChange handles boolean values correctly.

## Related Documentation

- [Circuit Breaker Backend Documentation](../docs/circuit_breaker.md)
- [Circuit Breaker Deployment Guide](../CIRCUIT_BREAKER_DEPLOYMENT.md)
- [Agent API Documentation](../API_DOCUMENTATION.md)
