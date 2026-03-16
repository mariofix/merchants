"""merchants-store — minimal demo store using flask-merchants.

Run locally::

    pip install -r requirements.txt
    flask --app app run --debug

Or with Docker::

    docker run -p 8000:8000 -e SECRET_KEY=change-me mariofix/merchants-store
"""

from __future__ import annotations

import os

from flask import Flask, redirect, render_template, request, url_for
from flask_admin import Admin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer

from flask_merchants import FlaskMerchants
from flask_merchants.contrib.sqla import PaymentModelView
from flask_merchants.models import PaymentMixin


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Payment(PaymentMixin, db.Model):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)


# ---------------------------------------------------------------------------
# Demo product catalogue (hardcoded — no DB needed)
# ---------------------------------------------------------------------------

PRODUCTS = [
    {
        "id": "prod_001",
        "name": "SDK Starter Pack",
        "description": "Everything you need to integrate payments in one afternoon.",
        "price": "9.99",
        "currency": "USD",
        "emoji": "📦",
    },
    {
        "id": "prod_002",
        "name": "Pro Licence",
        "description": "Unlimited providers, priority support, and coffee-fuelled updates.",
        "price": "49.99",
        "currency": "USD",
        "emoji": "🚀",
    },
    {
        "id": "prod_003",
        "name": "Enterprise Bundle",
        "description": "Custom SLAs, on-prem deployment, and a dedicated Slack channel.",
        "price": "299.00",
        "currency": "USD",
        "emoji": "🏢",
    },
]


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///store.db"
    )
    app.config["MERCHANTS_URL_PREFIX"] = "/pay"

    # Optional: set a webhook base URL so providers can call back
    if webhook_base := os.environ.get("MERCHANTS_WEBHOOK_BASE_URL"):
        app.config["MERCHANTS_WEBHOOK_BASE_URL"] = webhook_base

    # SQLAlchemy
    db.init_app(app)

    # flask-merchants (DummyProvider by default; swap via env)
    ext = FlaskMerchants(app, db=db, models=[Payment])

    # Flask-Admin
    admin = Admin(app, name="Merchants Store", template_mode="bootstrap4")
    admin.add_view(
        PaymentModelView(Payment, db.session, ext=ext, name="Payments")
    )

    # Create tables
    with app.app_context():
        db.create_all()

    # ------------------------------------------------------------------
    # Store routes
    # ------------------------------------------------------------------

    @app.route("/")
    def catalog():
        return render_template("catalog.html", products=PRODUCTS)

    @app.route("/checkout/<product_id>", methods=["GET", "POST"])
    def checkout(product_id: str):
        product = next((p for p in PRODUCTS if p["id"] == product_id), None)
        if product is None:
            return redirect(url_for("catalog"))

        if request.method == "POST":
            try:
                payment = Payment.create(
                    amount=product["price"],
                    currency=product["currency"],
                    provider=os.environ.get("MERCHANTS_PROVIDER", "dummy"),
                    success_url=url_for("payment_success", _external=True),
                    cancel_url=url_for("payment_cancel", _external=True),
                    email=request.form.get("email") or None,
                    request_context={"product_id": product_id, "product_name": product["name"]},
                )
                redirect_url = payment.response_payload.get("redirect_url", url_for("payment_success"))
                return redirect(redirect_url)
            except Exception as exc:
                return render_template("checkout.html", product=product, error=str(exc))

        return render_template("checkout.html", product=product, error=None)

    @app.route("/success")
    def payment_success():
        return render_template("success.html")

    @app.route("/cancel")
    def payment_cancel():
        return render_template("cancel.html")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
