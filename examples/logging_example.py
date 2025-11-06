"""Example demonstrating structured logging with correlation IDs."""

import asyncio
import logging
from src.utils.logging import setup_logging, set_correlation_id, log_event, clear_correlation_id

# Configure structured JSON logging
setup_logging(log_level='INFO', log_format='json')

logger = logging.getLogger(__name__)


async def simulate_workflow_execution():
    """Simulate a workflow execution with structured logging."""
    
    # Set correlation ID for this workflow run
    run_id = 'run-example-001'
    set_correlation_id(run_id)
    
    # Log workflow start
    log_event(
        logger, 'info', 'workflow_start',
        'Starting workflow execution',
        run_id=run_id,
        workflow_id='wf-001',
        workflow_name='example-workflow'
    )
    
    # Simulate step 1
    await simulate_step('step-1', 'ResearchAgent', run_id)
    
    # Simulate step 2
    await simulate_step('step-2', 'WriterAgent', run_id)
    
    # Log workflow completion
    log_event(
        logger, 'info', 'workflow_complete',
        'Workflow execution completed successfully',
        run_id=run_id,
        workflow_id='wf-001',
        total_steps=2
    )
    
    # Clear correlation ID
    clear_correlation_id()


async def simulate_step(step_id: str, agent_name: str, run_id: str):
    """Simulate a single workflow step execution."""
    
    # Log step start
    log_event(
        logger, 'info', 'step_start',
        f'Starting step {step_id}',
        run_id=run_id,
        step_id=step_id,
        agent_name=agent_name
    )
    
    # Simulate agent call
    task_id = f'task-{step_id}-001'
    correlation_id = f'corr-{run_id}-{step_id}'
    
    log_event(
        logger, 'info', 'agent_call',
        f'Publishing task to agent {agent_name}',
        run_id=run_id,
        step_id=step_id,
        task_id=task_id,
        agent_name=agent_name,
        correlation_id=correlation_id
    )
    
    # Simulate processing delay
    await asyncio.sleep(0.1)
    
    # Log step completion
    log_event(
        logger, 'info', 'step_complete',
        f'Step {step_id} completed successfully',
        run_id=run_id,
        step_id=step_id,
        agent_name=agent_name,
        status='COMPLETED'
    )


async def simulate_error_scenario():
    """Simulate an error scenario with structured logging."""
    
    run_id = 'run-error-001'
    set_correlation_id(run_id)
    
    log_event(
        logger, 'info', 'workflow_start',
        'Starting workflow execution',
        run_id=run_id,
        workflow_id='wf-002'
    )
    
    # Simulate step failure
    step_id = 'step-1'
    agent_name = 'FailingAgent'
    
    log_event(
        logger, 'info', 'step_start',
        f'Starting step {step_id}',
        run_id=run_id,
        step_id=step_id,
        agent_name=agent_name
    )
    
    # Simulate error
    error_message = 'Connection timeout after 30s'
    
    log_event(
        logger, 'error', 'step_failed',
        f'Step {step_id} failed: {error_message}',
        run_id=run_id,
        step_id=step_id,
        agent_name=agent_name,
        status='FAILED',
        error_message=error_message,
        error_type='TimeoutError'
    )
    
    log_event(
        logger, 'error', 'workflow_failed',
        'Workflow execution failed',
        run_id=run_id,
        workflow_id='wf-002',
        failed_step=step_id,
        error=error_message
    )
    
    clear_correlation_id()


async def main():
    """Run logging examples."""
    
    print("=== Example 1: Successful Workflow Execution ===")
    await simulate_workflow_execution()
    
    print("\n=== Example 2: Error Scenario ===")
    await simulate_error_scenario()
    
    print("\n=== Example 3: Text Format ===")
    # Switch to text format
    setup_logging(log_level='INFO', log_format='text')
    
    run_id = 'run-text-001'
    set_correlation_id(run_id)
    
    logger_text = logging.getLogger('text_example')
    
    log_event(
        logger_text, 'info', 'example_event',
        'This is a text-formatted log message',
        run_id=run_id,
        example_field='example_value'
    )
    
    clear_correlation_id()


if __name__ == '__main__':
    asyncio.run(main())
