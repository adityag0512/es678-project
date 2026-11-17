# Detailed evidence

Generated from saved predictions; no model changes.

## Main results

| cutoff | model | n | positives | alerts | true_positives | recall_at_10pct | precision_at_10pct | average_precision | brier | median_warning_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14 | inactivity | 1862 | 353 | 186 | 55 | 0.156 | 0.296 | 0.237 | — | 67.000 |
| 14 | random | 1862 | 353 | 186 | 39 | 0.110 | 0.210 | 0.208 | — | 79.000 |
| 14 | prevalence | 1862 | 353 | 186 | 34 | 0.096 | 0.183 | 0.190 | 0.155 | 77.000 |
| 14 | all_logistic | 1862 | 353 | 186 | 70 | 0.198 | 0.376 | 0.313 | 0.147 | 51.500 |
| 14 | all_boosted | 1862 | 353 | 186 | 61 | 0.173 | 0.328 | 0.298 | 0.148 | 51.000 |
| 28 | inactivity | 1834 | 325 | 183 | 60 | 0.185 | 0.328 | 0.233 | — | 38.500 |
| 28 | random | 1834 | 325 | 183 | 31 | 0.095 | 0.169 | 0.170 | — | 53.000 |
| 28 | prevalence | 1834 | 325 | 183 | 36 | 0.111 | 0.197 | 0.177 | 0.146 | 72.000 |
| 28 | all_logistic | 1834 | 325 | 183 | 73 | 0.225 | 0.399 | 0.330 | 0.136 | 46.000 |
| 28 | all_boosted | 1834 | 325 | 183 | 66 | 0.203 | 0.361 | 0.304 | 0.139 | 42.500 |
| 42 | inactivity | 1810 | 301 | 181 | 49 | 0.163 | 0.271 | 0.241 | — | 44.000 |
| 42 | random | 1810 | 301 | 181 | 28 | 0.093 | 0.155 | 0.166 | — | 49.500 |
| 42 | prevalence | 1810 | 301 | 181 | 22 | 0.073 | 0.122 | 0.166 | 0.139 | 73.000 |
| 42 | all_logistic | 1810 | 301 | 181 | 69 | 0.229 | 0.381 | 0.331 | 0.131 | 38.000 |
| 42 | all_boosted | 1810 | 301 | 181 | 55 | 0.183 | 0.304 | 0.283 | 0.132 | 30.000 |

## Common cohort: 1,809 students and 300 withdrawals

| cutoff | model | recall_at_10pct | median_warning_days |
| --- | --- | --- | --- |
| 14 | inactivity | 0.153 | 92.000 |
| 14 | all_logistic | 0.197 | 67.000 |
| 14 | all_boosted | 0.160 | 73.500 |
| 28 | inactivity | 0.167 | 45.000 |
| 28 | all_logistic | 0.213 | 58.500 |
| 28 | all_boosted | 0.187 | 47.500 |
| 42 | inactivity | 0.163 | 45.000 |
| 42 | all_logistic | 0.227 | 37.500 |
| 42 | all_boosted | 0.183 | 30.000 |

## Ablation: both model families

