import sqlite3
import os


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DB_PATH = os.path.join(
    BASE_DIR,
    "data",
    "payments.db"
)


def get_connection():

    return sqlite3.connect(DB_PATH)


def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            payment_id TEXT,

            order_id TEXT,

            transaction_amount REAL,

            transaction_hour INTEGER,

            account_age_days INTEGER,

            new_device INTEGER,

            location_mismatch INTEGER,

            failed_attempts INTEGER,

            transactions_last_10min INTEGER,

            transactions_last_24h INTEGER,

            previous_avg_amount REAL,

            international_transaction INTEGER,

            risk_score REAL,

            risk_level TEXT

        )
    """)

    connection.commit()

    connection.close()


def save_transaction(
    payment_id,
    order_id,
    transaction,
    risk_score,
    risk_level
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO transactions (

            payment_id,
            order_id,
            transaction_amount,
            transaction_hour,
            account_age_days,
            new_device,
            location_mismatch,
            failed_attempts,
            transactions_last_10min,
            transactions_last_24h,
            previous_avg_amount,
            international_transaction,
            risk_score,
            risk_level

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        payment_id,
        order_id,

        transaction["transaction_amount"],
        transaction["transaction_hour"],
        transaction["account_age_days"],
        transaction["new_device"],
        transaction["location_mismatch"],
        transaction["failed_attempts"],
        transaction["transactions_last_10min"],
        transaction["transactions_last_24h"],
        transaction["previous_avg_amount"],
        transaction["international_transaction"],

        risk_score,
        risk_level

    ))

    connection.commit()

    connection.close()

def get_transactions():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM transactions
        ORDER BY id DESC
    """)

    transactions = cursor.fetchall()

    connection.close()

    return transactions


if __name__ == "__main__":

    initialize_database()

    print("Database initialized successfully!")