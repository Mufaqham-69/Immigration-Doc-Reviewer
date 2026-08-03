from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.database import get_db
from app.db.models import Organization, SubscriptionStatus, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_active_subscription(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> User:
    """
    Gate expensive agent endpoints (document processing) behind an active
    subscription. Trialing orgs get a grace period; everything else must be
    'active'. Attach this dependency to any route that costs you LLM tokens.
    """
    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    if org.subscription_status not in (SubscriptionStatus.active, SubscriptionStatus.trialing):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Subscription inactive. Update billing to continue processing documents.",
        )
    return user