| cutoff | model | recall_at_10pct | average_precision | brier |
| --- | --- | --- | --- | --- |
| 14 | background_logistic | 0.176 | 0.260 | 0.151 |
| 14 | background_boosted | 0.170 | 0.248 | 0.153 |
| 14 | engagement_logistic | 0.176 | 0.261 | 0.151 |
| 14 | engagement_boosted | 0.127 | 0.242 | 0.152 |
| 14 | engagement_submission_logistic | 0.178 | 0.265 | 0.151 |
| 14 | engagement_submission_boosted | 0.133 | 0.239 | 0.153 |
| 14 | all_logistic | 0.198 | 0.313 | 0.147 |
| 14 | all_boosted | 0.173 | 0.298 | 0.148 |
| 28 | background_logistic | 0.191 | 0.245 | 0.144 |
| 28 | background_boosted | 0.182 | 0.230 | 0.145 |
| 28 | engagement_logistic | 0.166 | 0.262 | 0.143 |
| 28 | engagement_boosted | 0.166 | 0.250 | 0.143 |
| 28 | engagement_submission_logistic | 0.206 | 0.295 | 0.139 |
| 28 | engagement_submission_boosted | 0.191 | 0.279 | 0.141 |
| 28 | all_logistic | 0.225 | 0.330 | 0.136 |
| 28 | all_boosted | 0.203 | 0.304 | 0.139 |
| 42 | background_logistic | 0.183 | 0.225 | 0.137 |
| 42 | background_boosted | 0.173 | 0.205 | 0.139 |
| 42 | engagement_logistic | 0.163 | 0.234 | 0.135 |
| 42 | engagement_boosted | 0.153 | 0.228 | 0.138 |
| 42 | engagement_submission_logistic | 0.206 | 0.281 | 0.133 |
| 42 | engagement_submission_boosted | 0.193 | 0.242 | 0.136 |
| 42 | all_logistic | 0.229 | 0.331 | 0.131 |
| 42 | all_boosted | 0.183 | 0.283 | 0.132 |

## Paired uncertainty

| cutoff | population | model | baseline | metric | difference | ci_low | ci_high | valid_replicates |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14 | dynamic | all_logistic | inactivity | recall_at_10pct | 0.042 | 0.005 | 0.087 | 2000 |
| 14 | dynamic | all_logistic | inactivity | precision_at_10pct | 0.081 | 0.011 | 0.167 | 2000 |
| 14 | dynamic | all_logistic | inactivity | average_precision | 0.077 | 0.043 | 0.116 | 2000 |
| 14 | common | all_logistic | inactivity | recall_at_10pct | 0.043 | -0.007 | 0.088 | 2000 |
| 14 | common | all_logistic | inactivity | precision_at_10pct | 0.072 | -0.011 | 0.144 | 2000 |
| 14 | common | all_logistic | inactivity | average_precision | 0.055 | 0.024 | 0.092 | 2000 |
| 14 | dynamic | all_boosted | inactivity | recall_at_10pct | 0.017 | -0.024 | 0.051 | 2000 |
| 14 | dynamic | all_boosted | inactivity | precision_at_10pct | 0.032 | -0.048 | 0.097 | 2000 |
| 14 | dynamic | all_boosted | inactivity | average_precision | 0.061 | 0.031 | 0.099 | 2000 |
| 14 | common | all_boosted | inactivity | recall_at_10pct | 0.007 | -0.037 | 0.049 | 2000 |
| 14 | common | all_boosted | inactivity | precision_at_10pct | 0.011 | -0.061 | 0.083 | 2000 |
| 14 | common | all_boosted | inactivity | average_precision | 0.046 | 0.016 | 0.086 | 2000 |
| 28 | dynamic | all_logistic | inactivity | recall_at_10pct | 0.040 | 0.009 | 0.088 | 2000 |
| 28 | dynamic | all_logistic | inactivity | precision_at_10pct | 0.071 | 0.016 | 0.158 | 2000 |
| 28 | dynamic | all_logistic | inactivity | average_precision | 0.097 | 0.063 | 0.140 | 2000 |
| 28 | common | all_logistic | inactivity | recall_at_10pct | 0.047 | 0.006 | 0.088 | 2000 |
| 28 | common | all_logistic | inactivity | precision_at_10pct | 0.078 | 0.011 | 0.144 | 2000 |
| 28 | common | all_logistic | inactivity | average_precision | 0.087 | 0.053 | 0.125 | 2000 |
| 28 | dynamic | all_boosted | inactivity | recall_at_10pct | 0.018 | -0.022 | 0.064 | 2000 |
| 28 | dynamic | all_boosted | inactivity | precision_at_10pct | 0.033 | -0.038 | 0.115 | 2000 |
| 28 | dynamic | all_boosted | inactivity | average_precision | 0.071 | 0.036 | 0.114 | 2000 |
| 28 | common | all_boosted | inactivity | recall_at_10pct | 0.020 | -0.024 | 0.063 | 2000 |
| 28 | common | all_boosted | inactivity | precision_at_10pct | 0.033 | -0.039 | 0.106 | 2000 |
| 28 | common | all_boosted | inactivity | average_precision | 0.069 | 0.033 | 0.111 | 2000 |
| 42 | dynamic | all_logistic | inactivity | recall_at_10pct | 0.066 | 0.023 | 0.116 | 2000 |
| 42 | dynamic | all_logistic | inactivity | precision_at_10pct | 0.110 | 0.039 | 0.193 | 2000 |
| 42 | dynamic | all_logistic | inactivity | average_precision | 0.089 | 0.045 | 0.138 | 2000 |
| 42 | common | all_logistic | inactivity | recall_at_10pct | 0.063 | 0.022 | 0.116 | 2000 |
| 42 | common | all_logistic | inactivity | precision_at_10pct | 0.106 | 0.039 | 0.194 | 2000 |
| 42 | common | all_logistic | inactivity | average_precision | 0.089 | 0.045 | 0.137 | 2000 |
| 42 | dynamic | all_boosted | inactivity | recall_at_10pct | 0.020 | -0.025 | 0.073 | 2000 |
| 42 | dynamic | all_boosted | inactivity | precision_at_10pct | 0.033 | -0.044 | 0.122 | 2000 |
| 42 | dynamic | all_boosted | inactivity | average_precision | 0.042 | 0.003 | 0.089 | 2000 |
| 42 | common | all_boosted | inactivity | recall_at_10pct | 0.020 | -0.024 | 0.074 | 2000 |
| 42 | common | all_boosted | inactivity | precision_at_10pct | 0.033 | -0.039 | 0.122 | 2000 |
| 42 | common | all_boosted | inactivity | average_precision | 0.045 | 0.006 | 0.089 | 2000 |

