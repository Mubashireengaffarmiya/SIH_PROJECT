from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel

from database.database import get_db, User, Inspection, ReviewAction, AuditLog
from routers.auth import get_current_user, require_role
from models.schemas import InspectionSummary

router = APIRouter(prefix="/api/reviewer", tags=["Reviewer"])

class ReviewActionRequest(BaseModel):
    action: str  # CONFIRM | REJECT | RETAKE | NOT_VERIFIABLE
    comment: str = ""

@router.get("/queue")
def get_review_queue(db: Session = Depends(get_db), current_user: User = Depends(require_role(["REVIEWER", "ADMIN"]))):
    inspections = db.query(Inspection).filter(Inspection.status == "NEEDS_HUMAN_REVIEW").order_by(Inspection.created_at.desc()).all()
    result = []
    for insp in inspections:
        result.append(InspectionSummary(
            inspection_id=insp.inspection_id,
            created_at=insp.created_at,
            product_name=insp.product_name,
            status=insp.status,
            overall_confidence=insp.overall_confidence,
            image_quality=insp.image_quality,
            violation_count=sum(1 for evaluation in insp.evaluations if evaluation.result == "NON-COMPLIANT"),
            is_demo=insp.is_demo,
        ))
    return result

@router.post("/inspections/{inspection_id}/review")
def review_inspection(inspection_id: str, request: ReviewActionRequest, db: Session = Depends(get_db), current_user: User = Depends(require_role(["REVIEWER", "ADMIN"]))):
    insp = db.query(Inspection).filter(Inspection.inspection_id == inspection_id).first()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
    
    # Save review action
    review = ReviewAction(
        inspection_id=inspection_id,
        reviewer_username=current_user.username,
        action=request.action,
        comment=request.comment
    )
    db.add(review)
    
    # Update status based on action
    if request.action == "CONFIRM":
        insp.status = "VERIFIED_COMPLIANT"
    elif request.action == "REJECT":
        insp.status = "POTENTIAL_VIOLATION"
    elif request.action in ("RETAKE", "NOT_VERIFIABLE"):
        insp.status = request.action
        
    insp.review_status = "APPROVED" if request.action in ("CONFIRM", "REJECT") else request.action
    
    # Audit log
    db.add(AuditLog(
        username=current_user.username,
        action="REVIEW_INSPECTION",
        resource_type="inspection",
        resource_id=inspection_id,
        detail=f"Action: {request.action}, Comment: {request.comment}"
    ))
    
    db.commit()
    return {"status": "success", "message": "Review recorded successfully"}
