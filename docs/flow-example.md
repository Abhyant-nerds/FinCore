# Account Record Change Flow Example

This example shows how a LangChain Deep Agent coordinates an account record change request while LangGraph provides durable state, checkpoints, interrupts, and resume behavior underneath.

The important boundary is:

- The Deep Agent understands, plans, coordinates tools, and explains.
- Validators produce deterministic or structured validation results.
- The policy engine calculates the official disposition.
- LangGraph persists workflow state and handles interrupts.
- The command service is the only component allowed to execute approved mutations.

## Example Input

```json
{
  "request_id": "REQ-20260717-00124",
  "idempotency_key": "branch-portal-784512",
  "tenant_id": "BANK-001",
  "operation": "UPDATE",
  "entity_type": "ACCOUNT",
  "record_id": "ACC-100582",
  "account_type": "PRIVATE_INDIVIDUAL",
  "expected_record_version": 18,
  "requested_by": {
    "user_id": "USR-501",
    "role": "OPERATIONS_USER",
    "branch_id": "PUNE-017",
    "channel": "BRANCH_PORTAL",
    "authentication_level": "MFA"
  },
  "changes": [
    {
      "field_path": "account_holder_name",
      "action": "REPLACE",
      "old_value": "Rahul Kumar",
      "new_value": "Rahul K. Kumar",
      "reason": "Customer requested a name correction"
    }
  ],
  "evidence": [
    {
      "document_id": "DOC-99218",
      "document_type": "IDENTITY_PROOF",
      "purpose": "NAME_CHANGE"
    }
  ],
  "submitted_at": "2026-07-17T08:30:00+05:30"
}
```

## 1. Gateway Validates Schema

The platform first checks the request against the account record change input schema.

Required fields include:

```text
request_id
idempotency_key
tenant_id
operation
entity_type
account_type
requested_by
changes
submitted_at
```

The schema also checks:

```text
operation is ADD, UPDATE, or DELETE
entity_type is ACCOUNT
submitted_at is date-time
```

If schema validation fails, the Deep Agent does not reason over the request. The workflow returns a schema validation error.

## 2. Deep Agent Starts

The LangChain Deep Agent receives the structured `ChangeRequest`.

It identifies:

```text
operation: UPDATE
account type: PRIVATE_INDIVIDUAL
record: ACC-100582
changed field: account_holder_name
old value: Rahul Kumar
new value: Rahul K. Kumar
evidence: identity proof document DOC-99218
```

The agent uses the request-understanding skill to normalize intent and detect missing request data. It does not approve, reject, authorize, or mutate data.

## 3. Idempotency Is Registered

The platform records an idempotency key scoped to the tenant and source channel:

```text
BANK-001 + BRANCH_PORTAL + branch-portal-784512
```

If this exact request was already processed, the system returns the prior result and avoids duplicate validation or mutation.

## 4. Authorization Is Checked

A deterministic authorization validator checks whether the requester is allowed to request this change:

```text
user: USR-501
role: OPERATIONS_USER
branch: PUNE-017
channel: BRANCH_PORTAL
authentication: MFA
operation: UPDATE
field: account_holder_name
```

Missing or unclear authorization must not be treated as a pass. It must produce a blocking validation result, an `INDETERMINATE` result, or a request for more information depending on the applicable rule.

## 5. Current Record Is Loaded

The agent calls a narrow, typed record tool:

```text
get_record_snapshot(record_id="ACC-100582", tenant_id="BANK-001")
```

Example response:

```json
{
  "record_id": "ACC-100582",
  "entity_type": "ACCOUNT",
  "account_type": "PRIVATE_INDIVIDUAL",
  "version": 18,
  "status": "ACTIVE",
  "fields": {
    "account_holder_name": "Rahul Kumar",
    "customer_id": "CUST-901",
    "country": "IN"
  },
  "relationships": [],
  "restrictions": [],
  "last_updated_at": "2026-07-16T10:12:00+05:30"
}
```

