# Demo Workflow: Complete Life Insurance Application Processing

## Overview

This workflow demonstrates the full capabilities of the LiteCone Orchestrator by processing a life insurance application from intake to policy activation. It showcases all major workflow patterns and agent coordination.

## Workflow Features Demonstrated

### 1. **Sequential Processing**
- Application intake → Document validation → Assessment → Decision
- Each step builds on the previous step's output

### 2. **Parallel Execution**
- Medical, Financial, and Credit assessments run simultaneously
- Reduces total processing time by 3x
- Demonstrates efficient resource utilization

### 3. **Conditional Logic**
- Document completeness checks
- Risk classification routing
- Approval/decline decision trees

### 4. **Error Handling & Recovery**
- Missing document requests
- Additional medical review requests
- Re-evaluation workflows

## Workflow Steps Breakdown

### Phase 1: Intake & Validation (Steps 1-3)
```
intake_application → validate_documents → check_completeness
```
- **Agents Used**: Intake & Submissions Agent, Cross Validator Agent
- **Purpose**: Receive and validate application completeness

### Phase 2: Parallel Assessment (Steps 4-7)
```
                    ┌─→ medical_summary_extraction ─┐
parallel_initial ──┼─→ financial_assessment ────────┼─→ consolidate
                    └─→ credit_risk_analysis ────────┘
```
- **Agents Used**: Medical Agent, Financial Agent, Credit Arbiter Agent, Industry & Market Agent
- **Purpose**: Comprehensive risk assessment from multiple angles
- **Benefit**: 3x faster than sequential processing

### Phase 3: Underwriting Decision (Steps 8-9)
```
underwriting_decision → evaluate_risk_classification
```
- **Agents Used**: Underwriting Arbiter Agent
- **Purpose**: Determine risk classification and eligibility

### Phase 4: Conditional Routing (Steps 10-16)
```
                    ┌─→ calculate_premium (if standard/preferred)
evaluate_risk ──────┤
                    ├─→ send_decline (if declined)
                    └─→ request_additional_review (if substandard)
                            ↓
                        re_evaluate → final_decision
```
- **Agents Used**: Third Party Interaction Agent, Medical Agent, Underwriting Arbiter Agent
- **Purpose**: Route based on risk level, handle edge cases

### Phase 5: Premium Calculation & Policy Generation (Steps 17-21)
```
                        ┌─→ create_main_policy ──────┐
calculate_premium ──────┼─→ create_riders_document ──┼─→ consolidate_documents → send_approval
                        └─→ create_disclosure_doc ───┘
```
- **Agents Used**: Eric (Health Underwriter), Leo (Life Insurance Underwriter) x3, Cross Validator Agent, Communication Agent
- **Purpose**: Calculate pricing and generate all required documents in parallel
- **Parallel**: Generates 3 document types simultaneously for faster processing

### Phase 6: Activation & Onboarding (Steps 20-23)
```
setup_billing → activate_policy → send_welcome_package
```
- **Agents Used**: Medical Billing Auditing Agent, Aris (Claims Manager), Communication Agent
- **Purpose**: Finalize policy and welcome customer

## Agent Utilization

| Agent | Usage Count | Purpose |
|-------|-------------|---------|
| Intake & Submissions Agent | 1 | Initial application processing |
| Cross Validator Agent | 1 | Document validation |
| Medical Agent | 2 | Health assessment & review |
| Financial Agent | 1 | Financial standing analysis |
| Credit Arbiter Agent | 1 | Credit risk evaluation |
| Industry & Market Agent | 1 | Data consolidation |
| Underwriting Arbiter Agent | 2 | Risk classification decisions |
| Third Party Interaction Agent | 1 | External medical exam coordination |
| Eric (Health Underwriter) | 1 | Premium calculation |
| Leo (Life Insurance Underwriter) | 3 | Policy document generation (parallel) |
| Communication Agent | 4 | Customer notifications |
| Medical Billing Auditing Agent | 1 | Billing setup |
| Aris (Claims Manager) | 1 | Policy activation |

**Total: 13 unique agents, 18+ agent invocations**

## Sample Input

