import os
import sys
import requests
import streamlit as st
import pandas as pd
import joblib


# =========================================================
# PROJECT PATH
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="AI Payment Risk Manager",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# BACKEND URL
# =========================================================

try:
    BACKEND_URL = st.secrets.get("BACKEND_URL", "")
except Exception:
    BACKEND_URL = ""

if not BACKEND_URL:
    BACKEND_URL = os.getenv(
        "BACKEND_URL",
        "http://127.0.0.1:5000"
    )

BACKEND_URL = BACKEND_URL.rstrip("/")


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .subtitle {
        font-size: 16px;
        color: #9ca3af;
        margin-bottom: 32px;
    }

    .section-title {
        font-size: 30px;
        font-weight: 750;
        margin-top: 10px;
        margin-bottom: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# LOAD ML MODEL
# =========================================================

@st.cache_resource
def load_model():

    model_path = os.path.join(
        BASE_DIR,
        "models",
        "payment_risk_model.pkl"
    )

    package = joblib.load(model_path)

    model = package["model"]
    scaler = package["scaler"]
    features = package["features"]

    threshold = package.get(
        "threshold",
        0.5
    )

    return model, scaler, features, threshold


try:

    model, scaler, features, threshold = load_model()

except Exception as error:

    st.error(
        f"❌ Could not load ML model: {error}"
    )

    st.info(
        "Make sure models/payment_risk_model.pkl exists."
    )

    st.stop()


# =========================================================
# SESSION STATE
# =========================================================

if "payment_created" not in st.session_state:
    st.session_state.payment_created = False

if "payment_info" not in st.session_state:
    st.session_state.payment_info = {}

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None


# =========================================================
# BACKEND FUNCTIONS
# =========================================================

def backend_get(endpoint, timeout=30):

    return requests.get(
        f"{BACKEND_URL}{endpoint}",
        timeout=timeout
    )


def backend_post(endpoint, payload, timeout=30):

    return requests.post(
        f"{BACKEND_URL}{endpoint}",
        json=payload,
        timeout=timeout
    )


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🛡️ AI Payment Risk Manager</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'AI-powered transaction monitoring, fraud-risk analysis '
    'and payment verification dashboard'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ Transaction Details")

    transaction_amount = st.number_input(
        "Transaction Amount (₹)",
        min_value=10.0,
        max_value=1000000.0,
        value=1200.0,
        step=100.0
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
        max_value=5000,
        value=450
    )

    new_device = st.selectbox(
        "New Device?",
        ["No", "Yes"]
    )

    location_mismatch = st.selectbox(
        "Location Mismatch?",
        ["No", "Yes"]
    )

    failed_attempts = st.number_input(
        "Failed Attempts",
        min_value=0,
        max_value=20,
        value=0
    )

    transactions_last_10min = st.number_input(
        "Transactions in Last 10 Minutes",
        min_value=0,
        max_value=50,
        value=0
    )

    transactions_last_24h = st.number_input(
        "Transactions in Last 24 Hours",
        min_value=0,
        max_value=100,
        value=2
    )

    previous_avg_amount = st.number_input(
        "Previous Average Transaction (₹)",
        min_value=1.0,
        max_value=1000000.0,
        value=1300.0,
        step=50.0
    )

    international_transaction = st.selectbox(
        "International Transaction?",
        ["No", "Yes"]
    )


# =========================================================
# PAYMENT
# =========================================================

st.markdown(
    '<div class="section-title">💳 Payment</div>',
    unsafe_allow_html=True
)

payment_col1, payment_col2 = st.columns(2)


# =========================================================
# CREATE TEST PAYMENT
# =========================================================

with payment_col1:

    if st.button(
        "💳 Create Test Payment",
        use_container_width=True,
        key="create_payment_button"
    ):

        transaction = {

            "transaction_amount": float(
                transaction_amount
            ),

            "transaction_hour": int(
                transaction_hour
            ),

            "account_age_days": int(
                account_age_days
            ),

            "new_device": 1 if new_device == "Yes" else 0,

            "location_mismatch":
                1 if location_mismatch == "Yes" else 0,

            "failed_attempts": int(
                failed_attempts
            ),

            "transactions_last_10min": int(
                transactions_last_10min
            ),

            "transactions_last_24h": int(
                transactions_last_24h
            ),

            "previous_avg_amount": float(
                previous_avg_amount
            ),

            "international_transaction":
                1 if international_transaction == "Yes" else 0
        }

        try:

            response = backend_post(
                "/create-order",
                transaction,
                timeout=30
            )

            if response.status_code == 200:

                order = response.json()

                st.session_state.payment_created = True

                st.session_state.payment_info = order

                st.session_state.analysis_result = None

                st.success(
                    "✅ Test Payment Created Successfully!"
                )

                info1, info2, info3 = st.columns(3)

                with info1:

                    st.metric(
                        "Amount",
                        f"₹{transaction_amount:.0f}"
                    )

                with info2:

                    st.write("**Payment ID**")

                    st.code(
                        order.get(
                            "payment_id",
                            "N/A"
                        )
                    )

                with info3:

                    st.write("**Order ID**")

                    st.code(
                        order.get(
                            "id",
                            "N/A"
                        )
                    )

                st.info(
                    "Test payment is automatically verified. "
                    "Click **Check Payment & Analyze**."
                )

            else:

                st.error(
                    f"Could not create payment. "
                    f"Status: {response.status_code}"
                )

                try:

                    st.code(
                        response.json()
                    )

                except Exception:

                    st.code(
                        response.text
                    )

        except requests.exceptions.ConnectionError:

            st.error(
                "❌ Payment backend is not running."
            )

            st.code(
                "python -m src.payment_server"
            )

        except requests.exceptions.Timeout:

            st.error(
                "❌ Payment backend request timed out."
            )

        except Exception as error:

            st.error(
                f"Payment creation failed: {error}"
            )


# =========================================================
# CHECK PAYMENT & ANALYZE
# =========================================================

with payment_col2:

    if st.button(
        "🔍 Check Payment & Analyze",
        use_container_width=True,
        key="analyze_payment_button"
    ):

        try:

            response = backend_get(
                "/payment-status",
                timeout=30
            )

            if response.status_code != 200:

                st.error(
                    "Could not contact payment backend."
                )

            else:

                payment_data = response.json()

                payment = payment_data.get(
                    "payment",
                    {}
                )

                transaction = payment_data.get(
                    "transaction",
                    {}
                )

                if not payment:

                    st.warning(
                        "No test payment found. "
                        "Create a test payment first."
                    )

                elif not transaction:

                    st.warning(
                        "Payment exists, but transaction "
                        "data is missing."
                    )

                else:

                    # =========================================
                    # PAYMENT VERIFIED
                    # =========================================

                    st.session_state.payment_created = True

                    st.session_state.payment_info = payment

                    st.success(
                        "✅ Test Payment Verified!"
                    )

                    payment_info1, payment_info2 = (
                        st.columns(2)
                    )

                    with payment_info1:

                        st.write("**Payment ID**")

                        st.code(
                            payment.get(
                                "payment_id",
                                "N/A"
                            )
                        )

                    with payment_info2:

                        st.write("**Order ID**")

                        st.code(
                            payment.get(
                                "order_id",
                                "N/A"
                            )
                        )

                    st.write(
                        "**Payment Mode:** "
                        + str(
                            payment.get(
                                "payment_mode",
                                "TEST SIMULATOR"
                            )
                        )
                    )


                    # =========================================
                    # ML INPUT
                    # =========================================

                    transaction_df = pd.DataFrame(
                        [transaction]
                    )


                    missing_features = [
                        feature
                        for feature in features
                        if feature not in transaction_df.columns
                    ]


                    if missing_features:

                        st.error(
                            "❌ Model features missing: "
                            + ", ".join(
                                missing_features
                            )
                        )

                    else:

                        X = transaction_df[
                            features
                        ]


                        # =====================================
                        # CONVERT NUMERIC
                        # =====================================

                        for column in X.columns:

                            X[column] = pd.to_numeric(
                                X[column],
                                errors="coerce"
                            )


                        # =====================================
                        # SCALE
                        # =====================================

                        X_scaled = scaler.transform(
                            X
                        )


                        # =====================================
                        # PREDICTION
                        # =====================================

                        probability = float(
                            model.predict_proba(
                                X_scaled
                            )[0, 1]
                        )


                        risk_score = round(
                            probability * 100,
                            2
                        )


                        # =====================================
                        # RISK LEVEL
                        # =====================================

                        if probability >= threshold:

                            risk_level = "HIGH"

                        elif probability >= 0.30:

                            risk_level = "MEDIUM"

                        else:

                            risk_level = "LOW"


                        # =====================================
                        # SAVE ANALYSIS
                        # =====================================

                        save_payload = {

                            "payment_id":
                                payment.get(
                                    "payment_id"
                                ),

                            "order_id":
                                payment.get(
                                    "order_id"
                                ),

                            "transaction":
                                transaction,

                            "risk_score":
                                float(
                                    risk_score
                                ),

                            "risk_level":
                                risk_level
                        }


                        try:

                            save_response = backend_post(
                                "/save-analysis",
                                save_payload,
                                timeout=30
                            )

                            if save_response.status_code == 200:

                                st.success(
                                    "✅ Transaction saved to database!"
                                )

                            else:

                                st.warning(
                                    "Risk analysis completed, "
                                    "but database save failed."
                                )

                        except Exception:

                            st.warning(
                                "Risk analysis completed, "
                                "but database save failed."
                            )


                        # =====================================
                        # STORE RESULT
                        # =====================================

                        st.session_state.analysis_result = {

                            "risk_score":
                                risk_score,

                            "probability":
                                probability,

                            "risk_level":
                                risk_level,

                            "transaction":
                                transaction,

                            "payment":
                                payment
                        }


        except requests.exceptions.ConnectionError:

            st.error(
                "❌ Payment backend is not running."
            )

            st.code(
                "python -m src.payment_server"
            )

        except requests.exceptions.Timeout:

            st.error(
                "❌ Backend request timed out."
            )

        except Exception as error:

            st.error(
                f"Analysis failed: {error}"
            )


# =========================================================
# AI RISK ANALYSIS
# =========================================================

result = st.session_state.analysis_result


if result:

    st.divider()

    st.markdown(
        '<div class="section-title">🤖 AI Risk Analysis</div>',
        unsafe_allow_html=True
    )

    risk_col1, risk_col2, risk_col3 = st.columns(3)

    with risk_col1:

        st.metric(
            "Risk Score",
            f"{result['risk_score']:.2f}/100"
        )

    with risk_col2:

        st.metric(
            "Fraud Probability",
            f"{result['probability']:.2%}"
        )

    with risk_col3:

        st.metric(
            "Risk Level",
            result["risk_level"]
        )


    # =========================================================
    # RISK FACTORS
    # =========================================================

    st.subheader("⚠️ Risk Factors")

    transaction = result["transaction"]

    risk_factors = []


    previous_avg = float(
        transaction.get(
            "previous_avg_amount",
            0
        )
    )

    amount = float(
        transaction.get(
            "transaction_amount",
            0
        )
    )


    if previous_avg > 0:

        amount_ratio = (
            amount / previous_avg
        )

        if amount_ratio >= 2:

            risk_factors.append(
                f"Transaction amount is "
                f"{amount_ratio:.1f}× the previous average"
            )


    if transaction.get(
        "new_device",
        0
    ) == 1:

        risk_factors.append(
            "New device detected"
        )


    if transaction.get(
        "location_mismatch",
        0
    ) == 1:

        risk_factors.append(
            "Location mismatch detected"
        )


    if transaction.get(
        "failed_attempts",
        0
    ) >= 2:

        risk_factors.append(
            f"{transaction['failed_attempts']} "
            "failed payment attempts"
        )


    if transaction.get(
        "transactions_last_10min",
        0
    ) >= 2:

        risk_factors.append(
            f"{transaction['transactions_last_10min']} "
            "transactions in the last 10 minutes"
        )


    if transaction.get(
        "transactions_last_24h",
        0
    ) >= 20:

        risk_factors.append(
            f"{transaction['transactions_last_24h']} "
            "transactions in the last 24 hours"
        )


    if transaction.get(
        "international_transaction",
        0
    ) == 1:

        risk_factors.append(
            "International transaction"
        )


    if transaction.get(
        "transaction_hour",
        12
    ) in [1, 2, 3, 4, 5]:

        risk_factors.append(
            "Transaction occurred during late-night hours"
        )


    if transaction.get(
        "account_age_days",
        100
    ) <= 14:

        risk_factors.append(
            "Very new account"
        )


    if risk_factors:

        for factor in risk_factors:

            st.warning(
                "⚠️ " + factor
            )

    else:

        st.success(
            "✅ No major risk factors detected."
        )


# =========================================================
# TRANSACTION HISTORY
# =========================================================

st.divider()

st.markdown(
    '<div class="section-title">📊 Transaction History</div>',
    unsafe_allow_html=True
)


history_col1, history_col2 = st.columns(
    [5, 1]
)


with history_col1:

    st.caption(
        "Latest transactions recorded by the payment risk system."
    )


with history_col2:

    refresh_history = st.button(
        "🔄 Refresh",
        use_container_width=True,
        key="refresh_history_button"
    )


if refresh_history:

    st.rerun()


# =========================================================
# LOAD TRANSACTIONS
# =========================================================

try:

    history_response = backend_get(
        "/transactions",
        timeout=30
    )

    if history_response.status_code == 200:

        history_data = history_response.json()

        transactions = history_data.get(
            "transactions",
            []
        )


        if transactions:

            history_df = pd.DataFrame(
                transactions
            )


            # =============================================
            # EXPECTED DATABASE COLUMNS
            # =============================================

            expected_columns = [

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


            # =============================================
            # NUMERIC COLUMN NAMES
            # =============================================

            if (
                not history_df.empty
                and len(history_df.columns)
                == len(expected_columns)
            ):

                numeric_column_names = all(
                    str(column).isdigit()
                    for column in history_df.columns
                )

                if numeric_column_names:

                    history_df.columns = (
                        expected_columns
                    )


            # =============================================
            # NORMALIZE NAMES
            # =============================================

            rename_map = {

                "payment_id":
                    "Payment ID",

                "order_id":
                    "Order ID",

                "transaction_amount":
                    "Amount",

                "transaction_hour":
                    "Hour",

                "account_age_days":
                    "Account Age",

                "new_device":
                    "New Device",

                "location_mismatch":
                    "Location Mismatch",

                "failed_attempts":
                    "Failed Attempts",

                "transactions_last_10min":
                    "Transactions 10min",

                "transactions_last_24h":
                    "Transactions 24h",

                "previous_avg_amount":
                    "Previous Avg",

                "international_transaction":
                    "International",

                "risk_score":
                    "Risk Score",

                "risk_level":
                    "Risk Level"
            }


            history_df = history_df.rename(
                columns=rename_map
            )


            # =============================================
            # SORT NEWEST FIRST
            # =============================================

            if "ID" in history_df.columns:

                try:

                    history_df = history_df.sort_values(
                        by="ID",
                        ascending=False
                    )

                except Exception:

                    pass


            # =============================================
            # RISK OVERVIEW
            # =============================================

            st.subheader(
                "📊 Risk Overview"
            )


            risk_series = None

            if "Risk Level" in history_df.columns:

                risk_series = (
                    history_df["Risk Level"]
                    .astype(str)
                    .str.upper()
                    .str.strip()
                )


            total_transactions = len(
                history_df
            )

            high_risk = 0
            medium_risk = 0
            low_risk = 0


            if risk_series is not None:

                high_risk = int(
                    (
                        risk_series == "HIGH"
                    ).sum()
                )

                medium_risk = int(
                    (
                        risk_series == "MEDIUM"
                    ).sum()
                )

                low_risk = int(
                    (
                        risk_series == "LOW"
                    ).sum()
                )


            average_risk = 0.0


            if "Risk Score" in history_df.columns:

                numeric_scores = pd.to_numeric(
                    history_df["Risk Score"],
                    errors="coerce"
                )

                if numeric_scores.notna().any():

                    average_risk = float(
                        numeric_scores.mean()
                    )


            overview1, overview2, overview3, overview4, overview5 = (
                st.columns(5)
            )


            with overview1:

                st.metric(
                    "Total Transactions",
                    total_transactions
                )


            with overview2:

                st.metric(
                    "🔴 High Risk",
                    high_risk
                )


            with overview3:

                st.metric(
                    "🟡 Medium Risk",
                    medium_risk
                )


            with overview4:

                st.metric(
                    "🟢 Low Risk",
                    low_risk
                )


            with overview5:

                st.metric(
                    "Average Risk",
                    f"{average_risk:.2f}"
                )


            # =============================================
            # ONE TRANSACTION TABLE
            # =============================================

            st.subheader(
                "Recent Transactions"
            )


            preferred_columns = [

                "Payment ID",
                "Order ID",
                "Amount",
                "Hour",
                "Account Age",
                "New Device",
                "Location Mismatch",
                "Failed Attempts",
                "Risk Score",
                "Risk Level"
            ]


            display_columns = [

                column
                for column in preferred_columns
                if column in history_df.columns
            ]


            if display_columns:

                display_df = history_df[
                    display_columns
                ].copy()

            else:

                display_df = history_df.copy()


            # =============================================
            # FORMAT AMOUNT
            # =============================================

            if "Amount" in display_df.columns:

                display_df["Amount"] = pd.to_numeric(
                    display_df["Amount"],
                    errors="coerce"
                )


            # =============================================
            # FORMAT RISK SCORE
            # =============================================

            if "Risk Score" in display_df.columns:

                display_df["Risk Score"] = pd.to_numeric(
                    display_df["Risk Score"],
                    errors="coerce"
                ).round(2)


            # =============================================
            # SHOW ONLY ONE TABLE
            # =============================================

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=430
            )


            st.caption(
                f"{len(history_df)} transaction(s) recorded."
            )


        else:

            st.info(
                "No transactions found yet."
            )


    else:

        st.error(
            "Could not load transaction history."
        )


except requests.exceptions.ConnectionError:

    st.warning(
        "Transaction history unavailable because "
        "the payment backend is not running."
    )


except requests.exceptions.Timeout:

    st.warning(
        "Transaction history request timed out."
    )


except Exception as error:

    st.error(
        f"Could not load transaction history: {error}"
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "AI Payment Risk Manager • Test Simulator Mode"
)