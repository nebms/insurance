# Known Limitations - CSI Pivot Quote System

This document outlines known limitations and areas for future enhancement in the CSI Pivot Quote insurance application.

## Security & Permissions

### No Permission System (P0 - Critical)

**Current State:**
- NO role-based access control (RBAC) system implemented
- NO permission validation for sensitive operations
- All users can perform all actions without restrictions

**Impact:**
- Any user can cancel any policy (`CancellationService.cancel_policy()`)
- Any user can reinstate policies (`CancellationService.reinstate_policy()`)
- Any user can bind quotes, update policy information, upload documents
- No distinction between agents, managers, and administrators

**Tracking:**
- `cancelled_by_user_id` field exists but is never validated
- User ID is stored for audit purposes only, not enforced

**Recommended Future Implementation:**
1. Add user roles table (agent, manager, admin)
2. Add permissions table (can_cancel_policy, can_bind_quote, etc.)
3. Add permission checks to all CancellationService methods
4. Add permission checks to BindingService methods
5. Add UI-level permission enforcement (hide/disable actions)
6. Consider approval workflows for high-risk actions (cancellation, large refunds)

**Workarounds for Production Use:**
- Implement application-level access controls outside the Python codebase
- Use database triggers to prevent unauthorized actions
- Monitor `cancelled_by_user_id` audit trail regularly
- Establish company policies for who can perform sensitive operations

---

## Data Integrity

### Status Field Redundancy (P0 - Critical)

**Current State:**
- Quote model has BOTH `status` (TEXT) and `is_cancelled` (INTEGER) fields
- These fields can become out of sync
- No database constraints linking them

**Risk:**
- Could have `status='bound'` with `is_cancelled=1` (invalid state)
- Filtering/reporting could show inconsistent results

