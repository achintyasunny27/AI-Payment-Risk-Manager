import os
import uuid
import razorpay
from dotenv import load_dotenv

load_dotenv()

KEY_ID = os.getenv("RAZORPAY_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

client = razorpay.Client(
    auth=(KEY_ID, KEY_SECRET)
)


def create_test_order(amount_rupees):

    amount_paise = int(amount_rupees * 100)

    order_data = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"risk_manager_{uuid.uuid4().hex[:10]}"
    }

    order = client.order.create(data=order_data)

    return order