# AXTURION Dashboard Design

The Dashboard is the operational control surface for recruiters and managers.

It visualizes lifecycle health, SLA risk, and workflow performance — without owning business logic.

All rules are enforced by Core.  
The Dashboard interprets and presents.

---

## High-Level Dashboard Structure

```mermaid
graph TD

    Page[Dashboard Page]
    SLA[SLABreachCard]
    TTC[TimeToCloseCard]
    Aging[StageAgingTable]
    Duration[StageDurationTable]

    PolicyHook[usePolicyConfig]
    AgingHook[useStageAging]
    TTCHook[useTimeToClose]
    DurationHook[useStageDurationSummary]

    PolicyAPI[/governance/policy]
    AgingAPI[/reporting/stage-aging]
    TTCAPI[/reporting/time-to-close]
    DurationAPI[/reporting/stage-duration-summary]

    Page --> SLA
    Page --> TTC
    Page --> Aging
    Page --> Duration

    Page --> PolicyHook
    Page --> AgingHook
    Page --> TTCHook
    Page --> DurationHook

    PolicyHook --> PolicyAPI
    AgingHook --> AgingAPI
    TTCHook --> TTCAPI
    DurationHook --> DurationAPI
```

---

## Data Sources

### 1. PolicyConfig

Endpoint:
```
GET /governance/policy
```

Used for:
- stage_aging_sla_days

Fallback behavior:
- If policy fails → default SLA = 7 days

Policy does not mutate lifecycle state.
It only affects interpretation.

---

### 2. Stage Aging

Endpoint:
```
GET /reporting/stage-aging
```

Returns:
- application_id
- workflow_id
- current_stage
- age_seconds

Used for:
- SLA breach detection
- Open application visibility

---

### 3. Time to Close

Endpoint:
```
GET /reporting/time-to-close
```

Used for:
- Performance tracking
- Hiring efficiency insight

---

### 4. Stage Duration Summary

Endpoint:
```
GET /reporting/stage-duration-summary
```

Used for:
- Bottleneck detection
- Workflow performance analysis

Requires workflow_id.

---

## Component Responsibilities

### SLABreachCard

Inputs:
- stageAging.data
- policy.stage_aging_sla_days

Calculates:
- total open applications
- breachCount
- breachPercent

Color rules:
- 0 breaches → green
- ≤20% → amber
- >20% → red

Pure UI aggregation.  
No backend mutation.

---

### TimeToCloseCard

Displays:
- count
- average
- median
- p90
- min
- max

All values formatted via shared duration utility.

---

### StageAgingTable

Displays:
- Application ID
- Current stage
- Age (formatted)

Highlights rows exceeding SLA threshold.

Highlight is interpretation-only.
No state mutation.

---

### StageDurationTable

Displays:
- Stage
- Count
- Avg duration
- Median
- P90

Sorted and formatted consistently.

---

## Rendering Strategy

- All cards handle loading/error safely.
- No component crashes if data is null.
- Fallback defaults prevent UI breakage.
- Hooks are isolated per data source.

Dashboard is resilient.

---

## Identity Model

Each request includes:

- X-Org-Id
- X-User-Id

Read from localStorage:

- org_id
- user_id

Authorization enforced server-side.

---

## Design Principles

1. Dashboard is read-only.
2. Dashboard aggregates but does not enforce.
3. Policy drives interpretation.
4. Reporting drives metrics.
5. UI state must not alter domain state.
6. Every metric must be traceable to a backend endpoint.

---

## Future Extensions (Planned)

Potential improvements:

- Click SLA card → filter StageAgingTable to breached only
- Auto-refresh interval
- SLA breach trend over time
- Workflow selector dropdown
- Recruiter performance overlay

Dashboard should evolve without breaking governance separation.

---

The Dashboard is not a reporting gimmick.

It is the operational risk surface of AXTURION.