The agent can inspect this snapshot, but it cannot modify the account database.

## 6. Operation Preconditions Are Checked

Because this is an `UPDATE`, deterministic checks include:

```text
record exists
record is active
old value matches current value
expected_record_version matches current version
field is mutable
```

For this example:

```text
expected_record_version = 18
current version = 18
```

The version check passes. If the current version were `19`, the policy path would reject or stop the request due to version conflict.

## 7. Proposed Record Is Built

A deterministic service applies the change set to the current snapshot.

Before:

```json
{
  "account_holder_name": "Rahul Kumar"
}
```

After:

```json
{
  "account_holder_name": "Rahul K. Kumar"
}
```

Proposed record:

```json
{
  "record_id": "ACC-100582",
  "entity_type": "ACCOUNT",
  "account_type": "PRIVATE_INDIVIDUAL",
  "base_version": 18,
  "fields": {
    "account_holder_name": "Rahul K. Kumar",
    "customer_id": "CUST-901",
    "country": "IN"
  },
  "changed_fields": ["account_holder_name"]
}
```

This construction is deterministic. The agent does not invent the proposed state.

## 8. Profile And Rules Are Loaded

For `PRIVATE_INDIVIDUAL`, the account profile requires:

```yaml
required_fields:
  - account_holder_name
  - customer_id
  - country

name_policy:
  strategy: VERIFIED_PERSON_IDENTITY

delete_policy:
  mode: CLOSE
  human_approval_required: true
```

The rule resolver selects applicable rules using:

```text
entity_type = ACCOUNT
operation = UPDATE
account_type = PRIVATE_INDIVIDUAL
changed_fields = account_holder_name
```

Applicable rule:

```yaml
rule_id: PRIVATE_NAME_MATCH
version: "2.1"
validator_name: CUSTOMER_MASTER_NAME_MATCH
minimum_similarity: 0.96
require_document_match: true
on_failure: HUMAN_REVIEW
```

Also applicable:

```yaml
rule_id: RECORD_VERSION_MATCH
version: "1.0"
validator_name: RECORD_VERSION_VALIDATOR
on_failure: REJECT
```

## 9. Validation Plan Is Created

The Deep Agent creates a validation plan only from resolved rules and allowed tools.

Example plan:

```text
1. Run record version validator.
2. Confirm mandatory profile fields.
3. Retrieve customer master name.
4. Compare requested name to customer master.
5. Retrieve identity document facts.
6. Compare document name to requested name.
7. Aggregate results.
8. Ask policy engine for official decision.
```

The agent may coordinate tool usage, but it cannot invent additional business rules.

## 10. Deterministic Validators Run

Example deterministic result:

```json
{
  "rule_id": "RECORD_VERSION_MATCH",
  "rule_version": "1.0",
  "validator_name": "RECORD_VERSION_VALIDATOR",
  "status": "PASS",
  "severity": "CRITICAL",
  "field_paths": ["record.version"],
  "message": "Expected record version matches current record version.",
  "observed_value": 18,
  "expected_value": 18,
  "blocking": false
}
```

## 11. Evidence Analysis Runs

The evidence-analysis subagent receives only evidence tools. It may call:

```text
get_document(DOC-99218)
extract_document_fields(document_id=DOC-99218, fields=["person_name"])
compare_document_fact(...)
```

Example validation result:

```json
{
  "rule_id": "PRIVATE_NAME_MATCH",
  "rule_version": "2.1",
  "validator_name": "CUSTOMER_MASTER_NAME_MATCH",
  "status": "WARNING",
  "severity": "ERROR",
  "field_paths": ["account_holder_name"],
  "message": "Requested name is compatible but below strict normalized threshold.",
  "expected_value": "Rahul Kumar",
  "observed_value": "Rahul K. Kumar",
  "evidence_references": ["DOC-99218:page=1"],
  "confidence": 0.91,
  "blocking": false,
  "retryable": false
}
```

