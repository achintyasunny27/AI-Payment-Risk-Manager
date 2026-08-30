import uuid
import os
import razorpay

from flask import Flask, request, jsonify, render_template_string
from dotenv import load_dotenv
from src.database import (
    initialize_database,
    save_transaction,
    get_transactions
)

load_dotenv()

KEY_ID = os.getenv("RAZORPAY_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
print("RAZORPAY KEY ID:", KEY_ID[:12] if KEY_ID else "MISSING", flush=True)
print("RAZORPAY SECRET PRESENT:", bool(KEY_SECRET), flush=True)
print("RAZORPAY SECRET LENGTH:", len(KEY_SECRET) if KEY_SECRET else 0, flush=True)


client = razorpay.Client(
    auth=(KEY_ID, KEY_SECRET)
)

latest_transaction = {}
latest_payment = {}
latest_order = {}
app = Flask(__name__)
initialize_database()


@app.route("/")
def home():

    if not latest_order:
        return """
        <h1>AI Payment Risk Manager</h1>
        <p>No payment order is ready.</p>
        <p>Go back to the Streamlit dashboard and create an order first.</p>
        """

    html = """
    <!DOCTYPE html>

    <html>

    <head>

        <title>AI Payment Risk Manager</title>

        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>

    </head>

    <body>

        <h1>AI Payment Risk Manager</h1>

        <h2>Razorpay Test Checkout</h2>

        <p>Amount: ₹AMOUNT_PLACEHOLDER</p>

        <button id="payButton">
            Pay Now - Test Mode
        </button>


        <script>

        document.getElementById("payButton").addEventListener(
            "click",
            startPayment
        );


        function startPayment() {

            const options = {

                key: "KEY_ID_PLACEHOLDER",

                amount: AMOUNT_PAISE_PLACEHOLDER,

                currency: "INR",

                name: "AI Payment Risk Manager",

                description: "AI Risk Manager Test Payment",

                order_id: "ORDER_ID_PLACEHOLDER",


                handler: async function(paymentResponse) {

                    const verifyResponse = await fetch(
                        "/verify-payment",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type": "application/json"
                            },

                            body: JSON.stringify(
                                paymentResponse
                            )
                        }
                    );


                    const result =
                        await verifyResponse.json();


                    if (result.success) {

                        alert(
                            "PAYMENT VERIFIED!\\n\\n" +
                            "Payment ID: " +
                            result.payment_id +
                            "\\n\\n" +
                            "You can now return to the dashboard."
                        );

                    } else {

                        alert(
                            "PAYMENT VERIFICATION FAILED!\\n\\n" +
                            result.message
                        );

                    }

                }

            };


            const razorpayCheckout =
                new Razorpay(options);


            razorpayCheckout.open();

        }

        </script>

    </body>

    </html>
    """

    amount_paise = latest_order["amount"]
    amount_rupees = amount_paise / 100

    html = html.replace(
        "KEY_ID_PLACEHOLDER",
        KEY_ID
    )

    html = html.replace(
        "ORDER_ID_PLACEHOLDER",
        latest_order["id"]
    )

    html = html.replace(
        "AMOUNT_PAISE_PLACEHOLDER",
        str(amount_paise)
    )

    html = html.replace(
        "AMOUNT_PLACEHOLDER",
        f"{amount_rupees:.2f}"
    )

    return render_template_string(html)
@app.route("/create-order", methods=["POST"])
def create_order():
    global latest_transaction
    global latest_order

    data = request.get_json() or {}

    amount_rupees = float(
        data.get("transaction_amount", 100)
    )

    latest_transaction = data

    order_data = {
        "amount": int(amount_rupees * 100),
        "currency": "INR",
        "receipt": f"risk_manager_{uuid.uuid4().hex[:10]}"
    }

    print("=== CREATE ORDER CALLED ===", flush=True)
    print("ORDER DATA:", order_data, flush=True)

    try:
        order = client.order.create(
            data=order_data
        )

        latest_order = order

        print("=== RAZORPAY ORDER CREATED ===", flush=True)
        print("ORDER ID:", order.get("id"), flush=True)

        return jsonify(order), 200

    except Exception as error:
        print("=== RAZORPAY ERROR ===", flush=True)
        print("ERROR TYPE:", type(error).__name__, flush=True)
        print("ERROR:", repr(error), flush=True)

        return jsonify({
            "error": "Razorpay order creation failed",
            "details": str(error)
        }), 500

@app.route("/verify-payment", methods=["POST"])
def verify_payment():
    global latest_payment

    data = request.get_json() or {}

    # DEMO PAYMENT
    # If the order was created in demo mode,
    # skip Razorpay signature verification.
    if latest_order.get("demo") is True:

        latest_payment = {
            "payment_id": f"demo_payment_{uuid.uuid4().hex[:10]}",
            "order_id": latest_order["id"],
            "transaction": latest_transaction,
            "status": "verified",
            "demo": True
        }

        print("DEMO PAYMENT VERIFIED")

        return jsonify({
            "success": True,
            "message": "Demo payment verified",
            "payment_id": latest_payment["payment_id"],
            "order_id": latest_payment["order_id"],
            "transaction": latest_transaction,
            "demo": True
        })

    # REAL RAZORPAY PAYMENT
    try:

        client.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"]
        })

        latest_payment = {
            "payment_id": data["razorpay_payment_id"],
            "order_id": data["razorpay_order_id"],
            "transaction": latest_transaction,
            "status": "verified",
            "demo": False
        }

        return jsonify({
            "success": True,
            "message": "Payment signature verified",
            "payment_id": data["razorpay_payment_id"],
            "order_id": data["razorpay_order_id"],
            "transaction": latest_transaction,
            "demo": False
        })

    except Exception as error:

        print("Payment verification error:", error)

        return jsonify({
            "success": False,
            "message": "Payment verification failed"
        }), 400
@app.route("/transaction", methods=["GET"])
def get_transaction():

    return jsonify({
        "transaction": latest_transaction,
        "payment": latest_payment
    })
@app.route("/save-analysis", methods=["POST"])
def save_analysis():

    data = request.get_json()

    try:

        save_transaction(
            payment_id=data["payment_id"],
            order_id=data["order_id"],
            transaction=data["transaction"],
            risk_score=data["risk_score"],
            risk_level=data["risk_level"]
        )

        return jsonify({
            "success": True,
            "message": "Transaction saved successfully"
        })

    except Exception as error:

        print(
            "Database save error:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Could not save transaction"
        }), 500

@app.route("/payment-status", methods=["GET"])
def payment_status():

    return jsonify({
        "payment": latest_payment,
        "transaction": latest_transaction
    })
@app.route("/transactions", methods=["GET"])
def get_all_transactions():

    try:

        transactions = get_transactions()

        return jsonify({
            "success": True,
            "transactions": transactions
        })

    except Exception as error:

        print(
            "Database fetch error:",
            error
        )

        return jsonify({
            "success": False,
            "message": "Could not fetch transactions"
        }), 500

print("=== PAYMENT SERVER LOADED ===", flush=True)
print("ROUTES:", app.url_map, flush=True)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "Payment backend is running"
    })

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
