"""
ITR Form Type Detector

Automatically detects the correct ITR form type (ITR-1, ITR-2, ITR-3, ITR-4) based on:
- Income signals from Form 16, AIS, Form 26AS
- TDS section codes
- Additional eligibility indicators

Based on Income Tax Act rules for ITR form selection.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ITRFormType(Enum):
    """ITR Form Types"""
    ITR_1 = "ITR-1"
    ITR_2 = "ITR-2"
    ITR_3 = "ITR-3"
    ITR_4 = "ITR-4"


# TDS Section Code to Income Type Mapping
TDS_SECTION_MAPPING = {
    # Salary
    "192": "salary",
    "192A": "salary",  # Premature withdrawal from EPF
    
    # Interest Income
    "194A": "interest",
    "194DA": "insurance_maturity",
    "194EE": "nss_interest",
    
    # Professional/Contractor Income (Business Income indicators)
    "194J": "professional",
    "194JA": "professional_technical",
    "194JB": "professional_non_technical",
    "194C": "contractor",
    "194H": "commission",
    "194M": "contractor_individual",
    "194O": "ecommerce",
    
    # Dividend
    "194": "dividend",
    "194K": "mutual_fund_dividend",
    
    # Rent Income
    "194I": "rent",
    "194IA": "rent_immovable",
    "194IB": "rent_paid",
    
    # Property Sale (Capital Gains indicator)
    "194IA": "property_sale",
    
    # Crypto/Virtual Digital Assets
    "194S": "crypto",
    
    # Lottery/Winnings
    "194B": "lottery",
    "194BB": "horse_racing",
    
    # Foreign Income (NRI/Foreign)
    "195": "foreign_payment",
    "196A": "nri_income",
    "196B": "nri_units",
    "196C": "nri_bonds",
    "196D": "nri_securities",
    
    # Other
    "194D": "insurance_commission",
    "194G": "lottery_commission",
    "194N": "cash_withdrawal",
    "194P": "senior_citizen_pension",
    "194Q": "purchase_goods",
    "193": "interest_securities",
    "194LA": "compensation_acquisition",
    "194LB": "infrastructure_debt",
    "194LC": "foreign_currency_bonds",
}

# Sections indicating business/professional income
BUSINESS_INCOME_SECTIONS = {"194J", "194JA", "194JB", "194C", "194H", "194M", "194O"}


@dataclass
class IncomeSignals:
    """Income signals extracted from documents"""
    # Income Heads
    salary: float = 0.0
    house_property: float = 0.0
    capital_gains: float = 0.0
    capital_gains_short_term: float = 0.0
    capital_gains_long_term: float = 0.0
    capital_gains_ltcg_112a: float = 0.0  # LTCG under section 112A (equity)
    business_income: float = 0.0
    professional_income: float = 0.0
    other_sources: float = 0.0
    
    # Sub-components
    interest_income: float = 0.0
    dividend_income: float = 0.0
    rental_income: float = 0.0
    crypto_income: float = 0.0
    agricultural_income: float = 0.0
    
    # Total Income
    total_income: float = 0.0
    
    # Eligibility Indicators
    num_house_properties: int = 1
    has_foreign_assets: bool = False
    has_foreign_income: bool = False
    is_director_in_company: bool = False
    has_unlisted_equity: bool = False
    is_resident: bool = True
    
    # Business/Professional indicators
    has_presumptive_income_44ad: bool = False
    has_presumptive_income_44ada: bool = False
    has_presumptive_income_44ae: bool = False
    
    # TDS Section codes found
    tds_sections_found: List[str] = None
    
    def __post_init__(self):
        if self.tds_sections_found is None:
            self.tds_sections_found = []


@dataclass
class ITRDetectionResult:
    """Result of ITR form detection"""
    itr_form: str
    reason: str
    detected_income_heads: Dict[str, float]
    eligibility_indicators: Dict[str, Any]
    confidence: str = "high"
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            "itr_form": self.itr_form,
            "reason": self.reason,
            "detected_income_heads": self.detected_income_heads,
            "eligibility_indicators": self.eligibility_indicators,
            "confidence": self.confidence,
            "warnings": self.warnings
        }


class ITRFormDetector:
    """
    Intelligent ITR Form Detector
    
    Analyzes document data using deterministic logic based on the Income Tax Act
    to recommend the correct ITR form type.
    """
    
    # Income limit constants (from Income Tax rules)
    INCOME_LIMIT_ITR1_ITR4 = 5000000  # Rs. 50 Lakhs
    AGRICULTURAL_INCOME_LIMIT = 5000  # Rs. 5000 for ITR-1
    LTCG_112A_LIMIT = 125000  # Rs. 1,25,000 for ITR-1 (equity LTCG)
    
    def __init__(self):
        self.signals = IncomeSignals()
        self.warnings = []
    
    def detect_itr_form(
        self,
        aggregated_data: Dict[str, Any],
        user_data: Optional[Dict[str, Any]] = None
    ) -> ITRDetectionResult:
        """
        Main method to detect the appropriate ITR form
        
        Args:
            aggregated_data: Aggregated data from all documents
            user_data: Optional user profile data
        
        Returns:
            ITRDetectionResult with form type, reason, and details
        """
        # Step 1: Extract income signals from documents
        self._extract_income_signals(aggregated_data, user_data)
        
        # Step 2: Identify income types from TDS sections
        self._detect_income_from_tds_sections(aggregated_data)
        
        # Step 3: Apply ITR eligibility rules
        itr_form, reason = self._apply_eligibility_rules()
        
        # Step 4: Build result
        result = ITRDetectionResult(
            itr_form=itr_form,
            reason=reason,
            detected_income_heads={
                "salary": self.signals.salary,
                "house_property": self.signals.house_property,
                "capital_gains": self.signals.capital_gains,
                "business_income": self.signals.business_income + self.signals.professional_income,
                "other_sources": self.signals.other_sources
            },
            eligibility_indicators={
                "total_income": self.signals.total_income,
                "num_house_properties": self.signals.num_house_properties,
                "has_foreign_assets": self.signals.has_foreign_assets,
                "has_foreign_income": self.signals.has_foreign_income,
                "is_director_in_company": self.signals.is_director_in_company,
                "has_unlisted_equity": self.signals.has_unlisted_equity,
                "is_resident": self.signals.is_resident,
                "has_capital_gains": self.signals.capital_gains > 0,
                "has_business_income": (self.signals.business_income + self.signals.professional_income) > 0,
                "has_ltcg_112a_exceeding_limit": self.signals.capital_gains_ltcg_112a > self.LTCG_112A_LIMIT,
                "agricultural_income": self.signals.agricultural_income,
                "tds_sections_found": self.signals.tds_sections_found,
                "has_presumptive_income": (
                    self.signals.has_presumptive_income_44ad or 
                    self.signals.has_presumptive_income_44ada or 
                    self.signals.has_presumptive_income_44ae
                )
            },
            confidence=self._calculate_confidence(),
            warnings=self.warnings
        )
        
        return result
    
    def _extract_income_signals(
        self, 
        aggregated_data: Dict[str, Any],
        user_data: Optional[Dict[str, Any]] = None
    ):
        """
        Extract income signals from aggregated document data
        
        From Form 16: Salary, Perquisites, Allowances, TDS u/s 192
        From AIS: Interest, Dividend, Capital Gains, Crypto, Foreign Income
        From Form 26AS: TDS section codes to detect income types
        """
        # === SALARY INCOME ===
        self.signals.salary = max(
            self._safe_float(aggregated_data.get("salary_income", 0)),
            self._safe_float(aggregated_data.get("gross_salary", 0)),
            self._safe_float(aggregated_data.get("net_salary", 0))
        )
        
        # === HOUSE PROPERTY INCOME ===
        self.signals.house_property = self._safe_float(
            aggregated_data.get("house_property_income", 0)
        )
        
        # Number of house properties (check metadata if available)
        self.signals.num_house_properties = aggregated_data.get("num_house_properties", 1)
        if aggregated_data.get("multiple_house_properties", False):
            self.signals.num_house_properties = max(2, self.signals.num_house_properties)
        
        # === CAPITAL GAINS ===
        self.signals.capital_gains_short_term = self._safe_float(
            aggregated_data.get("capital_gains_short_term", 0)
        )
        self.signals.capital_gains_long_term = self._safe_float(
            aggregated_data.get("capital_gains_long_term", 0)
        )
        self.signals.capital_gains_ltcg_112a = self._safe_float(
            aggregated_data.get("capital_gains_ltcg_112a", 0)
        )
        
        # LTCG 112A is a part of long-term capital gains
        # If LTCG 112A is provided but LTCG is not, use LTCG 112A as LTCG
        if self.signals.capital_gains_ltcg_112a > 0 and self.signals.capital_gains_long_term == 0:
            self.signals.capital_gains_long_term = self.signals.capital_gains_ltcg_112a
        
        # Calculate total capital gains
        self.signals.capital_gains = max(
            self.signals.capital_gains_short_term + 
            self.signals.capital_gains_long_term +
            self._safe_float(aggregated_data.get("capital_gains", 0)),
            self.signals.capital_gains_ltcg_112a  # Ensure LTCG 112A is counted
        )
        
        # Crypto income (treated as capital gains or VDA income)
        self.signals.crypto_income = self._safe_float(
            aggregated_data.get("crypto_income", 0)
        )
        if self.signals.crypto_income > 0:
            self.signals.capital_gains += self.signals.crypto_income
        
        # === BUSINESS/PROFESSIONAL INCOME ===
        self.signals.business_income = self._safe_float(
            aggregated_data.get("business_income", 0)
        )
        self.signals.professional_income = self._safe_float(
            aggregated_data.get("professional_income", 0)
        )
        
        # Presumptive taxation indicators
        self.signals.has_presumptive_income_44ad = aggregated_data.get(
            "has_presumptive_income_44ad", False
        )
        self.signals.has_presumptive_income_44ada = aggregated_data.get(
            "has_presumptive_income_44ada", False
        )
        self.signals.has_presumptive_income_44ae = aggregated_data.get(
            "has_presumptive_income_44ae", False
        )
        
        # === OTHER INCOME SOURCES ===
        self.signals.interest_income = self._safe_float(
            aggregated_data.get("interest_income", 0)
        )
        self.signals.dividend_income = self._safe_float(
            aggregated_data.get("dividend_income", 0)
        )
        self.signals.rental_income = self._safe_float(
            aggregated_data.get("rental_income", 0)
        )
        self.signals.other_sources = (
            self.signals.interest_income +
            self.signals.dividend_income +
            self._safe_float(aggregated_data.get("other_income", 0))
        )
        
        # === AGRICULTURAL INCOME ===
        self.signals.agricultural_income = self._safe_float(
            aggregated_data.get("agricultural_income", 0)
        )
        
        # === ELIGIBILITY INDICATORS ===
        # Foreign assets/income
        self.signals.has_foreign_assets = aggregated_data.get("has_foreign_assets", False)
        self.signals.has_foreign_income = aggregated_data.get("has_foreign_income", False)
        
        # Director status
        self.signals.is_director_in_company = aggregated_data.get(
            "is_director_in_company", False
        )
        
        # Unlisted equity
        self.signals.has_unlisted_equity = aggregated_data.get("has_unlisted_equity", False)
        
        # Residency status (default to resident)
        self.signals.is_resident = aggregated_data.get("is_resident", True)
        if user_data:
            self.signals.is_resident = user_data.get("is_resident", True)
        
        # === TOTAL INCOME ===
        self.signals.total_income = max(
            self._safe_float(aggregated_data.get("gross_total_income", 0)),
            self.signals.salary + 
            abs(self.signals.house_property) +  # House property can be negative (loss)
            self.signals.capital_gains +
            self.signals.business_income +
            self.signals.professional_income +
            self.signals.other_sources
        )
    
    def _detect_income_from_tds_sections(self, aggregated_data: Dict[str, Any]):
        """
        Detect income types from TDS section codes in Form 26AS
        
        Uses TDS section codes to identify income types:
        - 192 → Salary
        - 194A → Interest income
        - 194J → Professional income
        - 194C → Contractor income
        - 194H → Commission income
        - 194IA → Property sale
        - 194S → Crypto transactions
        """
        # Get TDS details from aggregated data
        tds_details = aggregated_data.get("tds_details", {})
        tds_sections = aggregated_data.get("tds_sections", [])
        
        # Also check raw TDS section data
        if isinstance(tds_details, dict):
            for section, amount in tds_details.items():
                section_code = str(section).upper().replace("SECTION_", "").replace("SEC_", "")
                # Extract just the number if it contains text
                import re
                match = re.search(r'(\d+[A-Z]*)', section_code)
                if match:
                    section_code = match.group(1)
                    if section_code not in self.signals.tds_sections_found:
                        self.signals.tds_sections_found.append(section_code)
                    
                    # Map section to income type and update signals
                    self._process_tds_section(section_code, self._safe_float(amount))
        
        # Process explicit TDS sections list
        if isinstance(tds_sections, list):
            for section in tds_sections:
                section_code = str(section).upper()
                if section_code not in self.signals.tds_sections_found:
                    self.signals.tds_sections_found.append(section_code)
        
        # Check for business income indicators from TDS sections
        business_sections_found = set(self.signals.tds_sections_found) & BUSINESS_INCOME_SECTIONS
        if business_sections_found and self.signals.business_income == 0:
            # TDS sections indicate business/professional income
            self.signals.business_income = max(
                self.signals.business_income,
                self.signals.professional_income,
                1  # Flag that business income exists even if amount unknown
            )
            self.warnings.append(
                f"Business/Professional income detected from TDS sections: {business_sections_found}"
            )
    
    def _process_tds_section(self, section_code: str, amount: float):
        """Process a TDS section code and update income signals"""
        income_type = TDS_SECTION_MAPPING.get(section_code, "unknown")
        
        if income_type == "salary":
            # Already captured from Form 16
            pass
        elif income_type in ["professional", "professional_technical", "professional_non_technical"]:
            self.signals.professional_income = max(self.signals.professional_income, amount / 0.1)  # Estimate gross (assuming 10% TDS)
        elif income_type in ["contractor", "commission", "contractor_individual", "ecommerce"]:
            # These indicate business income
            estimated_income = amount / 0.01  # Contractor TDS is typically 1-2%
            self.signals.business_income = max(self.signals.business_income, estimated_income)
        elif income_type == "interest":
            self.signals.interest_income = max(self.signals.interest_income, amount / 0.1)
        elif income_type in ["dividend", "mutual_fund_dividend"]:
            self.signals.dividend_income = max(self.signals.dividend_income, amount / 0.1)
        elif income_type == "property_sale":
            # Property sale indicates capital gains
            self.signals.capital_gains = max(self.signals.capital_gains, 1)
        elif income_type == "crypto":
            self.signals.crypto_income = max(self.signals.crypto_income, amount / 0.01)  # 1% TDS on crypto
            self.signals.capital_gains += self.signals.crypto_income
        elif income_type in ["foreign_payment", "nri_income", "nri_units", "nri_bonds", "nri_securities"]:
            self.signals.has_foreign_income = True
    
    def _apply_eligibility_rules(self) -> Tuple[str, str]:
        """
        Apply ITR eligibility rules to determine the correct form
        
        Order of evaluation (higher complexity first):
        1. ITR-3: Business/Professional income
        2. ITR-4: Presumptive taxation (44AD/44ADA/44AE)
        3. ITR-2: Capital gains, multiple properties, foreign assets, etc.
        4. ITR-1: Simple salary/pension + one house property + other sources
        """
        reasons = []
        
        # === CHECK ITR-3 FIRST (Business/Professional Income) ===
        if self._is_itr3_applicable():
            return self._build_itr3_result()
        
        # === CHECK ITR-4 (Presumptive Taxation) ===
        if self._is_itr4_applicable():
            return self._build_itr4_result()
        
        # === CHECK ITR-2 (Complex cases without business income) ===
        if self._is_itr2_applicable():
            return self._build_itr2_result()
        
        # === DEFAULT: ITR-1 (Simple cases) ===
        if self._is_itr1_applicable():
            return self._build_itr1_result()
        
        # === FALLBACK: ITR-2 if ITR-1 not applicable ===
        return self._build_itr2_fallback_result()
    
    def _is_itr3_applicable(self) -> bool:
        """
        Check if ITR-3 is applicable
        
        ITR-3 Required when:
        - Income from business or profession exists
        - TDS sections 194J, 194C, 194H indicate business/professional income
        """
        # Check for business/professional income
        if self.signals.business_income > 0 or self.signals.professional_income > 0:
            return True
        
        # Check TDS sections that indicate business income
        business_sections = set(self.signals.tds_sections_found) & BUSINESS_INCOME_SECTIONS
        if business_sections:
            return True
        
        return False
    
    def _is_itr4_applicable(self) -> bool:
        """
        Check if ITR-4 (Sugam) is applicable
        
        ITR-4 Required when:
        - Income from presumptive taxation (44AD/44ADA/44AE)
        - Resident individual
        - Total income ≤ Rs. 50 Lakhs
        - No capital gains (except permitted cases)
        """
        has_presumptive = (
            self.signals.has_presumptive_income_44ad or
            self.signals.has_presumptive_income_44ada or
            self.signals.has_presumptive_income_44ae
        )
        
        if not has_presumptive:
            return False
        
        # Must be resident
        if not self.signals.is_resident:
            return False
        
        # Total income must be ≤ 50 Lakhs
        if self.signals.total_income > self.INCOME_LIMIT_ITR1_ITR4:
            return False
        
        # No capital gains (other than permitted)
        if self.signals.capital_gains > 0:
            # ITR-4 doesn't allow capital gains in most cases
            return False
        
        return True
    
    def _is_itr2_applicable(self) -> bool:
        """
        Check if ITR-2 is applicable
        
        ITR-2 Required when NO business income AND any of:
        - Capital gains exist
        - Multiple house properties
        - Foreign assets or foreign income
        - Total income > Rs. 50 Lakhs
        - Director in company
        - Unlisted equity shares held
        - LTCG u/s 112A > Rs. 1,25,000
        """
        # Don't suggest ITR-2 if business income exists (that's ITR-3)
        if self.signals.business_income > 0 or self.signals.professional_income > 0:
            return False
        
        # Check disqualifying conditions for ITR-1
        if self.signals.capital_gains > 0:
            # For ITR-1, only LTCG 112A up to 1.25L is allowed
            if self.signals.capital_gains_ltcg_112a > self.LTCG_112A_LIMIT:
                return True
            # Any STCG or other LTCG requires ITR-2
            if self.signals.capital_gains_short_term > 0:
                return True
            # Non-112A LTCG requires ITR-2
            if self.signals.capital_gains_long_term > self.signals.capital_gains_ltcg_112a:
                return True
        
        if self.signals.num_house_properties > 1:
            return True
        
        if self.signals.has_foreign_assets or self.signals.has_foreign_income:
            return True
        
        if self.signals.total_income > self.INCOME_LIMIT_ITR1_ITR4:
            return True
        
        if self.signals.is_director_in_company:
            return True
        
        if self.signals.has_unlisted_equity:
            return True
        
        if self.signals.crypto_income > 0:
            return True
        
        return False
    
    def _is_itr1_applicable(self) -> bool:
        """
        Check if ITR-1 (Sahaj) is applicable
        
        ITR-1 Only when ALL conditions are satisfied:
        - Individual is Resident
        - Total income ≤ Rs. 50,00,000
        - Income sources limited to:
          - Salary
          - One house property
          - Other sources (interest etc.)
          - LTCG u/s 112A ≤ Rs. 1,25,000
        - Agricultural income ≤ Rs. 5,000
        - No business or professional income
        - No foreign assets
        - Not a director in company
        - No unlisted equity shares
        """
        # Must be resident
        if not self.signals.is_resident:
            self.warnings.append("ITR-1 not applicable: Non-resident individual")
            return False
        
        # Total income limit
        if self.signals.total_income > self.INCOME_LIMIT_ITR1_ITR4:
            self.warnings.append(
                f"ITR-1 not applicable: Total income Rs.{self.signals.total_income:,.0f} "
                f"exceeds Rs.50,00,000 limit"
            )
            return False
        
        # No business/professional income
        if self.signals.business_income > 0 or self.signals.professional_income > 0:
            return False
        
        # Check capital gains limits for ITR-1
        if self.signals.capital_gains > 0:
            # Only LTCG 112A up to 1.25L allowed in ITR-1
            if self.signals.capital_gains_short_term > 0:
                return False
            if self.signals.capital_gains_ltcg_112a > self.LTCG_112A_LIMIT:
                return False
            # Other types of capital gains not allowed
            other_cg = self.signals.capital_gains - self.signals.capital_gains_ltcg_112a
            if other_cg > 0:
                return False
        
        # Only one house property
        if self.signals.num_house_properties > 1:
            return False
        
        # Agricultural income limit
        if self.signals.agricultural_income > self.AGRICULTURAL_INCOME_LIMIT:
            return False
        
        # No foreign assets/income
        if self.signals.has_foreign_assets or self.signals.has_foreign_income:
            return False
        
        # Not a director
        if self.signals.is_director_in_company:
            return False
        
        # No unlisted equity
        if self.signals.has_unlisted_equity:
            return False
        
        # No crypto income
        if self.signals.crypto_income > 0:
            return False
        
        return True
    
    def _build_itr1_result(self) -> Tuple[str, str]:
        """Build ITR-1 recommendation result"""
        reasons = [
            "ITR-1 (Sahaj) is applicable because:",
            "- You are a Resident Individual",
            f"- Total income Rs.{self.signals.total_income:,.0f} is within Rs.50,00,000 limit",
            "- Income is from allowed sources: Salary, One House Property, Other Sources",
        ]
        
        if self.signals.salary > 0:
            reasons.append(f"- Salary income: Rs.{self.signals.salary:,.0f}")
        
        if self.signals.house_property != 0:
            reasons.append(f"- House property income/loss: Rs.{self.signals.house_property:,.0f}")
        
        if self.signals.other_sources > 0:
            reasons.append(f"- Other sources income: Rs.{self.signals.other_sources:,.0f}")
        
        if self.signals.capital_gains_ltcg_112a > 0 and self.signals.capital_gains_ltcg_112a <= self.LTCG_112A_LIMIT:
            reasons.append(f"- LTCG u/s 112A: Rs.{self.signals.capital_gains_ltcg_112a:,.0f} (within Rs.1,25,000 limit)")
        
        reasons.extend([
            "- No business/professional income",
            "- No foreign assets or income",
            "- Not a director in any company",
            "- No unlisted equity shares"
        ])
        
        return ITRFormType.ITR_1.value, "\n".join(reasons)
    
    def _build_itr2_result(self) -> Tuple[str, str]:
        """Build ITR-2 recommendation result"""
        reasons = ["ITR-2 is applicable because:"]
        
        if self.signals.capital_gains > 0:
            reasons.append(f"- Capital gains exist: Rs.{self.signals.capital_gains:,.0f}")
            if self.signals.capital_gains_short_term > 0:
                reasons.append(f"  - Short-term capital gains: Rs.{self.signals.capital_gains_short_term:,.0f}")
            if self.signals.capital_gains_long_term > 0:
                reasons.append(f"  - Long-term capital gains: Rs.{self.signals.capital_gains_long_term:,.0f}")
            if self.signals.crypto_income > 0:
                reasons.append(f"  - Virtual Digital Assets (Crypto): Rs.{self.signals.crypto_income:,.0f}")
        
        if self.signals.num_house_properties > 1:
            reasons.append(f"- Multiple house properties: {self.signals.num_house_properties}")
        
        if self.signals.has_foreign_assets:
            reasons.append("- Foreign assets are held")
        
        if self.signals.has_foreign_income:
            reasons.append("- Foreign income exists")
        
        if self.signals.total_income > self.INCOME_LIMIT_ITR1_ITR4:
            reasons.append(f"- Total income Rs.{self.signals.total_income:,.0f} exceeds Rs.50,00,000")
        
        if self.signals.is_director_in_company:
            reasons.append("- Director in a company")
        
        if self.signals.has_unlisted_equity:
            reasons.append("- Holds unlisted equity shares")
        
        reasons.append("- No business or professional income")
        
        return ITRFormType.ITR_2.value, "\n".join(reasons)
    
    def _build_itr2_fallback_result(self) -> Tuple[str, str]:
        """Build ITR-2 fallback result when ITR-1 is not applicable"""
        reasons = [
            "ITR-2 is recommended because ITR-1 is not applicable:",
        ]
        
        if not self.signals.is_resident:
            reasons.append("- Non-resident individual (ITR-1 requires resident status)")
        
        if self.signals.agricultural_income > self.AGRICULTURAL_INCOME_LIMIT:
            reasons.append(f"- Agricultural income Rs.{self.signals.agricultural_income:,.0f} exceeds Rs.5,000 limit")
        
        reasons.append("- ITR-2 accommodates individual/HUF income without business income")
        
        return ITRFormType.ITR_2.value, "\n".join(reasons)
    
    def _build_itr3_result(self) -> Tuple[str, str]:
        """Build ITR-3 recommendation result"""
        reasons = ["ITR-3 is applicable because:"]
        
        if self.signals.business_income > 0:
            reasons.append(f"- Business income exists: Rs.{self.signals.business_income:,.0f}")
        
        if self.signals.professional_income > 0:
            reasons.append(f"- Professional income exists: Rs.{self.signals.professional_income:,.0f}")
        
        # Check TDS sections
        business_sections = set(self.signals.tds_sections_found) & BUSINESS_INCOME_SECTIONS
        if business_sections:
            reasons.append(f"- TDS sections indicating business/professional income: {sorted(business_sections)}")
            section_types = []
            for sec in business_sections:
                if sec in ["194J", "194JA", "194JB"]:
                    section_types.append("Professional services (194J)")
                elif sec == "194C":
                    section_types.append("Contractor payments (194C)")
                elif sec == "194H":
                    section_types.append("Commission income (194H)")
            if section_types:
                reasons.append(f"  - Detected income types: {', '.join(section_types)}")
        
        reasons.append("- ITR-3 is required for individuals with business or professional income")
        
        return ITRFormType.ITR_3.value, "\n".join(reasons)
    
    def _build_itr4_result(self) -> Tuple[str, str]:
        """Build ITR-4 recommendation result"""
        reasons = ["ITR-4 (Sugam) is applicable because:"]
        
        if self.signals.has_presumptive_income_44ad:
            reasons.append("- Presumptive income under Section 44AD (business)")
        
        if self.signals.has_presumptive_income_44ada:
            reasons.append("- Presumptive income under Section 44ADA (professionals)")
        
        if self.signals.has_presumptive_income_44ae:
            reasons.append("- Presumptive income under Section 44AE (goods carriage)")
        
        reasons.extend([
            "- Resident individual",
            f"- Total income Rs.{self.signals.total_income:,.0f} is within Rs.50,00,000 limit",
            "- No capital gains (other than permitted cases)"
        ])
        
        return ITRFormType.ITR_4.value, "\n".join(reasons)
    
    def _calculate_confidence(self) -> str:
        """Calculate confidence level of the detection"""
        # High confidence if we have salary data and clear indicators
        if self.signals.salary > 0:
            if len(self.warnings) == 0:
                return "high"
            elif len(self.warnings) <= 2:
                return "medium"
        
        # Medium confidence if we have some data
        if self.signals.total_income > 0:
            return "medium"
        
        # Low confidence if limited data
        return "low"
    
    @staticmethod
    def _safe_float(value: Any) -> float:
        """Safely convert value to float"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                # Remove common formatting
                cleaned = value.replace(",", "").replace("Rs.", "").replace("₹", "").strip()
                return float(cleaned)
            except ValueError:
                return 0.0
        return 0.0


def detect_itr_form(
    aggregated_data: Dict[str, Any],
    user_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to detect ITR form type
    
    Args:
        aggregated_data: Aggregated data from all documents
        user_data: Optional user profile data
    
    Returns:
        Dictionary with itr_form, reason, detected_income_heads, etc.
    """
    detector = ITRFormDetector()
    result = detector.detect_itr_form(aggregated_data, user_data)
    return result.to_dict()
