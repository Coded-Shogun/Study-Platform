"""
GDPR compliance models for consent management and privacy tracking.

Supports GDPR Articles 6, 7, 15, 17, 20
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.utils.database import Base


class ConsentRecord(Base):
    """
    Track user consent for data processing.

    Supports GDPR Article 7 (Conditions for consent)
    """
    __tablename__ = "consent_records"

    id = Column(Integer, primary_key=True, index=True)

    # User information
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Consent details
    consent_type = Column(String(100), nullable=False, index=True)  # e.g., "terms_of_service", "privacy_policy", "marketing"
    purpose = Column(Text, nullable=False)  # Clear description of what data is used for

    # Consent status
    consented = Column(Boolean, nullable=False)
    consented_at = Column(DateTime, nullable=True)
    withdrawn_at = Column(DateTime, nullable=True)

    # Version tracking
    version = Column(String(20), nullable=False)  # Version of terms/policy

    # Evidence of consent
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    method = Column(String(50), nullable=False)  # "explicit_checkbox", "click_through", etc.

    # Additional context
    additional_metadata = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)

    # Relationships
    user = relationship("User", backref="consent_records")

    # Indexes
    __table_args__ = (
        Index('idx_consent_user_type', 'user_id', 'consent_type'),
        Index('idx_consent_status', 'user_id', 'consented'),
    )

    def withdraw(self):
        """Withdraw consent"""
        self.consented = False
        self.withdrawn_at = datetime.utcnow()

    def __repr__(self):
        return f"<ConsentRecord {self.id}: User {self.user_id} - {self.consent_type} ({'Consented' if self.consented else 'Withdrawn'})>"


class PrivacyPolicyVersion(Base):
    """
    Track versions of privacy policy and terms of service.

    Supports GDPR Article 13 (Information to be provided)
    """
    __tablename__ = "privacy_policy_versions"

    id = Column(Integer, primary_key=True, index=True)

    # Document details
    document_type = Column(String(50), nullable=False, index=True)  # "privacy_policy", "terms_of_service", "cookie_policy"
    version = Column(String(20), nullable=False, unique=True, index=True)
    title = Column(String(200), nullable=False)

    # Content
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)  # Brief summary of changes

    # Status
    is_active = Column(Boolean, default=False, nullable=False, index=True)

    # Timestamps
    effective_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_policy_type_active', 'document_type', 'is_active'),
    )

    def __repr__(self):
        return f"<PrivacyPolicyVersion {self.version}: {self.document_type}>"


class DataExportRequest(Base):
    """
    Track user data export requests.

    Supports GDPR Article 15 (Right of access) and Article 20 (Right to data portability)
    """
    __tablename__ = "data_export_requests"

    id = Column(Integer, primary_key=True, index=True)

    # User information
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Request details
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", index=True)  # PENDING, PROCESSING, COMPLETED, FAILED

    # Processing
    processing_started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Export details
    export_format = Column(String(20), nullable=False, default="JSON")  # JSON, CSV, PDF
    file_path = Column(String(500), nullable=True)  # Path to generated export file
    file_size_bytes = Column(Integer, nullable=True)
    download_count = Column(Integer, default=0, nullable=False)
    last_downloaded_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Export file expiration (30 days)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Relationships
    user = relationship("User", backref="data_export_requests")

    # Indexes
    __table_args__ = (
        Index('idx_export_user_status', 'user_id', 'status'),
    )

    def __repr__(self):
        return f"<DataExportRequest {self.id}: User {self.user_id} - {self.status}>"


class DataDeletionRequest(Base):
    """
    Track user data deletion requests (Right to be Forgotten).

    Supports GDPR Article 17 (Right to erasure)
    """
    __tablename__ = "data_deletion_requests"

    id = Column(Integer, primary_key=True, index=True)

    # User information (denormalized since user will be deleted)
    user_id = Column(Integer, nullable=False, index=True)  # No FK since user may be deleted
    username = Column(String(100), nullable=False)
    email = Column(String(200), nullable=False)

    # Request details
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", index=True)  # PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED

    # Processing
    processing_started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Deletion details
    deletion_scope = Column(String(50), nullable=False, default="FULL")  # FULL, ANONYMIZE
    reason = Column(Text, nullable=True)  # User's reason for deletion

    # What was deleted
    deleted_data = Column(JSON, nullable=True)  # Summary of deleted data

    # Retention period (if required by law to keep some data)
    retention_required = Column(Boolean, default=False, nullable=False)
    retention_reason = Column(Text, nullable=True)
    retention_until = Column(DateTime, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Audit trail
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who approved
    approved_at = Column(DateTime, nullable=True)

    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_deletion_user', 'user_id'),
        Index('idx_deletion_status', 'status'),
    )

    def __repr__(self):
        return f"<DataDeletionRequest {self.id}: User {self.user_id} - {self.status}>"


class DataProcessingActivity(Base):
    """
    Record of data processing activities (ROPA - Record of Processing Activities).

    Supports GDPR Article 30 (Records of processing activities)
    """
    __tablename__ = "data_processing_activities"

    id = Column(Integer, primary_key=True, index=True)

    # Activity identification
    activity_name = Column(String(200), nullable=False)
    activity_type = Column(String(100), nullable=False)  # "USER_AUTHENTICATION", "QUIZ_GRADING", etc.

    # Purpose
    purpose = Column(Text, nullable=False)
    legal_basis = Column(String(100), nullable=False)  # "CONSENT", "CONTRACT", "LEGITIMATE_INTEREST", etc.

    # Data categories
    data_categories = Column(JSON, nullable=False)  # ["personal_identifiers", "education_data", etc.]
    data_subjects = Column(JSON, nullable=False)  # ["students", "teachers", "admins"]

    # Recipients
    recipients = Column(JSON, nullable=True)  # Who receives the data
    third_country_transfers = Column(Boolean, default=False, nullable=False)
    safeguards = Column(Text, nullable=True)  # Safeguards for international transfers

    # Retention
    retention_period = Column(String(100), nullable=False)
    deletion_procedure = Column(Text, nullable=False)

    # Security measures
    security_measures = Column(JSON, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    last_reviewed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<DataProcessingActivity {self.id}: {self.activity_name}>"
