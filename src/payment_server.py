import os
import uuid

from flask import (
    Flask,
    request,
    jsonify,
    render_template_string
)

from src.database import (
    initialize_database,
    save_transaction,
    get_transactions
)


# =========================================================
# APP
# =========================================================

app = Flask(__name__)

initialize_database()


# =========================================================
# CURRENT PAYMENT STATE
# =========================================================

latest_transaction = {}
latest_payment = {}
latest_order = {}


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():

    if not latest_order:

        return """
        <!DOCTYPE html>

        <html>

        <head>
            <title>AI Payment Risk Manager</title>
        </head>

        <body style="
            font-family: Arial;
            background: #0e1117;
            color: white;
            padding: 50px;
        ">

            <h1>🛡️ AI Payment Risk Manager</h1>

            <h2>🧪 Test Payment Simulator</h2>

            <p>
                Payment backend is running.
            </p>

            <p>
                No real money is processed.
            </p>

            <p>
                Create a test payment from the
                Streamlit dashboard.
            </p>

        </body>

        </html>
        """


    amount_rupees = (
        latest_order["amount"] / 100
    )


    return render_template_string(
        """
        <!DOCTYPE html>

        <html>

        <head>

            <title>
                AI Payment Risk Manager
            </title>

        </head>

        <body style="
            font-family: Arial;
            background: #0e1117;
            color: white;
            padding: 50px;
        ">

        <div style="
            max-width: 600px;
            margin: auto;
            background: #1b1f27;
            padding: 35px;
            border-radius: 15px;
        ">

            <h1>🧪 Test Payment</h1>

            <h2>
                AI Payment Risk Manager
            </h2>

            <hr>

            <h2>
                Amount: ₹{{ amount }}
            </h2>

            <p>
                <b>Order ID:</b>
                {{ order_id }}
            </p>

            <p>
                <b>Payment ID:</b>
                {{ payment_id }}
            </p>

            <p style="
                color: #00ff88;
                font-weight: bold;
            ">
                ✅ TEST PAYMENT VERIFIED
            </p>

            <p>
                This is a simulated payment.
                No real money has been charged.
            </p>

            <p>
                Return to the Streamlit dashboard
                and click
                <b>Check Payment & Analyze</b>.
            </p>

        </div>

        </body>

        </html>
        """,

        amount=f"{amount_rupees:.2f}",

        order_id=latest_order["id"],

        payment_id=latest_payment.get(
            "payment_id",
            "N/A"
        )
    )


# =========================================================
# CREATE TEST ORDER
# =========================================================

@app.route(
    "/create-order",
    methods=["POST"]
)
def create_order():

    global latest_transaction
    global latest_order
    global latest_payment


    data = request.get_json(
        silent=True
    ) or {}


    # -----------------------------------------------------
    # AMOUNT
    # -----------------------------------------------------

    try:

        amount_rupees = float(
            data.get(
                "transaction_amount",
                100
            )
        )

    except (
        ValueError,
        TypeError
    ):

        return jsonify({

            "success": False,

            "message":
                "Invalid transaction amount"

        }), 400


    if amount_rupees <= 0:

        return jsonify({

            "success": False,

            "message":
                "Transaction amount must be greater than zero"

        }), 400


    # -----------------------------------------------------
    # SAVE TRANSACTION IN MEMORY
    # -----------------------------------------------------

    latest_transaction = data


    # -----------------------------------------------------
    # CREATE TEST IDs
    # -----------------------------------------------------

    order_id = (
        "test_order_"
        + uuid.uuid4().hex[:10]
    )


    payment_id = (
        "test_payment_"
        + uuid.uuid4().hex[:10]
    )


    # -----------------------------------------------------
    # CREATE TEST ORDER
    # -----------------------------------------------------

    latest_order = {

        "id":
            order_id,

        "amount":
            int(
                round(
                    amount_rupees * 100
                )
            ),

        "currency":
            "INR",

        "receipt":
            "risk_manager_"
            + uuid.uuid4().hex[:10],

        "status":
            "created",

        "demo":
            True
    }


    # -----------------------------------------------------
    # AUTOMATIC TEST PAYMENT
    # -----------------------------------------------------

    latest_payment = {

        "payment_id":
            payment_id,

        "order_id":
            order_id,

        "transaction":
            latest_transaction,

        "status":
            "verified",

        "demo":
            True,

        "payment_mode":
            "TEST SIMULATOR"
    }


    # -----------------------------------------------------
    # LOGS
    # -----------------------------------------------------

    print(
        "\n========================================",
        flush=True
    )

    print(
        "       TEST PAYMENT CREATED",
        flush=True
    )

    print(
        "========================================",
        flush=True
    )

    print(
        "ORDER ID:",
        order_id,
        flush=True
    )

    print(
        "PAYMENT ID:",
        payment_id,
        flush=True
    )

    print(
        "AMOUNT:",
        amount_rupees,
        "INR",
        flush=True
    )

    print(
        "STATUS: VERIFIED",
        flush=True
    )

    print(
        "========================================\n",
        flush=True
    )


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return jsonify({

        "success":
            True,

        "id":
            order_id,

        "amount":
            latest_order["amount"],

        "currency":
            "INR",

        "receipt":
            latest_order["receipt"],

        "status":
            "created",

        "demo":
            True,

        "payment_id":
            payment_id,

        "payment_status":
            "verified",

        "payment_mode":
            "TEST SIMULATOR"

    }), 200


