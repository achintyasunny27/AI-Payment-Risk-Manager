import requests 
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

import streamlit as st
import pandas as pd
import joblib

from src.razorpay_service import create_test_order


# -----------------------------
# Load trained model
# -----------------------------



model_path = os.path.join(
    BASE_DIR,
    "models",
    "payment_risk_model.pkl"
)

model_package = joblib.load(model_path)

model = model_package["model"]
model = model_package["model"]
scaler = model_package["scaler"]
features = model_package["features"]
threshold = model_package.get("threshold", 0.5)

print("MODEL TYPE:", type(model))
print("MODEL PATH:", model_path)
print("FEATURE COUNT:", len(features))
features = model_package["features"]
threshold = model_package.get("threshold", 0.5)

# -----------------------------
# Page configuration
# -----------------------------

st.set_page_config(
    page_title="AI Payment Risk Manager",
    page_icon="💳",
    layout="wide"
)


# -----------------------------
# Title
# -----------------------------

st.title("💳 AI Payment Risk Manager")
st.write("AI-powered payment transaction risk analysis")


# -----------------------------
# Transaction input
# -----------------------------

st.header("Transaction Details")

col1, col2 = st.columns(2)

with col1:
    transaction_amount = st.number_input(
        "Transaction Amount (₹)",
        min_value=10.0,
        value=1200.0
    )

    transaction_hour = st.slider(
        "Transaction Hour",
        min_value=0,
        max_value=23,
        value=14
    )

    account_age_days = st.number_input(
        "Account Age (days)",
        min_value=1,
        value=450
    )

    previous_avg_amount = st.number_input(
        "Previous Average Transaction (₹)",
        min_value=50.0,
        value=1300.0
    )

    failed_attempts = st.number_input(
        "Failed Attempts",
        min_value=0,
        max_value=10,
        value=0
    )


with col2:
    new_device = st.selectbox(
        "New Device?",
        ["No", "Yes"]
    )

    location_mismatch = st.selectbox(
        "Location Mismatch?",
        ["No", "Yes"]
    )

    international_transaction = st.selectbox(
        "International Transaction?",
        ["No", "Yes"]
    )

    transactions_last_10min = st.number_input(
        "Transactions in Last 10 Minutes",
        min_value=0,
        max_value=15,
        value=0
    )

    transactions_last_24h = st.number_input(
        "Transactions in Last 24 Hours",
        min_value=0,
        max_value=35,
        value=2
    )


# -----------------------------
# Analyze transaction
# -----------------------------

if st.button("💳 Create Razorpay Test Order"):

    transaction = {
        "transaction_amount": transaction_amount,
        "transaction_hour": transaction_hour,
        "account_age_days": account_age_days,
        "new_device": 1 if new_device == "Yes" else 0,
        "location_mismatch": 1 if location_mismatch == "Yes" else 0,
        "failed_attempts": failed_attempts,
        "transactions_last_10min": transactions_last_10min,
        "transactions_last_24h": transactions_last_24h,
        "previous_avg_amount": previous_avg_amount,
        "international_transaction": (
            1 if international_transaction == "Yes" else 0
        )
    }
    try:
        response = requests.post(
            "https://ai-payment-risk-manager-2ggl.onrender.com/create-order",
            json=transaction,
            timeout=60
        )

        st.write("Backend status:", response.status_code)
        st.write("Backend response:", response.text)

        if response.status_code == 200:
            order = response.json()

            st.success("Razorpay Test Order Created!")

            st.write(
                "Order ID:",
                order["id"]
            )

            st.info(
                "Order created successfully. "
                "Now we need to open Razorpay Checkout."
            )

        else:
            st.error(
                f"Could not create Razorpay order. "
                f"Status: {response.status_code}"
            )

    except Exception as e:
        st.error(f"Backend connection failed: {e}")
    
    
   

# --------------------------------
# Check verified payment
# --------------------------------

