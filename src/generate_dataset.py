"""AI Payment Risk Manager - Synthetic Dataset Generator

Generates realistic, synthetic payment transaction records with a latent
probabilistic risk model to avoid deterministic rules and target leakage.
Tailored for Indian fintech payment risk scenarios (INR / ₹).
"""
import os
import numpy as np
import pandas as pd


def generate_payment_dataset(
    n_samples: int = 100_000,
    random_seed: int = 42,
    output_filepath: str = "data/transactions.csv",
) -> pd.DataFrame:
    """
    Generate synthetic payment transactions with non-linear fraud probability,
    validate integrity constraints, and save to CSV.
    """
    np.random.seed(random_seed)

    # 1. Unique Transaction IDs
    transaction_ids = [f"TXN_{i:08d}" for i in range(1, n_samples + 1)]

    # 2. Account Age in Days (Mixture: newer accounts and seasoned accounts)
    # Most accounts are mature (median ~300 days), with a realistic tail up to ~5 years (1825 days)
    account_age_days = np.random.exponential(scale=350, size=n_samples) + 1
    account_age_days = np.clip(np.round(account_age_days), 1, 1825).astype(int)

    # 3. Previous Average Transaction Amount in INR (₹)
    # Typical customer historical spend: median ~₹1,200 - ₹3,500, with long tail for affluent users
    prev_log_mean = np.random.normal(loc=7.2, scale=0.7, size=n_samples)
    previous_avg_amount = np.exp(prev_log_mean)
    previous_avg_amount = np.clip(np.round(previous_avg_amount, 2), 50.0, 250000.0)

    # 4. Current Transaction Amount in INR (₹)
    # Positively skewed distribution anchored around user's historical spend profile
    amount_multiplier = np.random.lognormal(mean=0.0, sigma=0.6, size=n_samples)
    # Occasional high-value purchases (e.g. appliances, travel tickets, festival shopping)
    spontaneous_spike = np.random.choice([1.0, 2.5, 5.0, 10.0], size=n_samples, p=[0.93, 0.045, 0.018, 0.007])
    raw_amount = previous_avg_amount * amount_multiplier * spontaneous_spike
    transaction_amount = np.clip(np.round(raw_amount, 2), 10.0, 500000.0)

    # 5. Transaction Hour (Circadian pattern in IST: lull during 01:00 - 05:00 IST, peak afternoon & evening)
    hour_probs = np.array([
        0.015, 0.010, 0.008, 0.006, 0.006, 0.010,  # 00:00 - 05:00 (night lull)
        0.020, 0.035, 0.050, 0.065, 0.070, 0.070,  # 06:00 - 11:00 (morning ramp)
        0.075, 0.075, 0.070, 0.065, 0.065, 0.070,  # 12:00 - 17:00 (afternoon peak)
        0.075, 0.070, 0.060, 0.045, 0.035, 0.020   # 18:00 - 23:00 (evening taper)
    ])
    hour_probs = hour_probs / hour_probs.sum()
    transaction_hour = np.random.choice(np.arange(24), size=n_samples, p=hour_probs)

    # 6. Device Status (New Device: ~14% baseline, elevated for fresh accounts)
    new_device_prob = np.where(account_age_days < 30, 0.35, 0.12)
    new_device = (np.random.rand(n_samples) < new_device_prob).astype(int)

    # 7. Location Mismatch (e.g. travel across cities/states, VPN usage: ~8.5% baseline)
    location_mismatch = (np.random.rand(n_samples) < 0.085).astype(int)

    # 8. International Cross-border Transaction (~5.5% baseline)
    international_transaction = (np.random.rand(n_samples) < 0.055).astype(int)

    # 9. Failed Attempts before authorization (mostly 0; occasional OTP/PIN retries 1-3)
    failed_attempts_probs = [0.87, 0.085, 0.030, 0.010, 0.005]
    failed_attempts = np.random.choice(np.arange(5), size=n_samples, p=failed_attempts_probs)

    # 10. Velocity: Transactions in last 24h & last 10min
    transactions_last_24h = np.random.poisson(lam=2.6, size=n_samples)
    transactions_last_24h = np.clip(transactions_last_24h, 0, 35).astype(int)

    prob_10min_active = np.clip(transactions_last_24h * 0.07, 0.02, 0.40)
    has_10min_txns = np.random.rand(n_samples) < prob_10min_active
    transactions_last_10min = np.where(
        has_10min_txns,
        np.random.geometric(p=0.65, size=n_samples) - 1,
        0
    )
    # Ensure 10-minute velocity does not exceed 24-hour total velocity
    transactions_last_10min = np.minimum(transactions_last_10min, transactions_last_24h)
    transactions_last_10min = np.clip(transactions_last_10min, 0, 15).astype(int)

    # =========================================================================
    # LATENT FRAUD-RISK MECHANISM (Calibrated log-odds model + interactions + noise)
    # =========================================================================
    # Ratio of current transaction to historical baseline
    amount_deviation_ratio = transaction_amount / (previous_avg_amount + 1e-5)
    log_amount_ratio = np.log1p(amount_deviation_ratio)

    # Absolute transaction amount scale (standardized relative to median Indian ticket sizes)
    log_abs_amount = np.log1p(transaction_amount / 1000.0)

    # High-risk night hours (01:00 - 05:00 IST)
    late_night_flag = np.isin(transaction_hour, [1, 2, 3, 4, 5]).astype(float)

    # Freshly opened accounts (<= 14 days)
    new_account_flag = (account_age_days <= 14).astype(float)

    # Base log-odds (calibrated baseline intercept for ~1.8% to 2.2% realistic fraud prevalence)
    base_log_odds = -6.40

    # Additive component weights
    log_odds = (
        base_log_odds
        + 0.55 * log_amount_ratio
        + 0.30 * log_abs_amount
        + 0.75 * new_device
        + 0.80 * location_mismatch
        + 0.75 * international_transaction
        + 0.50 * failed_attempts
        + 0.35 * np.log1p(transactions_last_10min)
        + 0.20 * np.log1p(transactions_last_24h)
        + 0.50 * new_account_flag
        + 0.40 * late_night_flag
        # Interaction terms (synergistic compounding risk)
        + 0.95 * (new_device * location_mismatch)
        + 0.70 * (new_device * (failed_attempts >= 2))
        + 0.75 * (international_transaction * location_mismatch)
        + 0.65 * (new_account_flag * (amount_deviation_ratio > 3.0))
        + 0.60 * (late_night_flag * (transactions_last_10min >= 2))
        # Stochastic Gaussian noise for non-perfect separability
        + np.random.normal(loc=0.0, scale=0.75, size=n_samples)
    )

    # Sigmoid function to map log-odds to continuous probability [0, 1]
    fraud_probability = 1.0 / (1.0 + np.exp(-log_odds))

    # Binary fraud realization via Bernoulli trial
    is_fraud = (np.random.rand(n_samples) < fraud_probability).astype(int)

    # Construct final DataFrame with strictly specified columns
    df = pd.DataFrame({
        "transaction_id": transaction_ids,
        "transaction_amount": transaction_amount,
        "transaction_hour": transaction_hour,
        "account_age_days": account_age_days,
        "new_device": new_device,
        "location_mismatch": location_mismatch,
        "failed_attempts": failed_attempts,
        "transactions_last_10min": transactions_last_10min,
        "transactions_last_24h": transactions_last_24h,
        "previous_avg_amount": previous_avg_amount,
        "international_transaction": international_transaction,
        "is_fraud": is_fraud,
    })

    # =========================================================================
    # DATASET INTEGRITY & VALIDATION CHECKS
    # =========================================================================
    total_rows, total_cols = df.shape
    fraud_count = int(df["is_fraud"].sum())
    legit_count = total_rows - fraud_count
    fraud_pct = (fraud_count / total_rows) * 100.0
    missing_count = int(df.isnull().sum().sum())

    # 1. Assert row count matches requested sample size
    assert total_rows == n_samples, f"Expected {n_samples} rows, got {total_rows}"

    # 2. Assert fraud percentage is strictly within [1.0%, 3.0%]
    assert 1.0 <= fraud_pct <= 3.0, (
        f"Validation Error: Fraud percentage {fraud_pct:.2f}% is outside the target [1.0%, 3.0%] range."
    )

    # 3. Assert transaction_id is unique
    assert df["transaction_id"].is_unique, "Validation Error: transaction_id column contains duplicates."

    # 4. Assert there are no missing values
    assert missing_count == 0, f"Validation Error: Found {missing_count} missing values in dataset."

    # 5. Assert numeric features do not contain impossible negative values
    numeric_columns = [
        "transaction_amount",
        "transaction_hour",
        "account_age_days",
        "new_device",
        "location_mismatch",
        "failed_attempts",
        "transactions_last_10min",
        "transactions_last_24h",
        "previous_avg_amount",
        "international_transaction",
        "is_fraud",
    ]
    for col in numeric_columns:
        min_val = df[col].min()
        assert min_val >= 0, f"Validation Error: Column '{col}' contains negative values (min: {min_val})."

    # Save to CSV
    output_dir = os.path.dirname(output_filepath)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    df.to_csv(output_filepath, index=False)

    # Print summary statistics
    print("=" * 58)
    print("AI Payment Risk Manager - Dataset Generation Summary (₹ INR)")
    print("=" * 58)
    print(f"File Saved To:       {output_filepath}")
    print(f"Number of Rows:      {total_rows:,}")
    print(f"Number of Columns:   {total_cols}")
    print(f"Legitimate Count:    {legit_count:,}")
    print(f"Fraud Count:         {fraud_count:,}")
    print(f"Fraud Percentage:    {fraud_pct:.2f}%")
    print(f"Missing-Value Count: {missing_count}")
    print(f"Validation Checks:   ALL PASSED [1.0% <= {fraud_pct:.2f}% <= 3.0%]")
    print("=" * 58)

    return df


if __name__ == "__main__":
    generate_payment_dataset()
