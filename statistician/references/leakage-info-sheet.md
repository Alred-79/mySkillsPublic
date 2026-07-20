# Data leakage info sheet

Load on any modeling task (Phase 3). Leakage is when information that would not be available at prediction time leaks into training, producing an optimistic score that collapses in production. The Kapoor-Narayanan taxonomy documents this across >=294 papers in 17 fields; it is not a rare edge case, it is the default failure of naive ML pipelines.

## The one rule that prevents most of it

**Split first. Do every fitting-dependent step inside the training fold only, then apply the fitted transform to the test fold.** "Fitting-dependent" means the step learns parameters from the data:

| Step | Leaks if done before the split | Correct |
|---|---|---|
| Scaling / standardization | Test mean and variance leak into the scaler | Fit scaler on train, transform test |
| Imputation | Test values inform the imputed fill | Fit imputer on train, apply to test |
| Feature selection | Test target leaks through the selection | Select using train only, inside CV |
| Target / mean encoding | The target leaks directly | Encode within CV folds, out-of-fold |
| Resampling (SMOTE etc.) | Synthetic points built from test neighbors | Resample train only, after the split |

## The leakage types to check for

1. **No independent test set** - evaluating on data used in training. The split must exist and be honored.
2. **Preprocessing leakage** - the table above. The most common and most silent.
3. **Temporal leakage** - training on the future to predict the past. For any time-ordered data, split by time, not randomly. A random split lets tomorrow predict today.
4. **Duplicate / near-duplicate rows across the split** - the same entity in both folds inflates the score. De-duplicate by entity before splitting.
5. **Feature is a proxy for the target** - a column that is a downstream consequence of the label (e.g. "account_closed_date" predicting churn). Ask of every strong feature: would this value exist at prediction time?
6. **Group leakage** - rows from the same group (patient, user, store) split across folds. Use grouped splitting so a group is wholly in train or wholly in test.

## The tell

A model that scores far above a sane baseline, or near-perfect on noisy data, is leaking until proven otherwise. Suspiciously good is a symptom, not a success. Re-check the split and the preprocessing order before believing it.