## Snapshot diagnostics

| cutoff | split | n | no_activity | missing_submission_rate | assignments_due |
| --- | --- | --- | --- | --- | --- |
| 14 | development | 1890 | 41 | 1890 | 0 |
| 14 | test | 1862 | 41 | 1862 | 0 |
| 28 | development | 1874 | 21 | 0 | 1 |
| 28 | test | 1834 | 21 | 0 | 1 |
| 42 | development | 1846 | 12 | 0 | 1 |
| 42 | test | 1810 | 14 | 0 | 1 |

## Representative errors: median score within each error group

| cutoff | model | error_type | id_student | predicted_probability | final_result | total_clicks | active_days | overdue | warning_days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 14 | all_logistic | false_positive | 1866233 | 0.288 | Fail | 0 | 0 | 0 | — |
| 14 | all_logistic | missed_withdrawal | 698762 | 0.158 | Withdrawn | 374 | 12 | 0 | 60.000 |
| 14 | all_boosted | false_positive | 372511 | 0.309 | Pass | 1 | 1 | 0 | — |
| 14 | all_boosted | missed_withdrawal | 676040 | 0.151 | Withdrawn | 341 | 12 | 0 | 48.000 |
| 28 | all_logistic | false_positive | 679790 | 0.315 | Pass | 95 | 8 | 1 | — |
| 28 | all_logistic | missed_withdrawal | 695250 | 0.142 | Withdrawn | 716 | 26 | 0 | 72.000 |
| 28 | all_boosted | false_positive | 652647 | 0.311 | Fail | 388 | 24 | 1 | — |
| 28 | all_boosted | missed_withdrawal | 631193 | 0.142 | Withdrawn | 324 | 15 | 0 | 13.000 |
| 42 | all_logistic | false_positive | 650048 | 0.254 | Fail | 62 | 4 | 0 | — |
| 42 | all_logistic | missed_withdrawal | 340831 | 0.141 | Withdrawn | 311 | 32 | 0 | 27.000 |
| 42 | all_boosted | false_positive | 650031 | 0.273 | Fail | 691 | 26 | 0 | — |
| 42 | all_boosted | missed_withdrawal | 690962 | 0.150 | Withdrawn | 313 | 29 | 0 | 74.000 |
