# Problem Model Review Questions

12 questions organized into 4 focused review sets.
Work one set at a time. Do not consider other sets during review.

---

## Set 1: PRIMARY GOAL ALIGNMENT

*Does the model correctly encode and prioritize what we're trying to achieve?*

| #  | Question |
|----|----------|
| 1  | Does "instant redeploy" fully translate from VISION.md into verifiable requirements and success criteria in the problem model? |
| 2  | Is "no manual steps beyond password entry" prominent enough in requirements and constraints that it won't be compromised or diluted during implementation? |
| 3  | Are all "out of scope" items genuinely excluded, not deferred features waiting to creep back in? |

---

## Set 2: SECURITY MODEL

*Are security guarantees robust, enforceable, and verifiable?*

| #  | Question |
|----|----------|
| 4  | Is "secret exposure in git" mitigated with defense-in-depth (multiple safeguards), not just a single "we encrypt" assurance? |
| 5  | Are ALL six invariants in Section 10 actually enforceable at runtime, or are any of them aspirational statements that cannot be guaranteed? |
| 6  | Can the "secrets never appear unencrypted in git" invariant be verified automatically, not just through manual inspection? |

---

## Set 3: CAPTURE MODEL

*Does the model define what to capture and how to ensure completeness?*

| #  | Question |
|----|----------|
| 7  | Does the model define how gitignored essentials are DISCOVERED (not just pattern-matched), and how user validation prevents both false positives (junk captured) and false negatives (essentials missed)? |
| 8  | Does the model establish that complete capture of all necessary ~/.claude/ components is an immutable requirement that the system design must validate and verify through whatever means necessary? |

---

## Set 4: IMPLEMENTATION READINESS

*Can an agent implement this without ambiguity or creating complexity?*

| #  | Question |
|----|----------|
| 9  | Is "complexity creep" addressed with SPECIFIC mitigations beyond vague statements like "strict scope discipline"? |
| 10 | Can a fresh agent implement from this document WITHOUT asking the user any clarifying questions? |
| 11 | Are the functional requirements (FR1-FR8) specific enough that two different implementers would build the same thing? |
| 12 | Are there any ambiguities that could cause an agent to make reasonable but WRONG assumptions about intended behavior? |

---

## Set 5: PERFORMANCE & DISCOVERY EFFICIENCY

*Does the model adequately surface performance concerns and discovery edge cases?*

| #  | Question |
|----|----------|
| 13 | Does the model adequately warn about gitignore evaluation cost (parsing rules, handling negations, nested .gitignore files)? |
| 14 | Is the "content inspection may be needed" requirement clear about *when* and *why* - or could it be misread as "always inspect contents"? |
| 15 | Does anything in the model imply full directory traversal when incremental detection would suffice? |
| 16 | What strategies beyond `~/.claude/projects/` could reduce unnecessary scanning? Are these worth mentioning as design options, or is that design territory? |
| 17 | How should the system handle essential files that don't align with simple "project root" assumptions? (Nested sub-projects, secrets stored outside project roots) |
| 18 | Does the model distinguish between "discovering new projects" (potentially expensive) vs "detecting changes in known projects" (should be cheap, incremental)? |

---

## Review Protocol

```
For each set:
1. Read only that set's questions
2. Review the problem model against those questions
3. Document gaps, issues, or needed revisions
4. Complete revisions for that set before moving to next set
```