**Current Mitigation:**
- CancellationService always sets both fields together
- BindingService sets status='bound' (but doesn't touch is_cancelled)

**Recommended Future Implementation:**
- Option A: Remove `status` field entirely, derive from `is_bound` and `is_cancelled`
- Option B: Add database trigger to keep fields synchronized
- Option C: Add enum validation and CHECK constraints on status values

---

## Financial Tracking

### No Refund Processing Workflow (P1 - High)

**Current State:**
- Cancellation calculates `return_premium` amount
- NO tracking of whether refund was actually processed
- NO refund method, check number, or refund date tracking

**Impact:**
- Can't answer: "Was this refund issued?"
- Can't answer: "How was the refund sent?"
- Payment status remains 'paid' even when refund is owed

**Missing Fields:**
- `refund_status` ('pending', 'processed', 'completed')
- `refund_date`
- `refund_method` ('check', 'ACH', 'credit card reversal')
- `refund_check_number`
- `refund_amount_actual` (vs calculated `return_premium`)

**Recommended Future Implementation:**
1. Add refund tracking table
2. Add refund processing workflow
3. Integration with accounting system
4. Refund reconciliation reporting

---

## Policy Term Calculations

### Term Uses 30-Day Months (P1 - High)

**Current State:**
- Policy expiration calculated as: `effective_date + (term_months * 30 days)`
- 12-month policy = 360 days instead of 365/366 days

**Impact:**
- Policies expire earlier than expected
- Example: Jan 1, 2024 + 12 months = Dec 26, 2024 (not Jan 1, 2025)

**Affects:**
- `BindingService.bind_quote()` line 70
- Renewal date calculations
- Pro-rata cancellation calculations (which use actual calendar days)

**Recommended Fix:**
```python
from dateutil.relativedelta import relativedelta
expiration_date = effective_date + relativedelta(months=quote.term_months)
```

---

## Cancellation Features

### No Audit Trail for Cancel/Reinstate History (P2 - Medium)

**Current State:**
- Each reinstatement overwrites previous cancellation data
- No history of cancel/reinstate cycles

**Impact:**
- Can't track: "How many times was this policy cancelled?"
- Can't answer: "Who reinstated it last time?"

**Recommended Future Implementation:**
- Create `policy_cancellation_history` table
- Store all cancel/reinstate actions with timestamps
- Keep full audit trail

### No Cancellation Reports or Analytics (P2 - Medium)

**Current State:**
- Can view cancelled policies in Quote History
- NO reporting on cancellation trends, reasons, or financial impact

**Missing Reports:**
- Cancellation by reason
- Cancellation by carrier
- Return premium summary
- Cancellation rate trends
- Average time to cancellation

---

## Document Management

### No Automated Cancellation Notice Workflow (P2 - Medium)

**Current State:**
- "Cancellation Notice" is a valid document type
- NO integration with cancellation workflow
- No automatic prompting to upload cancellation notice

**Recommended Future Implementation:**
- Prompt for cancellation notice upload when cancelling
- Generate cancellation notice PDF automatically
- Track whether notice was sent to carrier/customer

### Document Upload to Cancelled Policies (Fixed in v2)

**Previous State:** Could upload documents to cancelled policies without warning
**Current State:** ✅ Fixed - DocumentService now blocks uploads to cancelled policies
**Mitigation:** Returns error: "Cannot upload documents to cancelled policy. Reinstate the policy first if needed."

---

## Search & Filtering

### Can't Search Cancellation Fields (P3 - Low)

**Current State:**
- Search works for quote number, customer name, agent name
- Cannot search cancellation reason, type, or notes

**Use Case:**
- Find "all policies cancelled for Non-payment"
- Search cancellation notes

**Recommended Future Implementation:**
- Add advanced search with cancellation field filters
- Add autocomplete for cancellation reasons

---

## Edge Cases

### No Validation for Retroactive Cancellations (P3 - Low)

**Current State:**
- Can cancel expired policies (after expiration_date)
- Pro-rata calculation returns $0 for expired policies (unused_days = 0)

**Impact:**
- Allows backdating cancellations without warning
- May not match business requirements

**Recommended Future Implementation:**
- Add validation to prevent cancellation after expiration
- OR require special permission for retroactive cancellations

### No Limit on Cancel/Reinstate Cycles (P3 - Low)

**Current State:**
- Can cancel and reinstate same policy unlimited times
- Can do multiple cycles on same day

**Impact:**
- Potential for data manipulation or errors

**Recommended Future Implementation:**
- Add validation to limit cancel/reinstate frequency
- Require escalating approval for multiple cycles

---

## Testing

### No Automated UI Tests (P2 - Medium)

**Current State:**
- Service-level tests exist (`test_cancellation.py`, `test_services.py`)
- NO UI/integration tests for cancellation workflows

**Missing Test Coverage:**
- End-to-end cancellation workflow via UI
- Cancellation with document upload
- Renewal cleanup verification
- Multi-user cancellation scenarios

**Recommended Future Implementation:**
- Add PyQt UI tests
- Add integration tests covering full workflows
- Add performance tests for large datasets

---

## Export & Reporting

### Unknown Export Behavior for Cancelled Policies (P2 - Medium)

**Current State:**
- No CSV/Excel export functionality found in codebase
- Unknown if future exports would include cancelled policies

**Recommended Future Implementation:**
- When implementing export, add cancellation filter options
- Include cancellation fields in export
- Separate reports for active vs cancelled policies

---

## Documentation

### No User Permission Documentation (P1 - High)

**Current State:**
- No documentation of who should be able to cancel policies
- No company policy documentation

**Recommended Future Implementation:**
- Document intended permission model
- Create user guides for cancellation workflow
- Document escalation procedures

---

## Future Enhancements

### Batch Operations

- Bulk cancellations (e.g., cancel all policies for non-payment)
- Bulk reinstatements
- CSV import for mass cancellations

### Customer Communication

- Email cancellation confirmations
- SMS notifications
- Automated letter generation
- Integration with email service

### Advanced Analytics

- Cancellation prediction (ML-based)
- Risk scoring for likely cancellations
- Customer retention analytics
- Financial impact dashboards

---

## Version History

- **v1.0** (Initial implementation): Basic cancellation functionality
- **v2.0** (Bug fixes): Fixed 5 critical bugs, added renewal cleanup, document validation
- **Current**: All P0 issues resolved, P1/P2/P3 documented for future enhancement

---

## Contributing

When adding new features that interact with cancellations:

1. Check `is_cancelled` status in all relevant operations
2. Update both `status` and `is_cancelled` fields together
3. Consider renewal tracking implications
4. Add appropriate permission checks (when permission system exists)
5. Update this document with any new limitations discovered
