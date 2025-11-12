"""
GDPR Compliance API Endpoints

Provides endpoints for GDPR rights:
- Right of Access (Article 15)
- Right to Erasure (Article 17)
- Right to Data Portability (Article 20)
- Consent Management (Article 7)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os

from ..utils.database import get_db
from ..utils.auth import get_current_user, get_current_active_user, get_admin_or_teacher
from ..utils.gdpr import (
    collect_user_data,
    create_export_file,
    process_export_request,
    process_deletion_request,
    record_consent,
    withdraw_consent,
    get_active_consents,
    has_consent,
)
from ..utils.audit import (
    log_audit_event,
    get_client_ip,
    get_user_agent,
    EventType,
    EventCategory,
    EventResult,
)
from ..models import User
from ..models.gdpr import (
    ConsentRecord,
    DataExportRequest,
    DataDeletionRequest,
    PrivacyPolicyVersion,
)

router = APIRouter(prefix="/api/gdpr", tags=["gdpr"])


# ==================== Pydantic Schemas ====================

class DataExportRequestCreate(BaseModel):
    export_format: str = "JSON"  # JSON, CSV


class DataExportResponse(BaseModel):
    id: int
    user_id: int
    requested_at: datetime
    status: str
    export_format: str
    completed_at: Optional[datetime]
    file_size_bytes: Optional[int]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class DataDeletionRequestCreate(BaseModel):
    deletion_scope: str = "ANONYMIZE"  # ANONYMIZE or FULL
    reason: Optional[str] = None
    confirm_deletion: bool  # User must explicitly confirm


class DataDeletionResponse(BaseModel):
    id: int
    user_id: int
    username: str
    email: str
    requested_at: datetime
    status: str
    deletion_scope: str
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ConsentCreate(BaseModel):
    consent_type: str  # "terms_of_service", "privacy_policy", "marketing", etc.
    consented: bool
    version: str


class ConsentResponse(BaseModel):
    id: int
    consent_type: str
    purpose: str
    consented: bool
    consented_at: Optional[datetime]
    withdrawn_at: Optional[datetime]
    version: str
    method: str

    class Config:
        from_attributes = True


class PrivacyPolicyResponse(BaseModel):
    id: int
    document_type: str
    version: str
    title: str
    summary: Optional[str]
    effective_date: datetime
    is_active: bool

    class Config:
        from_attributes = True


# ==================== Data Export Endpoints (Article 15 & 20) ====================

@router.post("/export-request", response_model=DataExportResponse, status_code=status.HTTP_201_CREATED)
def request_data_export(
    export_request: DataExportRequestCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Request data export (GDPR Article 15 - Right of access, Article 20 - Data portability).

    User can request their personal data in a machine-readable format.
    Export will be processed asynchronously and available for download.
    """
    # Check for pending requests
    pending = db.query(DataExportRequest).filter(
        DataExportRequest.user_id == current_user.id,
        DataExportRequest.status.in_(["PENDING", "PROCESSING"])
    ).first()

    if pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending export request. Please wait for it to complete."
        )

    # Create export request
    export_req = DataExportRequest(
        user_id=current_user.id,
        export_format=export_request.export_format.upper(),
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    db.add(export_req)
    db.commit()
    db.refresh(export_req)

    # Log the request
    log_audit_event(
        db=db,
        event_type=EventType.EXPORT,
        event_category=EventCategory.DATA,
        result=EventResult.SUCCESS,
        action="Data export requested",
        user_id=current_user.id,
        username=current_user.username,
        user_role=current_user.role,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        description=f"User requested data export in {export_request.export_format} format"
    )

    # Process export immediately (in production, use background task)
    process_export_request(db, export_req.id)
    db.refresh(export_req)

    return export_req


@router.get("/export-requests", response_model=List[DataExportResponse])
def get_my_export_requests(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all data export requests for current user.
    """
    requests = db.query(DataExportRequest).filter(
        DataExportRequest.user_id == current_user.id
    ).order_by(DataExportRequest.requested_at.desc()).all()

    return requests


@router.get("/export-requests/{request_id}", response_model=DataExportResponse)
def get_export_request(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific export request.
    """
    export_req = db.query(DataExportRequest).filter(
        DataExportRequest.id == request_id,
        DataExportRequest.user_id == current_user.id
    ).first()

    if not export_req:
        raise HTTPException(status_code=404, detail="Export request not found")

    return export_req


@router.get("/export-requests/{request_id}/download")
def download_export_file(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Download the exported data file.
    """
    export_req = db.query(DataExportRequest).filter(
        DataExportRequest.id == request_id,
        DataExportRequest.user_id == current_user.id
    ).first()

    if not export_req:
        raise HTTPException(status_code=404, detail="Export request not found")

    if export_req.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export is not ready. Current status: {export_req.status}"
        )

    if not export_req.file_path or not os.path.exists(export_req.file_path):
        raise HTTPException(status_code=404, detail="Export file not found")

    # Check expiration
    if export_req.expires_at and datetime.utcnow() > export_req.expires_at:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Export file has expired. Please request a new export."
        )

    # Update download count
    export_req.download_count += 1
    export_req.last_downloaded_at = datetime.utcnow()
    db.commit()

    # Return file
    filename = os.path.basename(export_req.file_path)
    return FileResponse(
        export_req.file_path,
        media_type="application/json",
        filename=filename
    )


@router.get("/my-data")
def get_my_data_preview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a preview of user's data without creating an export file.

    Useful for users to see what data is stored about them.
    """
    user_data = collect_user_data(db, current_user.id)
    return user_data


# ==================== Data Deletion Endpoints (Article 17) ====================

@router.post("/deletion-request", response_model=DataDeletionResponse, status_code=status.HTTP_201_CREATED)
def request_data_deletion(
    deletion_request: DataDeletionRequestCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Request account and data deletion (GDPR Article 17 - Right to erasure).

    This will delete or anonymize all user data. This action cannot be undone.

    Two deletion scopes:
    - ANONYMIZE: Remove PII but keep statistical data (recommended)
    - FULL: Complete deletion of all data
    """
    if not deletion_request.confirm_deletion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must confirm deletion by setting confirm_deletion to true"
        )

    # Check for pending requests
    pending = db.query(DataDeletionRequest).filter(
        DataDeletionRequest.user_id == current_user.id,
        DataDeletionRequest.status.in_(["PENDING", "PROCESSING"])
    ).first()

    if pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending deletion request."
        )

    # Create deletion request
    deletion_req = DataDeletionRequest(
        user_id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        deletion_scope=deletion_request.deletion_scope.upper(),
        reason=deletion_request.reason,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    db.add(deletion_req)
    db.commit()
    db.refresh(deletion_req)

    # Log the request
    log_audit_event(
        db=db,
        event_type=EventType.DELETE,
        event_category=EventCategory.DATA,
        result=EventResult.SUCCESS,
        action="Data deletion requested",
        user_id=current_user.id,
        username=current_user.username,
        user_role=current_user.role,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        description=f"User requested account deletion ({deletion_request.deletion_scope})"
    )

    # Note: In production, this should require admin approval or a grace period
    # For now, we'll process it immediately for ANONYMIZE, but require approval for FULL
    if deletion_request.deletion_scope.upper() == "ANONYMIZE":
        # Process anonymization immediately
        process_deletion_request(db, deletion_req.id)
        db.refresh(deletion_req)

    return deletion_req


@router.get("/deletion-requests", response_model=List[DataDeletionResponse])
def get_my_deletion_requests(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all data deletion requests for current user.
    """
    requests = db.query(DataDeletionRequest).filter(
        DataDeletionRequest.user_id == current_user.id
    ).order_by(DataDeletionRequest.requested_at.desc()).all()

    return requests


@router.delete("/deletion-requests/{request_id}")
def cancel_deletion_request(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a pending deletion request (only if not yet processed).
    """
    deletion_req = db.query(DataDeletionRequest).filter(
        DataDeletionRequest.id == request_id,
        DataDeletionRequest.user_id == current_user.id
    ).first()

    if not deletion_req:
        raise HTTPException(status_code=404, detail="Deletion request not found")

    if deletion_req.status not in ["PENDING"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel request with status: {deletion_req.status}"
        )

    deletion_req.status = "CANCELLED"
    db.commit()

    return {"message": "Deletion request cancelled successfully"}


# ==================== Admin Endpoints for Deletion Approval ====================

@router.get("/admin/deletion-requests", response_model=List[DataDeletionResponse])
def get_all_deletion_requests(
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_admin_or_teacher),
    db: Session = Depends(get_db)
):
    """
    Admin: Get all deletion requests.
    """
    query = db.query(DataDeletionRequest)

    if status_filter:
        query = query.filter(DataDeletionRequest.status == status_filter.upper())

    requests = query.order_by(DataDeletionRequest.requested_at.desc()).offset(skip).limit(limit).all()

    return requests


@router.post("/admin/deletion-requests/{request_id}/approve")
def approve_deletion_request(
    request_id: int,
    current_user: User = Depends(get_admin_or_teacher),
    db: Session = Depends(get_db)
):
    """
    Admin: Approve and process a deletion request.
    """
    deletion_req = db.query(DataDeletionRequest).filter(
        DataDeletionRequest.id == request_id
    ).first()

    if not deletion_req:
        raise HTTPException(status_code=404, detail="Deletion request not found")

    if deletion_req.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve request with status: {deletion_req.status}"
        )

    # Process deletion
    success = process_deletion_request(db, request_id, approved_by_id=current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process deletion request"
        )

    db.refresh(deletion_req)

    return {
        "message": "Deletion request approved and processed",
        "request": deletion_req
    }


# ==================== Consent Management Endpoints (Article 7) ====================

@router.post("/consent", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
def give_consent(
    consent: ConsentCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Record user consent for data processing.
    """
    # Define purposes for different consent types
    purposes = {
        "terms_of_service": "Agreement to Terms of Service for using the Study Platform",
        "privacy_policy": "Consent to Privacy Policy for processing personal data",
        "marketing": "Consent to receive marketing communications and newsletters",
        "analytics": "Consent to collect usage analytics for service improvement",
    }

    purpose = purposes.get(consent.consent_type, "Data processing consent")

    consent_record = record_consent(
        db=db,
        user_id=current_user.id,
        consent_type=consent.consent_type,
        purpose=purpose,
        version=consent.version,
        consented=consent.consented,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )

    # Log consent action
    log_audit_event(
        db=db,
        event_type="CONSENT_GIVEN" if consent.consented else "CONSENT_WITHDRAWN",
        event_category=EventCategory.DATA,
        result=EventResult.SUCCESS,
        action=f"Consent {'given' if consent.consented else 'withdrawn'} for {consent.consent_type}",
        user_id=current_user.id,
        username=current_user.username,
        user_role=current_user.role,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        description=f"User {'consented to' if consent.consented else 'withdrew consent for'} {consent.consent_type} (v{consent.version})"
    )

    return consent_record


@router.get("/consent", response_model=List[ConsentResponse])
def get_my_consents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all consent records for current user.
    """
    consents = get_active_consents(db, current_user.id)
    return consents


@router.delete("/consent/{consent_type}")
def withdraw_user_consent(
    consent_type: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Withdraw consent for a specific type.
    """
    success = withdraw_consent(db, current_user.id, consent_type)

    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"No active consent found for type: {consent_type}"
        )

    # Log consent withdrawal
    log_audit_event(
        db=db,
        event_type="CONSENT_WITHDRAWN",
        event_category=EventCategory.DATA,
        result=EventResult.SUCCESS,
        action=f"Consent withdrawn for {consent_type}",
        user_id=current_user.id,
        username=current_user.username,
        user_role=current_user.role,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
        description=f"User withdrew consent for {consent_type}"
    )

    return {"message": f"Consent withdrawn for {consent_type}"}


# ==================== Privacy Policy Endpoints ====================

@router.get("/privacy-policies", response_model=List[PrivacyPolicyResponse])
def get_privacy_policies(
    document_type: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get privacy policy versions.
    """
    query = db.query(PrivacyPolicyVersion)

    if document_type:
        query = query.filter(PrivacyPolicyVersion.document_type == document_type)

    if active_only:
        query = query.filter(PrivacyPolicyVersion.is_active == True)

    policies = query.order_by(PrivacyPolicyVersion.effective_date.desc()).all()

    return policies


@router.get("/privacy-policies/{version}")
def get_privacy_policy_version(
    version: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific privacy policy version.
    """
    policy = db.query(PrivacyPolicyVersion).filter(
        PrivacyPolicyVersion.version == version
    ).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Privacy policy version not found")

    return policy