Because the rule requires `minimum_similarity: 0.96`, a confidence of `0.91` is not a clean pass.

## 12. Policy Engine Calculates Decision

The Deep Agent does not calculate the official disposition.

The policy engine applies the decision matrix:

```text
critical blocking failure -> REJECT
mandatory information missing -> REQUEST_INFORMATION
material semantic uncertainty -> HUMAN_REVIEW
all mandatory validations passed -> AUTO_APPROVE
```

In this example:

```text
name match is compatible but below strict threshold
semantic uncertainty exists
rule on_failure = HUMAN_REVIEW
```

Official disposition:

```text
HUMAN_REVIEW
```

## 13. Human Review Interrupt

LangGraph durability is used here. The workflow checkpoints state, creates a review task, and pauses.

Review task:

```json
{
  "request_id": "REQ-20260717-00124",
  "field": "account_holder_name",
  "before_value": "Rahul Kumar",
  "requested_value": "Rahul K. Kumar",
  "authoritative_value": "Rahul Kumar",
  "failed_or_uncertain_rule": "PRIVATE_NAME_MATCH",
  "evidence": ["DOC-99218:page=1"],
  "allowed_actions": [
    "APPROVE",
    "REJECT",
    "EDIT_VALUE",
    "REQUEST_INFORMATION",
    "ESCALATE"
  ]
}
```

The agent can explain the issue, but it cannot approve the change itself.

## 14. Reviewer Responds

Example reviewer response:

```json
{
  "review_task_id": "REV-7781",
  "action": "APPROVE",
  "reviewed_by": "USR-900",
  "comments": "Identity document supports abbreviated middle initial."
}
```

The workflow resumes from the checkpoint.

## 15. Command Is Prepared

Only after approval does the system prepare a command:

```json
{
  "command_id": "CMD-REQ-20260717-00124-001",
  "request_id": "REQ-20260717-00124",
  "command_type": "UPDATE_ACCOUNT_RECORD",
  "record_id": "ACC-100582",
  "expected_record_version": 18,
  "mutations": [
    {
      "field_path": "account_holder_name",
      "old_value": "Rahul Kumar",
      "new_value": "Rahul K. Kumar"
    }
  ],
  "approval_reference": "REV-7781",
  "policy_decision_reference": "DEC-REQ-20260717-00124"
}
```

## 16. Command Service Executes

The Deep Agent does not execute the database write.

The command service rechecks:

```text
authorization
approval reference
record version is still 18
mutation is allowed
command has not already executed
```

Then it executes the approved mutation.

## 17. Audit And Events Are Written

The system persists:

```text
request
field changes
validation executions
tool executions
agent run metadata
policy decision
review task
command
execution result
audit events
outbox events
```

Example event:

```text
ChangeExecutionCompleted
```

## 18. Final Output

```json
{
  "request_id": "REQ-20260717-00124",
  "status": "COMPLETED",
  "disposition": "HUMAN_REVIEW",
  "policy_version": "2026.07.1",
  "field_results": [
    {
      "field_path": "account_holder_name",
      "decision": "APPROVED_AFTER_REVIEW",
      "validations": [
        {
          "rule_id": "RECORD_VERSION_MATCH",
          "status": "PASS"
        },
        {
          "rule_id": "PRIVATE_NAME_MATCH",
          "status": "WARNING",
          "message": "Requested name was below strict normalized threshold and required review."
        }
      ]
    }
  ],
  "review_task": {
    "review_task_id": "REV-7781",
    "action": "APPROVE"
  },
  "execution_result": {
    "command_id": "CMD-REQ-20260717-00124-001",
    "status": "EXECUTED",
    "new_record_version": 19
  }
}
```

## Summary

```text
Schema validates the request.
Deep Agent understands and coordinates.
Tools gather facts.
Validators produce structured results.
Policy engine decides.
LangGraph pauses and resumes when needed.
Command service executes approved mutation.
Audit preserves rule, evidence, tool, model, and policy-version provenance.
```
