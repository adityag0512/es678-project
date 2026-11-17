# Research reasoning and evidence

## Question and intended claim

How accurately can future withdrawal be predicted at days 14, 28 and 42? Do models
trained on an earlier offering improve on an inactivity ranking when only 10% of
eligible students can be flagged on a later offering?

One row represents a student–module–offering enrollment at a cutoff. A positive
label means withdrawal strictly after that cutoff. Pass, Distinction and academic
Fail count as non-withdrawal. Students who already withdrew are ineligible. This
is ranking for limited outreach capacity, not a diagnosis or causal intervention.

## Data and quality

The public OULAD release has 32,593 enrollment records, 22 offerings across seven
modules and 10,655,280 daily student–resource activity rows. These are enrollment
records, not 32,593 necessarily distinct people. The original archive documentation
contains a conflicting 32,953 count; use the measured CSV counts. See the data
paper and UCI citations in `AI_USE_AND_REFERENCES.md`.

We select FFF 2013J for development and FFF 2014J for test using same-season pairs,
chronology and development cohort size, never predictive performance. The raw
offerings have 2,283 and 2,365 enrollments. All 117 students appearing in both are
removed from development. Six snapshots contain:

| Day | Development N / withdrawals | Test N / withdrawals | Test prevalence |
|---|---|---|---|
| 14 | 1,890 / 302 | 1,862 / 353 | 18.96% |
| 28 | 1,874 / 286 | 1,834 / 325 | 17.72% |
| 42 | 1,846 / 258 | 1,810 / 301 | 16.63% |

The loader parses `?` as missing. It checks join-key uniqueness and matching
registration records. Five development and 26 test records fail outcome/date
consistency or registration-date validity checks, before cutoff eligibility.
These are retrospective complete-outcome exclusions, a possible selection bias.
Zero-activity students remain through enrollment-based joins. `data_audit.csv`,
`cohorts.csv`, `snapshot_diagnostics.csv` and the 48-row raw-record audit document
these checks. Public data are pseudonymized; there is no attempt at reidentification.

## Preprocessing and why it is appropriate

Background features are previous attempts, study load and highest education.
Engagement summarizes clicks, active dates, inactivity, a no-activity flag, recent
weekly clicks and their change. Submission features count non-exam submissions,
due assignments, overdue assignments and completion of due work. The exact
definitions are in `protocol.md` and the predictor allowlists in `data.py`.

At each cutoff, activity and submission records must have dates at or before it.
Pre-course activity is retained because it was observable. A deadline must be
strictly before the cutoff to count as overdue. A later submission cannot erase
an earlier overdue status. Marks are excluded because release times are unknown.
No activity becomes zero clicks/active days plus a separate indicator; inactivity
for these students uses a documented finite proxy, not a measured last-login date.
When nothing is due, submission rate is undefined, not evidence of poor completion.

Inside each training fold, numeric missing values receive training medians;
entirely missing numeric columns are retained with zero fill. Education receives
mode imputation and one-hot encoding, with unseen levels ignored. Logistic
regression uses standardized numeric inputs so regularization is comparable
across units. Trees do not require scaling. Validation/test data never determine
these learned transformations. IDs, outcomes, unregistration dates and warning
days are excluded from predictors even though they remain in audit datasets.

## Baselines and models

Random ranking measures no-information selection: expected recall is k/N and
expected precision is prevalence. One seeded realization is also reported.
Inactivity ranks never-active students first, then time since last activity;
ties use seeded, outcome-independent random ordering. This tests added value
beyond a cheap, understandable rule. A constant development-prevalence prediction
is the probability baseline for Brier score.

Regularized logistic regression estimates log-odds as a linear function of encoded
features; it is a restrained, interpretable starting point. Its L2 strength uses
C in {0.1, 1, 10}. Histogram gradient boosting models nonlinearities/interactions,
using 100 iterations, learning rate 0.05, leaves in {7, 15}, L2 in {1, 10}, and no
early stopping. We do not assume more complexity is better. Each cutoff and feature
group has its own fitted pipeline: 3 × 4 × 2 = 24 models, with 420 CV fits plus refits.

## Evaluation and statistical reasoning

We tune mean recall at the 10% budget using five stratified student-grouped folds
within 2013J, seed 678. Final models refit on all eligible development rows. Test
students are unseen, and all models are chosen before scoring 2014J. Exact IDs
and validation-fold assignments are exported to `results/splits/`.

Chronology assumes outcomes available 30 days after the earlier course finishes.
Using conservative month bounds, that date is 2014-08-25, before the earliest
day-14 test date of 2014-10-15. Actual release timestamps are unavailable; this is
an explicit assumption, not verified administrative history.

For N eligible students, k=floor(0.10N). Recall is TP / all withdrawals; precision
is TP / k. At a fixed budget and prevalence, precision = recall × prevalence / (k/N),
so these are complementary operational descriptions, not independent achievements.
Average precision summarizes ranking over thresholds. Brier is mean squared
probability error; it does not by itself demonstrate calibration. We do not assign
a Brier score to raw inactivity ranks. Warning time is withdrawal day minus cutoff,
summarized only among correctly flagged withdrawals; changing who is detected also
changes this conditional median. Overall accuracy is not the objective.

