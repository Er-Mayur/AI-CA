from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from models import Gender, DocType, VerificationStatus

# User schemas
class UserCreate(BaseModel):
    name: str
    pan_card: str
    email: EmailStr
    gender: Gender
    date_of_birth: date
    password: str
    confirm_password: str
    
    @validator('pan_card')
    def validate_pan(cls, v):
        v = v.upper().strip()
        if len(v) != 10:
            raise ValueError('PAN card must be 10 characters')
        if not v[:5].isalpha() or not v[5:9].isdigit() or not v[9].isalpha():
            raise ValueError('Invalid PAN card format')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class UserLogin(BaseModel):
    identifier: str  # Can be PAN or email
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    pan_card: str
    email: str
    gender: Gender
    date_of_birth: date
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Document schemas
class DocumentUpload(BaseModel):
    financial_year: str
    doc_type: DocType

class DocumentResponse(BaseModel):
    id: int
    user_id: int
    financial_year: str
    doc_type: DocType
    file_path: str
    verification_status: VerificationStatus
    verification_message: Optional[str]
    extracted_data: Optional[Dict[str, Any]]
    uploaded_at: datetime
    verified_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Tax computation schemas
class TaxComputationResponse(BaseModel):
    id: int
    user_id: int
    financial_year: str
    assessment_year: str
    gross_total_income: float
    old_regime_total_tax: float
    new_regime_total_tax: float
    recommended_regime: Optional[str]
    recommendation_reason: Optional[str]
    recommended_itr_form: Optional[str]
    tax_savings: float
    total_tds: float
    tax_payable: float
    refund_amount: float
    computed_at: datetime
    
    class Config:
        from_attributes = True

class TaxComputationDetail(BaseModel):
    id: int
    financial_year: str
    assessment_year: str
    
    # Income breakdown
    gross_total_income: float
    salary_income: float
    house_property_income: float
    capital_gains: float
    other_income: float
    
    # Old regime details
    old_regime_deductions: Optional[Dict[str, Any]]
    old_regime_total_deductions: float
    old_regime_taxable_income: float
    old_regime_tax_before_rebate: float
    old_regime_rebate: float
    old_regime_tax_after_rebate: float
    old_regime_surcharge: float
    old_regime_cess: float
    old_regime_total_tax: float
    
    # New regime details
    new_regime_deductions: Optional[Dict[str, Any]]
    new_regime_total_deductions: float
    new_regime_taxable_income: float
    new_regime_tax_before_rebate: float
    new_regime_rebate: float
    new_regime_tax_after_rebate: float
    new_regime_surcharge: float
    new_regime_cess: float
    new_regime_total_tax: float
    
    # Recommendation
    recommended_regime: Optional[str]
    recommendation_reason: Optional[str]
    recommended_itr_form: Optional[str]
    tax_savings: float
    
    # TDS and final tax
    total_tds: float
    tax_payable: float
    refund_amount: float
    
    computed_at: datetime
    
    class Config:
        from_attributes = True

# Dashboard schemas
class DashboardStats(BaseModel):
    financial_year: str
    documents_uploaded: int
    documents_verified: int
    tax_computed: bool
    gross_income: float
    total_tax: float
    tds_deducted: float
    net_payable_refund: float
    recommended_regime: Optional[str]

class ActivityHistoryResponse(BaseModel):
    id: int
    activity_type: str
    description: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

# Investment schemas
class InvestmentSuggestionResponse(BaseModel):
    id: int
    financial_year: str
    suggestions: List[Dict[str, Any]]
    potential_savings: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# Q&A schemas
class QuestionRequest(BaseModel):
    question: str
    conversation_id: Optional[int] = None
    financial_year: Optional[str] = None

class QuestionResponse(BaseModel):
    question: str
    answer: str
    conversation_id: int
    sources: Optional[List[str]] = None

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[MessageResponse]] = None
    
    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Chat"