```json
{
  "application": {
    "applicant_info": {
      "name": "John Doe",
      "age": 35,
      "email": "john.doe@example.com",
      "phone": "+1-555-0123"
    },
    "coverage_amount": 500000,
    "billing_preference": "monthly",
    "requested_start_date": "2024-01-01"
  },
  "documents": [
    "medical_records.pdf",
    "financial_statements.pdf",
    "identification.pdf"
  ],
  "medical_documents": ["health_history.pdf", "physician_report.pdf"],
  "financial_documents": ["tax_returns.pdf", "bank_statements.pdf"],
  "credit_data": {"score": 720, "history": "good"},
  "payment_info": {"type": "bank_account", "account": "****1234"}
}
```

## Execution Paths

### Path 1: Standard Approval (Happy Path)
```
Intake → Validate → Parallel Assessment → Underwriting → 
Calculate Premium → Generate Docs → Billing → Activate → Welcome
```
**Duration**: ~45-60 seconds
**Outcome**: Policy issued

### Path 2: Missing Documents
```
Intake → Validate → Missing Docs Request → [END]
```
**Duration**: ~10 seconds
**Outcome**: Request sent to applicant

### Path 3: Additional Medical Review Required
```
Intake → Validate → Parallel Assessment → Underwriting → 
Request Medical Exam → Wait for Results → Re-evaluate → 
Calculate Premium → Generate Docs → Billing → Activate → Welcome
```
**Duration**: ~60-90 seconds
**Outcome**: Policy issued after additional review

### Path 4: Application Declined
```
Intake → Validate → Parallel Assessment → Underwriting → 
Decline Notification → [END]
```
**Duration**: ~30 seconds
**Outcome**: Application declined with reasons

## Key Metrics

- **Total Steps**: 24
- **Parallel Branches**: 2 sets (3 agents each = 6 parallel executions)
- **Conditional Decisions**: 4
- **Agent Types**: 13
- **Execution Paths**: 4 possible outcomes

## How to Run This Demo

### Option 1: Via UI
1. Go to Workflows page
2. Click "Create Workflow"
3. Click "Use Template"
4. Select "Complete Life Insurance Application Processing"
5. Click "Create Workflow"
6. Go to workflow detail page
7. Click "Execute"
8. Provide sample input (see above)
9. Watch the execution in real-time

### Option 2: Via API
```bash
# Create the workflow
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @examples/demo_life_insurance_workflow.json

# Execute the workflow
curl -X POST http://localhost:8000/api/v1/workflows/{workflow_id}/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "application": {...},
      "documents": [...]
    }
  }'
```

### Option 3: Via AI Generator
1. Click "AI Generate" in workflow creation
2. Describe: "Create a complete life insurance application processing workflow with parallel medical, financial, and credit assessments, conditional underwriting decisions, and policy generation"
3. Let AI generate and refine

## What Makes This Demo Impressive

1. **Real-World Complexity**: Mirrors actual insurance underwriting processes
2. **All Patterns**: Sequential, parallel, conditional - all in one workflow
3. **Smart Routing**: Different paths based on risk classification
4. **Error Recovery**: Handles missing docs and additional reviews
5. **Agent Coordination**: 13 specialized agents working together
6. **Scalability**: Parallel execution reduces processing time
7. **Flexibility**: Multiple execution paths based on data
8. **Production-Ready**: Could be used in actual insurance operations

## Customization Ideas

- Add more conditional branches for different risk levels
- Include fraud detection checks
- Add compliance verification steps
- Integrate with external APIs (credit bureaus, medical databases)
- Add human approval steps for high-value policies
- Include policy modification workflows
- Add claims processing workflows

## Visual Flow

```
START
  ↓
Intake Application
  ↓
Validate Documents
  ↓
Complete? ──No──→ Request Missing Docs → END
  ↓ Yes
Parallel Assessment (Medical + Financial + Credit)
  ↓
Consolidate Results
  ↓
Underwriting Decision
  ↓
Risk Level?
  ├─ Standard/Preferred → Calculate Premium
  ├─ Declined → Send Decline → END
  └─ Substandard → Additional Medical Review
                      ↓
                   Re-evaluate
                      ↓
                   Approved? ──No──→ Send Decline → END
                      ↓ Yes
                   Calculate Premium
                      ↓
                   Generate Policy Docs (PARALLEL: Main + Riders + Disclosures)
                      ↓
                   Consolidate Documents
                      ↓
                   Send Approval
                      ↓
                   Setup Billing
                      ↓
                   Activate Policy
                      ↓
                   Send Welcome Package
                      ↓
                    END
```

This workflow showcases the power and flexibility of the LiteCone Orchestrator!
