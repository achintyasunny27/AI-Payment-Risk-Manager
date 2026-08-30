from src.payment_server import app

@app.route("/health")
def health():
    return {
        "status": "ok",
        "message": "Payment backend is running"
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)