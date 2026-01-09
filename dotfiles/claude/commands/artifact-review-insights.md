---
description: Analyze accumulated self-review logs for patterns and learning
allowed-tools: Read, Bash
---

# Artifact Review Insights

Analyze accumulated data from self-review runs to identify patterns, measure effectiveness, and close the learning loop.

## Log Locations

- **Success log**: `~/.claude/self-review-logs/reviews.jsonl`
- **Error log**: `~/.claude/self-review-logs/reviews.errors.jsonl`

## Your Task

### Step 1: Load the Data

Read both JSONL files. Handle gracefully:
- Missing files (no reviews yet)
- Empty files (directory exists but no data)
- Malformed lines (skip with warning)

### Step 2: Compute Overview Stats

From **success log** (`reviews.jsonl`):

| Metric | Computation |
|--------|-------------|
| Total reviews | Count of records |
| Ready rate | % with status starting "Ready for handoff" |
| Blocked rate | % with status starting "Blocked on" |
| Avg questions/review | Mean of `questions` field |
| Avg gaps/review | Mean of `gaps.total` |
| Avg revisions/review | Mean of `revisions` |
| Validation rate | Mean of `validated / questions` (how many questions confirmed correct) |

From **error log** (`reviews.errors.jsonl`):

| Metric | Computation |
|--------|-------------|
| Schema failures | Count of records |
| Failure rate | `errors / (successes + errors)` |
| Common errors | Frequency of each error code in `validation_errors` |

### Step 3: Analyze Patterns

**Gap Severity Distribution**:
- What % of gaps are Critical vs Significant vs Minor?
- Are Critical gaps correlated with Blocked status?

**Effectiveness Ratios**:
- Questions → Gaps ratio (how many questions surface actual gaps?)
- Gaps → Revisions ratio (are identified gaps being addressed?)
- If validated < questions, what's the false positive rate?

**Blocking Patterns** (if sufficient Blocked reviews):
- Extract blocking reasons from status field
- Categorize common blockers

**Error Patterns** (from error log):
- Which validation errors occur most?
- Are certain fields consistently problematic?
- This feeds back into P5 prompt improvements

### Step 4: Identify Actionable Insights

Based on the data, identify:

1. **Process Health**: Is the review system working? (success rate, ready rate)
2. **Question Quality**: Are questions surfacing real issues? (gaps/questions ratio)
3. **Revision Effectiveness**: Are gaps being addressed? (revisions/gaps ratio)
4. **Schema Compliance**: Is P5 following the output format? (error patterns)
5. **Improvement Opportunities**: What should change?

### Step 5: Present Results

Format your output as:

```
ARTIFACT REVIEW INSIGHTS
========================

DATA SUMMARY
- Reviews analyzed: [N] successful, [M] schema failures
- Date range: [earliest] to [latest]
- Success rate: [X]%

REVIEW OUTCOMES
- Ready for handoff: [N] ([X]%)
- Blocked: [N] ([X]%)

EFFECTIVENESS METRICS
- Avg questions per review: [N]
- Avg gaps identified: [N] ([X]% of questions)
- Avg revisions made: [N] ([X]% of gaps addressed)
- Validation rate: [X]% of findings confirmed correct

GAP SEVERITY DISTRIBUTION
- Critical: [N] ([X]%)
- Significant: [N] ([X]%)
- Minor: [N] ([X]%)

[If sufficient blocked reviews:]
COMMON BLOCKERS
1. [Reason] - [N] occurrences
2. [Reason] - [N] occurrences

[If error log has data:]
SCHEMA COMPLIANCE ISSUES
- [error_code]: [N] occurrences
- [error_code]: [N] occurrences
→ Recommendation: [What to fix in P5 prompt]

ACTIONABLE INSIGHTS
1. [Insight based on data]
2. [Insight based on data]
3. [Insight based on data]

RAW DATA AVAILABLE
- Success log: ~/.claude/self-review-logs/reviews.jsonl
- Error log: ~/.claude/self-review-logs/reviews.errors.jsonl
```

## Handling Edge Cases

**No data yet**:
```
No review data found. Run /artifact-review on some artifacts to generate data.
Log locations:
- ~/.claude/self-review-logs/reviews.jsonl (successful reviews)
- ~/.claude/self-review-logs/reviews.errors.jsonl (schema failures)
```

**Only errors, no successes**:
Focus analysis on error patterns. This indicates P5 output format needs adjustment.

**Very few reviews** (< 5):
Present raw data instead of statistics. Note that patterns require more data.

## Begin

Read the log files and produce the insights report.
