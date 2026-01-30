from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ------------------ CONSTANTS ------------------

MIN_WITHDRAWAL_AMOUNT = 500

# ------------------ SEED DATA ------------------

authors = [
    {"id": 1, "name": "Priya Sharma", "email": "priya@email.com"},
    {"id": 2, "name": "Rahul Verma", "email": "rahul@email.com"},
    {"id": 3, "name": "Anita Desai", "email": "anita@email.com"}
]

books = [
    {"id": 1, "title": "The Silent River", "author_id": 1, "royalty": 45},
    {"id": 2, "title": "Midnight in Mumbai", "author_id": 1, "royalty": 60},
    {"id": 3, "title": "Code & Coffee", "author_id": 2, "royalty": 75},
    {"id": 4, "title": "Startup Diaries", "author_id": 2, "royalty": 50},
    {"id": 5, "title": "Poetry of Pain", "author_id": 2, "royalty": 30},
    {"id": 6, "title": "Garden of Words", "author_id": 3, "royalty": 40}
]

sales = [
    {"book_id": 1, "qty": 25, "date": "2025-01-05"},
    {"book_id": 1, "qty": 40, "date": "2025-01-12"},
    {"book_id": 2, "qty": 15, "date": "2025-01-08"},
    {"book_id": 3, "qty": 60, "date": "2025-01-03"},
    {"book_id": 3, "qty": 45, "date": "2025-01-15"},
    {"book_id": 4, "qty": 30, "date": "2025-01-10"},
    {"book_id": 5, "qty": 20, "date": "2025-01-18"},
    {"book_id": 6, "qty": 10, "date": "2025-01-20"}
]

withdrawals = []

# ------------------ HELPERS ------------------

def calculate_earnings(author_id):
    total = 0
    for book in books:
        if book["author_id"] == author_id:
            for sale in sales:
                if sale["book_id"] == book["id"]:
                    total += sale["qty"] * book["royalty"]
    return total

def get_withdrawn_amount(author_id):
    return sum(w["amount"] for w in withdrawals if w["author_id"] == author_id)

# ------------------ ROUTES ------------------

@app.route("/")
def home():
    return jsonify({"message": "BookLeaf Royalty API is running"})

# 1️⃣ GET /authors
@app.route("/authors", methods=["GET"])
def get_authors():
    result = []
    for author in authors:
        total = calculate_earnings(author["id"])
        withdrawn = get_withdrawn_amount(author["id"])
        result.append({
            "id": author["id"],
            "name": author["name"],
            "total_earnings": total,
            "current_balance": total - withdrawn
        })
    return jsonify(result)

# 2️⃣ GET /authors/{id}
@app.route("/authors/<int:author_id>", methods=["GET"])
def get_author(author_id):
    author = next((a for a in authors if a["id"] == author_id), None)
    if not author:
        return jsonify({"error": "Author not found"}), 404

    books_data = []
    total_earnings = calculate_earnings(author_id)
    withdrawn = get_withdrawn_amount(author_id)

    for book in books:
        if book["author_id"] == author_id:
            total_sold = sum(s["qty"] for s in sales if s["book_id"] == book["id"])
            books_data.append({
                "id": book["id"],
                "title": book["title"],
                "royalty_per_sale": book["royalty"],
                "total_sold": total_sold,
                "total_royalty": total_sold * book["royalty"]
            })

    return jsonify({
        "id": author["id"],
        "name": author["name"],
        "email": author["email"],
        "total_books": len(books_data),
        "total_earnings": total_earnings,
        "current_balance": total_earnings - withdrawn,
        "books": books_data
    })

# 3️⃣ GET /authors/{id}/sales
@app.route("/authors/<int:author_id>/sales", methods=["GET"])
def get_author_sales(author_id):
    author_books = [b for b in books if b["author_id"] == author_id]
    if not author_books:
        return jsonify({"error": "Author not found"}), 404

    result = []
    for sale in sales:
        book = next((b for b in author_books if b["id"] == sale["book_id"]), None)
        if book:
            result.append({
                "book_title": book["title"],
                "quantity": sale["qty"],
                "royalty_earned": sale["qty"] * book["royalty"],
                "sale_date": sale["date"]
            })

    result.sort(key=lambda x: x["sale_date"], reverse=True)
    return jsonify(result)

# 4️⃣ POST /withdrawals
@app.route("/withdrawals", methods=["POST"])
def create_withdrawal():
    data = request.get_json()

    author_id = data.get("author_id")
    amount = data.get("amount")

    author = next((a for a in authors if a["id"] == author_id), None)
    if not author:
        return jsonify({"error": "Author not found"}), 404

    if amount < MIN_WITHDRAWAL_AMOUNT:
        return jsonify({"error": "Minimum withdrawal is ₹500"}), 400

    total_earnings = calculate_earnings(author_id)
    withdrawn = get_withdrawn_amount(author_id)
    current_balance = total_earnings - withdrawn

    if amount > current_balance:
        return jsonify({"error": "Insufficient balance"}), 400

    withdrawal = {
        "id": len(withdrawals) + 1,
        "author_id": author_id,
        "amount": amount,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }

    withdrawals.append(withdrawal)

    return jsonify({
        **withdrawal,
        "new_balance": current_balance - amount
    }), 201

# 5️⃣ GET /authors/{id}/withdrawals
@app.route("/authors/<int:author_id>/withdrawals", methods=["GET"])
def get_author_withdrawals(author_id):
    author = next((a for a in authors if a["id"] == author_id), None)
    if not author:
        return jsonify({"error": "Author not found"}), 404

    result = [w for w in withdrawals if w["author_id"] == author_id]
    result.sort(key=lambda x: x["created_at"], reverse=True)
    return jsonify(result)

# ------------------ RUN APP ------------------

if __name__ == "__main__":
    app.run(debug=True)