# =========================================================
# VERIFY PAYMENT
# =========================================================

@app.route(
    "/verify-payment",
    methods=["POST"]
)
def verify_payment():

    global latest_payment


    data = request.get_json(
        silent=True
    ) or {}


    if not latest_order:

        return jsonify({

            "success":
                False,

            "message":
                "No test payment has been created yet."

        }), 400


    payment_id = data.get(
        "payment_id"
    )


    if not payment_id:

        payment_id = latest_payment.get(
            "payment_id"
        )


    if not payment_id:

        payment_id = (
            "test_payment_"
            + uuid.uuid4().hex[:10]
        )


    latest_payment = {

        "payment_id":
            payment_id,

        "order_id":
            latest_order["id"],

        "transaction":
            latest_transaction,

        "status":
            "verified",

        "demo":
            True,

        "payment_mode":
            "TEST SIMULATOR"
    }


    print(
        "=== TEST PAYMENT VERIFIED ===",
        payment_id,
        flush=True
    )


    return jsonify({

        "success":
            True,

        "message":
            "Test payment verified",

        "payment_id":
            payment_id,

        "order_id":
            latest_order["id"],

        "transaction":
            latest_transaction,

        "demo":
            True,

        "payment_mode":
            "TEST SIMULATOR"

    }), 200


# =========================================================
# CURRENT TRANSACTION
# =========================================================

@app.route(
    "/transaction",
    methods=["GET"]
)
def get_transaction():

    return jsonify({

        "success":
            True,

        "transaction":
            latest_transaction,

        "payment":
            latest_payment,

        "order":
            latest_order

    }), 200


# =========================================================
# PAYMENT STATUS
# =========================================================

@app.route(
    "/payment-status",
    methods=["GET"]
)
def payment_status():

    return jsonify({

        "success":
            True,

        "payment":
            latest_payment,

        "transaction":
            latest_transaction,

        "order":
            latest_order

    }), 200


# =========================================================
# SAVE AI ANALYSIS
# =========================================================

@app.route(
    "/save-analysis",
    methods=["POST"]
)
def save_analysis():

    data = request.get_json(
        silent=True
    ) or {}


    required_fields = [

        "payment_id",

        "order_id",

        "transaction",

        "risk_score",

        "risk_level"
    ]


    missing_fields = [

        field

        for field in required_fields

        if field not in data
    ]


    if missing_fields:

        return jsonify({

            "success":
                False,

            "message":
                "Missing required fields",

            "missing":
                missing_fields

        }), 400


    try:

        save_transaction(

            payment_id =
                data["payment_id"],

            order_id =
                data["order_id"],

            transaction =
                data["transaction"],

            risk_score =
                float(
                    data["risk_score"]
                ),

            risk_level =
                str(
                    data["risk_level"]
                )
        )


        print(
            "=== TRANSACTION SAVED ===",
            data["payment_id"],
            flush=True
        )


        return jsonify({

            "success":
                True,

            "message":
                "Transaction saved successfully"

        }), 200


    except Exception as error:

        print(
            "DATABASE SAVE ERROR:",
            repr(error),
            flush=True
        )


        return jsonify({

            "success":
                False,

            "message":
                "Could not save transaction",

            "details":
                str(error)

        }), 500


# =========================================================
# TRANSACTION HISTORY
# =========================================================

@app.route(
    "/transactions",
    methods=["GET"]
)
def get_all_transactions():

    try:

        transactions = get_transactions()


        if transactions is None:

            transactions = []


        return jsonify({

            "success":
                True,

            "count":
                len(transactions),

            "transactions":
                transactions

        }), 200


    except Exception as error:

        print(
            "DATABASE FETCH ERROR:",
            repr(error),
            flush=True
        )


        return jsonify({

            "success":
                False,

            "message":
                "Could not fetch transactions",

            "details":
                str(error),

            "transactions":
                []

        }), 500


# =========================================================
# HEALTH
# =========================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "status":
            "ok",

        "message":
            "Payment backend is running",

        "mode":
            "TEST_SIMULATOR"

    }), 200


# =========================================================
# HEALTHZ
# =========================================================

@app.route(
    "/healthz",
    methods=["GET"]
)
def healthz():

    return jsonify({

        "status":
            "ok",

        "mode":
            "TEST_SIMULATOR"

    }), 200


# =========================================================
# SERVER START
# =========================================================

print(
    "========================================",
    flush=True
)

print(
    "       AI PAYMENT RISK MANAGER",
    flush=True
)

print(
    "       PAYMENT BACKEND LOADED",
    flush=True
)

print(
    "       MODE: TEST SIMULATOR",
    flush=True
)

print(
    "========================================",
    flush=True
)

print(
    "ROUTES:",
    app.url_map,
    flush=True
)


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )


    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

    )