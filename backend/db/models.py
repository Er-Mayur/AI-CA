# backend/db/models.py

from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.database import Base  # corrected import path

# --------------------------------------------------------------------
# 1️⃣ User Table
# --------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    pan_number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Required profile details
    date_of_birth: Mapped[datetime] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    employment_type: Mapped[str] = mapped_column(String(30), nullable=False)
    residential_status: Mapped[str] = mapped_column(String(30), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    documents: Mapped[list["Document"]] = relationship(back_populates="user", cascade="all, delete")
    summaries: Mapped[list["TaxSummary"]] = relationship(back_populates="user", cascade="all, delete")
    deductions: Mapped[list["Deduction"]] = relationship(back_populates="user", cascade="all, delete")
    history: Mapped[list["DocumentHistory"]] = relationship(back_populates="user", cascade="all, delete")



# --------------------------------------------------------------------
# 2️ Document Table
# --------------------------------------------------------------------
class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    doc_type: Mapped[str] = mapped_column(String(20))  # form16 | form26as | ais
    fy: Mapped[str] = mapped_column(String(9), default="2024-25")
    file_path: Mapped[str] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Parsed financial data (e.g., JSON summary)
    parsed_json: Mapped[str] = mapped_column(Text, default="{}")

    #  AI verification metadata
    verification_json: Mapped[str] = mapped_column(Text, default="{}")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="documents")




# --------------------------------------------------------------------
# 3️ Tax Summary Table
# --------------------------------------------------------------------
class TaxSummary(Base):
    __tablename__ = "tax_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    fy: Mapped[str] = mapped_column(String(9))  # 2024-25
    ay: Mapped[str] = mapped_column(String(9))  # 2025-26

    # Income heads
    total_salary: Mapped[float] = mapped_column(Float, default=0.0)
    house_property_income: Mapped[float] = mapped_column(Float, default=0.0)
    capital_gains: Mapped[float] = mapped_column(Float, default=0.0)
    interest_income: Mapped[float] = mapped_column(Float, default=0.0)
    dividend_income: Mapped[float] = mapped_column(Float, default=0.0)
    other_income: Mapped[float] = mapped_column(Float, default=0.0)
    total_income: Mapped[float] = mapped_column(Float, default=0.0)

    # Deductions
    deduction_80c: Mapped[float] = mapped_column(Float, default=0.0)
    deduction_80d: Mapped[float] = mapped_column(Float, default=0.0)
    deduction_80ccd: Mapped[float] = mapped_column(Float, default=0.0)
    deduction_hra: Mapped[float] = mapped_column(Float, default=0.0)
    total_deductions: Mapped[float] = mapped_column(Float, default=0.0)

    # Tax computation
    tds_total: Mapped[float] = mapped_column(Float, default=0.0)
    tax_old: Mapped[float] = mapped_column(Float, default=0.0)
    tax_new: Mapped[float] = mapped_column(Float, default=0.0)
    best_regime: Mapped[str] = mapped_column(String(10), default="new")
    refund_or_payable: Mapped[float] = mapped_column(Float, default=0.0)

    # 🔹 For graph analytics
    investment_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    tax_saving_percent: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="summaries")

# --------------------------------------------------------------------
# 4 Deduction Table
# --------------------------------------------------------------------
class Deduction(Base):
    __tablename__ = "deductions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    fy: Mapped[str] = mapped_column(String(9))
    section: Mapped[str] = mapped_column(String(10))   # e.g., 80C, 80D, 80TTA, 24(b)
    description: Mapped[str] = mapped_column(String(100))
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    suggested: Mapped[bool] = mapped_column(default=False)  # True if system-recommended

    # Add these verification fields here
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_json: Mapped[str] = mapped_column(Text, default="{}")

    user: Mapped["User"] = relationship(back_populates="deductions")

# --------------------------------------------------------------------
# 5 Document History Table (for audit logs)
# --------------------------------------------------------------------
class DocumentHistory(Base):
    __tablename__ = "document_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    fy: Mapped[str] = mapped_column(String(9))
    doc_type: Mapped[str] = mapped_column(String(20))
    old_file_path: Mapped[str] = mapped_column(Text, nullable=True)
    new_file_path: Mapped[str] = mapped_column(Text, nullable=True)
    action: Mapped[str] = mapped_column(String(20))  # uploaded / replaced / deleted
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="history")


