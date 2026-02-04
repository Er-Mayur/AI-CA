from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
import enum

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class DocType(str, enum.Enum):
    FORM_16 = "Form 16"
    FORM_26AS = "Form 26AS"
    AIS = "AIS"

class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    pan_card = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    tax_computations = relationship("TaxComputation", back_populates="user", cascade="all, delete-orphan")
    activities = relationship("ActivityHistory", back_populates="user", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    financial_year = Column(String(20), nullable=False)  # e.g., "2024-25"
    doc_type = Column(Enum(DocType), nullable=False)
    file_path = Column(String(500), nullable=False)
    verification_status = Column(Enum(VerificationStatus), default=VerificationStatus.PENDING)
    verification_message = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=True)  # Store extracted data as JSON
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="documents")

class TaxComputation(Base):
    __tablename__ = "tax_computations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    financial_year = Column(String(20), nullable=False)
    assessment_year = Column(String(20), nullable=False)
    
    # Income details
    gross_total_income = Column(Float, default=0.0)
    salary_income = Column(Float, default=0.0)
    house_property_income = Column(Float, default=0.0)
    capital_gains = Column(Float, default=0.0)
    other_income = Column(Float, default=0.0)
    
    # Old regime
    old_regime_deductions = Column(JSON, nullable=True)
    old_regime_total_deductions = Column(Float, default=0.0)
    old_regime_taxable_income = Column(Float, default=0.0)
    old_regime_tax_before_rebate = Column(Float, default=0.0)
    old_regime_rebate = Column(Float, default=0.0)
    old_regime_tax_after_rebate = Column(Float, default=0.0)
    old_regime_surcharge = Column(Float, default=0.0)
    old_regime_cess = Column(Float, default=0.0)
    old_regime_total_tax = Column(Float, default=0.0)
    
    # New regime
    new_regime_deductions = Column(JSON, nullable=True)
    new_regime_total_deductions = Column(Float, default=0.0)
    new_regime_taxable_income = Column(Float, default=0.0)
    new_regime_tax_before_rebate = Column(Float, default=0.0)
    new_regime_rebate = Column(Float, default=0.0)
    new_regime_tax_after_rebate = Column(Float, default=0.0)
    new_regime_surcharge = Column(Float, default=0.0)
    new_regime_cess = Column(Float, default=0.0)
    new_regime_total_tax = Column(Float, default=0.0)
    
    # Recommendation
    recommended_regime = Column(String(50), nullable=True)
    recommendation_reason = Column(Text, nullable=True)
    recommended_itr_form = Column(String(50), nullable=True)
    tax_savings = Column(Float, default=0.0)
    
    # TDS and final tax
    total_tds = Column(Float, default=0.0)
    tax_payable = Column(Float, default=0.0)
    refund_amount = Column(Float, default=0.0)
    
    computed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tax_computations")

class ActivityHistory(Base):
    __tablename__ = "activity_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    financial_year = Column(String(20), nullable=False)
    activity_type = Column(String(100), nullable=False)  # e.g., "DOCUMENT_UPLOAD", "TAX_CALCULATION", etc.
    description = Column(Text, nullable=False)
    activity_metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="activities")

class TaxRule(Base):
    __tablename__ = "tax_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    financial_year = Column(String(20), unique=True, nullable=False)
    assessment_year = Column(String(20), nullable=False)
    rules_json = Column(JSON, nullable=False)  # Complete tax rules as JSON
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class InvestmentSuggestion(Base):
    __tablename__ = "investment_suggestions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    financial_year = Column(String(20), nullable=False)
    suggestions = Column(JSON, nullable=False)  # Array of suggestions
    potential_savings = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False, default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(50), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