Paired percentile bootstrap intervals use 2,000 resamples of test students with
replacement, common indices for each model/baseline pair, and re-ranking within
each sample. They condition on fitted models and this offering, exclude retraining
and between-offering variability, and are not corrected for multiple comparisons.

## Main findings and interpretation

| Day | Inactivity recall | Logistic recall | Boosted recall | Logistic precision | Logistic median lead |
|---|---|---|---|---|---|
| 14 | 15.6% | 19.8% | 17.3% | 37.6% | 51.5 days |
| 28 | 18.5% | 22.5% | 20.3% | 39.9% | 46 days |
| 42 | 16.3% | 22.9% | 18.3% | 38.1% | 38 days |

Logistic-minus-inactivity recall differences are +4.2 percentage points (95% interval
+0.5 to +8.7), +4.0 (+0.9 to +8.8), and +6.6 (+2.3 to +11.6). Boosted differences
are smaller and their intervals include zero. This supports added predictive value
for logistic regression in this one transfer experiment, without establishing
general superiority across courses or a statistically tested logistic-versus-tree claim.

At day 28, logistic regression flags 183 students: 73 later withdraw, 110 do not;
252 withdrawals are missed. Inactivity identifies 60 withdrawals at the same budget.
Thus 13 additional withdrawals are identified, but most remain undetected.
At day 28, logistic AP is 0.330 versus inactivity 0.233; logistic Brier is 0.1364
versus the constant-probability baseline's 0.1464. See `results/EVIDENCE.md` for every
cutoff/model/AP/Brier value and uncertainty interval, not just these examples.

## Graduate depth: timing, ablation and budget

Later cutoffs provide more observations but remove students who already withdrew.
We therefore also compare the same 1,809 students (300 withdrawals) eligible at
all three cutoffs. One student in the day-42 cohort was not eligible at every earlier
cutoff. On this common cohort, logistic recall is 19.7%, 21.3%, 22.7%; inactivity
is 15.3%, 16.7%, 16.3%. The increasing logistic recall is therefore not explained
solely by changing cohort membership. This survivor-conditioned analysis is
retrospective and cannot define the operational day-14 population. It does not
isolate observation length perfectly: each cutoff uses separately trained models.

Logistic ablation recall at days 14/28/42 is: background 17.6/19.1/18.3%; engagement
17.6/16.6/16.3%; engagement plus submissions 17.8/20.6/20.6%; all groups
19.8/22.5/22.9%. Submission behavior helps especially after early deadlines, and
background adds further ranking information in this experiment. At day 14 there
are no overdue opportunities in the selected offering; submission counts can still
capture early submissions. Engagement-only models offer little benefit over the
rule at later cutoffs. Both families and all ablations are reported. These ablation
differences are descriptive; the main bootstrap intervals do not establish their
individual significance, nor do they prove causal effects of any feature.

The notebook adds an interactive 5–20% alert-budget control and day/cohort selection.
The 5%, 15% and 20% results are explicitly retrospective sensitivity analyses of
frozen scores, added after the first test evaluation. They are not used to choose
the primary budget, features or hyperparameters. The interaction reveals the
capacity–detection–false-alert trade-off and supports reasoning about a small change.

## Error analysis

At day 28, logistic false positives have median 94 clicks and six active days;
missed withdrawals have median 438 clicks and 17 active days. The false-positive
median overdue count is one; the missed-withdrawal median is zero. Low engagement
can precede eventual completion, while apparently active students can still withdraw.
Clicks cannot reveal every personal, financial or academic reason for withdrawal.
These are descriptive associations, not explanations of individual motives.

`results/error_examples.csv` supplies a reproducible representative false positive
and missed withdrawal for each full model and cutoff: the median-score case within
each error group, with stable tie ordering. It includes observed features and actual
outcomes. `error_analysis.csv` contains all four confusion-group counts and medians.
These test-set audits inform interpretation, not another tuning round.

## Limits and claim boundaries

This is one module and one later offering in historical distance education. Transfer
to another institution, time period or module is untested; the optional second-module
replication was not performed. Administrative withdrawal dates may lag actual
disengagement. Background/study-load values and assessment schedules are assumed
available at cutoff; timestamped revisions are unavailable. Banked assessments are
excluded as new submissions, but unobserved exemptions may inflate overdue counts.
The finite inactivity proxy also incorporates registration timing for never-active
students. Quality exclusions, no-activity logging gaps, arbitrary ties, seed choice
and season/year changes can affect results. Fairness across demographic groups and
intervention effectiveness are not established. No outreach deployment is claimed.

The proposal's analyses have been implemented; a positive result was never guaranteed.
The evidence favors a modest logistic improvement, with substantial false alerts and
missed withdrawals. Student understanding must still be demonstrated independently.
