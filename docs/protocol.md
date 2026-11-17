# Experimental protocol

## Scope and selection

One primary module; a second-module replication is optional. Select among same-season
earlier/later offerings with at least 500 earlier enrollments. Rank eligible pairs
by earlier enrollment count, then module code. Do not select on held-out performance.

OULAD presentation codes supply month, not exact start dates. Use the latest possible
day of the development start month plus recorded course length plus a 30-day assumed
outcome-availability lag. This must precede the earliest possible start of the test
month plus day 14. This is a conservative timing screen under a documented lag
assumption, not proof of actual grade/outcome release dates. Save candidate pairs.

Remove every student appearing anywhere in the later offering from development,
including students not eligible at a later cutoff. Use identifiers only for joins,
grouping, exclusion and local auditing; never as predictors.

## Eligibility and labels

The UCI archive uses `?` for missing fields; parse these explicitly as missing values.

Predictions occur at end of day 14, 28 or 42. A student must have registered on or
before the cutoff and must not have unregistered on or before it. Withdrawn with
known later unregistration date is positive. Pass, Distinction and Fail with no
unregistration date are negative. Exclude missing registration dates, unknown outcomes,
withdrawals without dates, and non-withdrawals with withdrawal dates; count exclusions.
These complete-outcome exclusions are a retrospective data-quality assumption.

## Feature dictionary

| Feature | Definition |
|---|---|
| num_of_prev_attempts | Recorded previous module attempts |
| studied_credits | Recorded study load; assumed available at prediction time |
| highest_education | Recorded highest education; assumed available at prediction time |
| total_clicks | Sum of positive clicks on dates <= cutoff, including negative pre-course dates |
| active_days | Distinct dates with positive clicks by cutoff |
| days_since_last_activity | Cutoff minus last positive activity date; for no activity, cutoff minus min(registration date, 0) plus 1 |
| no_activity | No positive activity observed by cutoff |
| clicks_last_7 | Clicks in [cutoff-6, cutoff] |
| clicks_previous_7 | Clicks in [cutoff-13, cutoff-7] |
| click_change | Recent week minus previous week clicks |
| submissions | Distinct non-exam, non-banked assessments submitted by cutoff |
| assignments_due | Non-exam assessments with known deadline strictly before cutoff |
| overdue | Due assessments with no observed non-banked submission by cutoff |
| submission_rate | Submitted due assessments / assessments due; missing if none due |

Exclude exam records, scores, final outcomes, withdrawal dates, full-course aggregates
and VLE availability-end metadata from predictors. Metadata are assumed to describe
the schedule known at the cutoff; actual schedule revisions are not timestamped.
Unknown assessment deadlines cannot contribute to due/overdue counts. Banked records
are excluded rather than treated as new activity. Unobserved exemptions can inflate
overdue counts for repeat students; report this limitation. No-activity rows remain.

## Training and metrics

Feature groups: background; engagement; engagement plus submission; all. Fit a separate
regularized logistic regression and histogram gradient-boosted classifier per group
and cutoff. Use five shuffled stratified student-grouped folds with seed 678.
Preprocessing is fitted inside folds; empty numeric columns are retained and imputed.
Logistic regression uses scaling. Trees do not. Categorical encoding ignores unseen levels.
No class rebalancing, post-hoc calibration, or early stopping is used in this first protocol.
Select on mean fold recall at 10%; equal scores follow the fixed grid order.

Set alerts to floor(0.1 * eligible N). Resolve equal scores using a seeded random
ordering independent of outcomes. Inactivity ranks never-active students first,
then ranks others by days since activity. Never-active ties receive the same seeded
tie-breaking policy as other ties. Random ranking is one seeded realization, with
expected recall k/N and precision equal to prevalence. A development-prevalence
constant prediction supplies the no-information Brier benchmark.

Report recall, precision, average precision and Brier (probability models only),
sample size, prevalence, number flagged, number of true positives and median lead
time among correctly flagged withdrawals. Brier is a probability error measure;
it does not alone establish calibration.

## Graduate analysis and uncertainty

Compare timings on each changing eligible cohort and on the intersection of all
three eligible test cohorts. The latter conditions on future survival and is a
retrospective diagnostic, not a deployable population definition. Retain the original
trained models and rerank within the common cohort's 10% budget.

Run all four feature groups for both families at each cutoff with the same tuning
protocol. Inspect aggregate true-positive, false-positive, missed-withdrawal and
true-negative feature medians. Do not use these test observations for model revision.

For full-feature model-versus-inactivity comparisons, resample students with replacement
2,000 times, reuse the same indices across methods and recompute each sample's rankings
and budget. Report percentile 95% intervals for paired differences in recall, precision
and average precision. Bootstrap does not retrain models or estimate between-offering
uncertainty. Intervals are descriptive without multiplicity adjustment.

## Submission audit and exploratory additions

The course paper is submitted separately and is intentionally excluded from this repository.
The primary model protocol and test results remain unchanged. After the original
test run, representative error cases and frozen-score budget sensitivity (5%, 15%,
20%, plus an interactive 5–20% range) were added for explanation. These are
retrospective analyses, not a new validation set or a reason to change the primary
10% budget. Reference snapshot hashes are included. Exact split IDs and CV fold membership are regenerated locally by the reproduction workflow; row-level exports are excluded from Git.
