"""
Stripe billing. This whole file is reusable as-is across all 20 concepts -
only STRIPE_PRICE_ID_STANDARD and the per-org model change.
"""
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.db.database import get_db
from app.db.models import Organization, SubscriptionStatus, User

router = APIRouter(prefix="/api/billing", tags=["billing"])
settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/create-checkout-session")
def create_checkout_session(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=user.email,
        line_items=[{"price": settings.STRIPE_PRICE_ID_STANDARD, "quantity": 1}],
        success_url=f"{settings.FRONTEND_URL}/dashboard?checkout=success",
        cancel_url=f"{settings.FRONTEND_URL}/pricing?checkout=canceled",
        client_reference_id=org.id,
    )
    return {"checkout_url": session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook signature") from exc

    data = event["data"]["object"]

    if event["type"] == "checkout.session.completed":
        org = db.query(Organization).filter(Organization.id == data.get("client_reference_id")).first()
        if org:
            org.stripe_customer_id = data.get("customer")
            org.stripe_subscription_id = data.get("subscription")
            org.subscription_status = SubscriptionStatus.active
            db.commit()

    elif event["type"] in ("customer.subscription.updated", "customer.subscription.deleted"):
        org = (
            db.query(Organization)
            .filter(Organization.stripe_subscription_id == data.get("id"))
            .first()
        )
        if org:
            status_map = {
                "active": SubscriptionStatus.active,
                "past_due": SubscriptionStatus.past_due,
                "canceled": SubscriptionStatus.canceled,
                "unpaid": SubscriptionStatus.past_due,
            }
            org.subscription_status = status_map.get(data.get("status"), org.subscription_status)
            db.commit()

    return {"received": True}