if st.button("🔍 Check Payment & Analyze"):

    response = requests.get(
         "https://ai-payment-risk-manager-2ggl.onrender.com/payment-status"
    )

    if response.status_code != 200:

        st.error("Could not contact payment server.")
        st.stop()

    payment_data = response.json()

    payment = payment_data.get("payment", {})
    transaction = payment_data.get("transaction", {})

    if not payment:

        st.warning(
            "Payment is not verified yet. "
            "Complete the Razorpay Test payment first."
        )

        st.stop()

    # --------------------------------
    # Payment verified
    # --------------------------------

    st.success("✅ Razorpay Payment Verified!")

    st.write(
        "Payment ID:",
        payment["payment_id"]
    )

    st.write(
        "Order ID:",
        payment["order_id"]
    )
    # --------------------------------
    # ML Risk Analysis
    # --------------------------------

    transaction_df = pd.DataFrame([payment_data.get("transaction", {})])

    X = transaction_df[features]

    st.write("DEBUG FEATURES SENT TO MODEL")
    st.write(X)

    # Apply the SAME scaling used during training
    X_scaled = scaler.transform(X)

    # Predict fraud probability
    probability = model.predict_proba(X_scaled)[0, 1]

    # Convert probability to 0-100 risk score
    risk_score = round(
        probability * 100,
        2
    )

    # Risk category
    if probability >= threshold:
        risk_level = "HIGH"
    elif probability >= 0.30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
            
        # -----------------------------
        # Save analysis to database
        # -----------------------------

    save_response = requests.post(
            "https://ai-payment-risk-manager-2ggl.onrender.com",
            json={
                "payment_id": payment["payment_id"],
                "order_id": payment["order_id"],
                "transaction": transaction,
                "fraud_probability": float(probability),
                 "risk_score": float(risk_score),
                "risk_level": risk_level
            }
        )

    if save_response.status_code == 200:
            st.success("✅ Transaction saved to database!")
    else:
            st.warning(
                "Risk analysis completed, "
                "but transaction could not be saved."
            )
    
    # --------------------------------
    # Risk Analysis
    # --------------------------------

    st.divider()

    st.header("Risk Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Risk Score",
            f"{risk_score:.2f}/100"
        )

    with col2:
        st.metric(
            "Model Score",
            f"{probability:.2%}"
        )

    with col3:
        st.metric(
            "Risk Level",
            risk_level
        )

    # --------------------------------
    # Risk Factors
    # --------------------------------

    st.subheader("⚠️ Risk Factors")

    risk_factors = []

    amount_ratio = (
        transaction["transaction_amount"]
        / transaction["previous_avg_amount"]
    )

    if amount_ratio >= 2:

        risk_factors.append(
            f"Transaction amount is "
            f"{amount_ratio:.1f}× the previous average"
        )

    if transaction["new_device"] == 1:
        risk_factors.append("New device detected")

    if transaction["location_mismatch"] == 1:
        risk_factors.append("Location mismatch detected")

    if transaction["failed_attempts"] >= 2:

        risk_factors.append(
            f"{transaction['failed_attempts']} failed attempts"
        )

    if transaction["transactions_last_10min"] >= 2:

        risk_factors.append(
            f"{transaction['transactions_last_10min']} "
            "transactions in the last 10 minutes"
        )

    if transaction["international_transaction"] == 1:
        risk_factors.append("International transaction")

    if transaction["transaction_hour"] in [1, 2, 3, 4, 5]:
        risk_factors.append(
            "Transaction occurred during late-night hours"
        )

    if transaction["account_age_days"] <= 14:
        risk_factors.append("Very new account")

    if risk_factors:

        for factor in risk_factors:
            st.warning(factor)

    else:

        st.success(
            "No major risk factors detected."
        )
        # -----------------------------
# Transaction History
# -----------------------------

st.divider()

st.header("📊 Transaction History")

history_response = requests.get(
    "https://ai-payment-risk-manager-2ggl.onrender.com/transactions"
)

if history_response.status_code == 200:

    history_data = history_response.json()

    transactions = history_data.get(
        "transactions",
        []
    )

    if transactions:
              # -----------------------------
        # Risk Overview
        # -----------------------------

        history_df = pd.DataFrame(transactions)

        total_transactions = len(history_df)

        high_risk = len(
            history_df[history_df.iloc[:, -1] == "HIGH"]
        )

        medium_risk = len(
            history_df[history_df.iloc[:, -1] == "MEDIUM"]
        )

        low_risk = len(
            history_df[history_df.iloc[:, -1] == "LOW"]
        )

        average_risk = history_df.iloc[:, -2].mean()

        st.subheader("📊 Risk Overview")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "Total Transactions",
                total_transactions
            )

        with col2:
            st.metric(
                "🔴 High Risk",
                high_risk
            )

        with col3:
            st.metric(
                "🟡 Medium Risk",
                medium_risk
            )

        with col4:
            st.metric(
                "🟢 Low Risk",
                low_risk
            )

        with col5:
            st.metric(
                "Average Risk",
                f"{average_risk:.2f}"
            )  
        columns = [
            "ID",
            "Payment ID",
            "Order ID",
            "Amount",
            "Hour",
            "Account Age",
            "New Device",
            "Location Mismatch",
            "Failed Attempts",
            "Transactions 10min",
            "Transactions 24h",
            "Previous Avg",
            "International",
            "Risk Score",
            "Risk Level"
        ]

        history_df = pd.DataFrame(
            transactions,
            columns=columns
        )

        display_df = history_df[
            [
                "Payment ID",
                "Order ID",
                "Amount",
                "Risk Score",
                "Risk Level"
            ]
        ]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No transactions found.")

else:

    st.error("Could not load transaction history.")