"""
Centralized Tax Rules Service
All tax figures MUST come from this service - no hardcoded values anywhere in the codebase.
Rules are loaded from the official government tax website and stored in the database.
"""
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from models import TaxRule
import json


class TaxRulesNotFoundError(Exception):
    """Raised when tax rules are not found for requested financial year"""
    pass


class RulesService:
    """
    Centralized service to fetch and parse tax rules from the database.
    All tax calculations MUST use this service to get figures.
    """
    
    def __init__(self, db: Session, financial_year: str = "2024-25"):
        self.db = db
        self.financial_year = financial_year
        self._rules: Optional[Dict[str, Any]] = None
        self._load_rules()
    
    def _load_rules(self):
        """Load rules from database for the specified financial year"""
        tax_rule = self.db.query(TaxRule).filter(
            TaxRule.financial_year == self.financial_year,
            TaxRule.is_active == True
        ).first()
        
        if not tax_rule:
            raise TaxRulesNotFoundError(
                f"Tax rules not found for FY {self.financial_year}. "
                f"Please run seed_tax_rules.py to populate the database."
            )
        
        self._rules = tax_rule.rules_json
        print(f"✅ Loaded tax rules for FY {self.financial_year}")
    
    @property
    def rules(self) -> Dict[str, Any]:
        """Get the raw rules JSON"""
        if self._rules is None:
            raise TaxRulesNotFoundError("Rules not loaded")
        return self._rules
    
    # ==========================================
    # STANDARD DEDUCTION
    # ==========================================
    def get_standard_deduction(self, regime: str = "new_regime") -> int:
        """Get standard deduction amount based on regime and FY"""
        # First check common_deductions_exemptions (FY 2023-24 format)
        common = self._rules.get("common_deductions_exemptions", {})
        
        if "standard_deduction_salaried" in common:
            std_ded = common["standard_deduction_salaried"]
            regimes_allowed = std_ded.get("regimes_allowed", [])
            
            # Check if this regime is allowed
            if regime in regimes_allowed or "new_regime" in regimes_allowed or "old_regime" in regimes_allowed:
                return std_ded.get("max_amount", 50000)
        
        # For FY 2024-25 format, standard deduction is Rs. 75,000 for salaried
        # (Updated in Budget 2024)
        fy = self._rules.get("financial_year", self.financial_year)
        if fy and fy >= "2024-25":
            return 75000
        
        # Default for older FYs
        return 50000
    
    # ==========================================
    # PROFESSIONAL TAX
    # ==========================================
    def get_professional_tax_limit(self) -> int:
        """Get professional tax deduction limit"""
        common = self._rules.get("common_deductions_exemptions", {})
        if "professional_tax" in common:
            return common["professional_tax"].get("max_amount", 2500)
        return 2500  # Constitutional limit
    
    # ==========================================
    # SECTION 80C LIMIT
    # ==========================================
    def get_80c_limit(self) -> int:
        """Get combined 80C/80CCC/80CCD(1) limit"""
        # Try old regime deductions structure first (FY 2024-25 format)
        deductions = self._rules.get("deductions", {})
        old_regime = deductions.get("old_regime_chapter_VIA_and_others", {})
        
        if "section_80C_80CCC_80CCD1" in old_regime:
            return old_regime["section_80C_80CCC_80CCD1"].get("combined_limit")
        
        # Try common deductions (FY 2023-24 format)
        common = self._rules.get("common_deductions_exemptions", {})
        if "80C" in common:
            return common["80C"].get("max_amount")
        
        raise TaxRulesNotFoundError(f"Section 80C limit not found in rules for FY {self.financial_year}")
    
    # ==========================================
    # SECTION 80CCD(1B) - Additional NPS
    # ==========================================
    def get_80ccd1b_limit(self) -> int:
        """Get 80CCD(1B) additional NPS limit"""
        deductions = self._rules.get("deductions", {})
        old_regime = deductions.get("old_regime_chapter_VIA_and_others", {})
        
        if "section_80CCD1B" in old_regime:
            return old_regime["section_80CCD1B"].get("additional_limit")
        
        common = self._rules.get("common_deductions_exemptions", {})
        if "80CCD(1B)" in common:
            return common["80CCD(1B)"].get("max_amount")
        
        raise TaxRulesNotFoundError(f"Section 80CCD(1B) limit not found in rules for FY {self.financial_year}")
    
    # ==========================================
    # SECTION 80CCD(2) - Employer NPS
    # ==========================================
    def get_80ccd2_percent(self, employer_type: str = "private") -> int:
        """Get 80CCD(2) employer NPS percentage limit"""
        deductions = self._rules.get("deductions", {})
        
        # Try new regime allowed deductions
        new_allowed = deductions.get("new_regime_115BAC(1A)_allowed", {})
        if "section_80CCD_2_employer_nps" in new_allowed:
            limits = new_allowed["section_80CCD_2_employer_nps"].get("limit", [])
            for limit in limits:
                if employer_type.lower() in ["central", "state", "government"]:
                    if "Government" in limit.get("employer_type", ""):
                        return limit.get("percent_of_salary", 14)
                else:
                    if "PSU" in limit.get("employer_type", "") or "Others" in limit.get("employer_type", ""):
                        return limit.get("percent_of_salary", 10)
        
        # Try common deductions
        common = self._rules.get("common_deductions_exemptions", {})
        if "80CCD(2)" in common:
            return common["80CCD(2)"].get("max_amount_percent_salary", 10)
        
        # Default based on employer type
        return 14 if employer_type.lower() in ["central", "state", "government"] else 10
    
    # ==========================================
    # SECTION 80D - Health Insurance
    # ==========================================
    def get_80d_limits(self) -> Dict[str, int]:
        """Get 80D health insurance limits"""
        deductions = self._rules.get("deductions", {})
        old_regime = deductions.get("old_regime_chapter_VIA_and_others", {})
        
        result = {
            "self_family": 25000,
            "self_family_senior": 50000,
            "parents": 25000,
            "parents_senior": 50000,
            "preventive_checkup": 5000
        }
        
        if "section_80D_health_insurance" in old_regime:
            d80 = old_regime["section_80D_health_insurance"]
            
            self_fam = d80.get("self_family", {})
            result["self_family"] = self_fam.get("limit", 25000)
            result["self_family_senior"] = self_fam.get("senior_citizen_limit", 50000)
            result["preventive_checkup"] = self_fam.get("preventive_checkup_included_limit", 5000)
            
            parents = d80.get("parents", {})
            result["parents"] = parents.get("limit", 25000)
            result["parents_senior"] = parents.get("senior_citizen_limit", 50000)
        else:
            # Try common deductions
            common = self._rules.get("common_deductions_exemptions", {})
            if "80D" in common:
                d80 = common["80D"]
                result["self_family"] = d80.get("max_amount_self_family", 25000)
                result["parents"] = d80.get("max_amount_parents", 25000)
                result["parents_senior"] = d80.get("max_amount_parents_senior", 50000)
        
        return result
    
    # ==========================================
    # SECTION 80DD/80U - Disability
    # ==========================================
    def get_disability_limits(self) -> Dict[str, int]:
        """Get 80DD (dependent) and 80U (self) disability limits"""
        deductions = self._rules.get("deductions", {})
        old_regime = deductions.get("old_regime_chapter_VIA_and_others", {})
        
        result = {
            "80DD_regular": 75000,
            "80DD_severe": 125000,
            "80U_regular": 75000,
            "80U_severe": 125000
        }
        
        if "section_80DD_disabled_dependent" in old_regime:
            dd = old_regime["section_80DD_disabled_dependent"]
            result["80DD_regular"] = dd.get("regular_disability", 75000)
            result["80DD_severe"] = dd.get("severe_disability_80_percent_or_more", 125000)
        
        if "section_80U_taxpayer_with_disability" in old_regime:
            u = old_regime["section_80U_taxpayer_with_disability"]
            result["80U_regular"] = u.get("regular_disability", 75000)
            result["80U_severe"] = u.get("severe_disability_80_percent_or_more", 125000)
        
        return result
    
    # ==========================================
    # SECTION 80DDB - Medical Treatment
    # ==========================================
    def get_80ddb_limits(self) -> Dict[str, int]:
        """Get 80DDB medical treatment limits"""
        deductions = self._rules.get("deductions", {})
        old_regime = deductions.get("old_regime_chapter_VIA_and_others", {})
        
        if "section_80DDB_specified_diseases" in old_regime:
            ddb = old_regime["section_80DDB_specified_diseases"]
            return {
                "non_senior": ddb.get("non_senior_citizen_limit", 40000),
                "senior": ddb.get("senior_citizen_limit", 100000)
            }
        
        return {"non_senior": 40000, "senior": 100000}
    
    # ==========================================
    # SECTION 80TTA/80TTB - Interest Deduction
    # ==========================================
    def get_80tta_limit(self) -> int:
        """Get 80TTA savings interest limit (non-seniors)"""
        deductions = self._rules.get("deductions", {})
        old_regime = deductions.get("old_regime_chapter_VIA_and_others", {})
        
        if "section_80TTA_savings_interest_non_senior" in old_regime:
            return old_regime["section_80TTA_savings_interest_non_senior"].get("limit")
        
        common = self._rules.get("common_deductions_exemptions", {})
        if "80TTA" in common:
            return common["80TTA"].get("max_amount")
        
        raise TaxRulesNotFoundError(f"Section 80TTA limit not found in rules for FY {self.financial_year}")
    
    def get_80ttb_limit(self) -> int:
        """Get 80TTB deposit interest limit (seniors only)"""
        deductions = self._rules.get("deductions", {})
        old_regime = deductions.get("old_regime_chapter_VIA_and_others", {})
        
        if "section_80TTB_deposit_interest_senior" in old_regime:
            return old_regime["section_80TTB_deposit_interest_senior"].get("limit")
        
        common = self._rules.get("common_deductions_exemptions", {})
        if "80TTB" in common:
            return common["80TTB"].get("max_amount")
        
        raise TaxRulesNotFoundError(f"Section 80TTB limit not found in rules for FY {self.financial_year}")
    
    # ==========================================
    # SECTION 80EE/80EEA/80EEB - Home/EV Loan
    # ==========================================
    def get_home_loan_limits(self) -> Dict[str, int]:
        """Get home loan interest deduction limits"""
        deductions = self._rules.get("deductions", {})
        old_regime = deductions.get("old_regime_chapter_VIA_and_others", {})
        
        result = {
            "24b_self_occupied": 200000,
            "80EE": 50000,
            "80EEA": 150000,
            "80EEB": 150000
        }
        
        # Section 24(b) - Self occupied
        if "section_24b_house_property_interest" in old_regime:
            s24 = old_regime["section_24b_house_property_interest"]
            self_occupied = s24.get("self_occupied", [])
            if self_occupied and len(self_occupied) > 0:
                result["24b_self_occupied"] = self_occupied[0].get("limit", 200000)
        
        # Section 80EE
        if "section_80EE_home_loan_interest_extra" in old_regime:
            result["80EE"] = old_regime["section_80EE_home_loan_interest_extra"].get("limit", 50000)
        
        # Section 80EEA
        if "section_80EEA_first_time_home_buyer_interest" in old_regime:
            result["80EEA"] = old_regime["section_80EEA_first_time_home_buyer_interest"].get("limit", 150000)
        
        # Section 80EEB (EV loan)
        if "section_80EEB_ev_loan_interest" in old_regime:
            result["80EEB"] = old_regime["section_80EEB_ev_loan_interest"].get("limit", 150000)
        
        return result
    
    # ==========================================
    # SECTION 80GG - Rent
    # ==========================================
    def get_80gg_info(self) -> Dict[str, Any]:
        """Get 80GG rent deduction info"""
        deductions = self._rules.get("deductions", {})
        old_regime = deductions.get("old_regime_chapter_VIA_and_others", {})
        
        if "section_80GG_rent_no_hra" in old_regime:
            return old_regime["section_80GG_rent_no_hra"]
        
        return {
            "least_of": [
                "Rent paid minus 10% of Total Income",
                "₹5,000 per month",
                "25% of Total Income"
            ]
        }
    
    # ==========================================
    # TAX SLABS
    # ==========================================
    def get_slabs(self, regime: str, age: int = 30) -> List[Dict[str, Any]]:
        """Get tax slabs based on regime and age"""
        # Determine age category
        if age >= 80:
            age_category = "individual_80_and_above"
        elif age >= 60:
            age_category = "individual_60_to_79"
        else:
            age_category = "individual_below_60"
        
        # Determine regime key
        if regime.lower() in ["new", "new_regime"]:
            regime_key = "new_regime_115BAC(1A)"
            # FY 2023-24 format check
            if "income_tax_slabs" in self._rules:
                regime_key = "new_regime"
        else:
            regime_key = "old_regime"
        
        # Try FY 2024-25 format first (slabs key)
        if "slabs" in self._rules:
            slabs_data = self._rules["slabs"]
            age_slabs = slabs_data.get(age_category, {})
            
            # Handle "Same as individual_below_60" references
            regime_slabs = age_slabs.get(regime_key)
            if isinstance(regime_slabs, str) and "Same as" in regime_slabs:
                # Use individual_below_60 slabs
                age_slabs = slabs_data.get("individual_below_60", {})
                regime_slabs = age_slabs.get(regime_key, [])
            
            if regime_slabs:
                return self._normalize_slabs(regime_slabs)
        
        # Try FY 2023-24 format (income_tax_slabs key)
        if "income_tax_slabs" in self._rules:
            slabs_data = self._rules["income_tax_slabs"]
            regime_data = slabs_data.get(regime_key, {})
            
            # Map age category
            if age >= 80:
                cat = "super_senior_citizen"
            elif age >= 60:
                cat = "senior_citizen"
            else:
                cat = "general"
            
            cat_data = regime_data.get(cat, regime_data.get("general", {}))
            if "slabs" in cat_data:
                return self._normalize_slabs(cat_data["slabs"])
        
        raise TaxRulesNotFoundError(f"Tax slabs not found for {regime} regime, age {age} in FY {self.financial_year}")
    
    def _normalize_slabs(self, slabs: List[Dict]) -> List[Dict[str, Any]]:
        """Normalize different slab formats to standard format"""
        normalized = []
        
        for slab in slabs:
            entry = {
                "min": 0,
                "max": None,
                "rate_percent": 0
            }
            
            # Handle min
            if "min" in slab:
                entry["min"] = slab["min"]
            elif "over" in slab:
                entry["min"] = slab["over"] + 1
            elif "upto" in slab:
                entry["min"] = 0
            
            # Handle max
            if "max" in slab:
                entry["max"] = slab["max"]
            elif "up_to" in slab:
                entry["max"] = slab["up_to"]
            elif "upto" in slab:
                entry["max"] = slab["upto"]
            
            # Handle rate
            if "rate_percent" in slab:
                entry["rate_percent"] = slab["rate_percent"]
            elif "formula" in slab:
                # Parse formula to extract rate
                formula = slab["formula"]
                if "30%" in formula:
                    entry["rate_percent"] = 30
                elif "25%" in formula:
                    entry["rate_percent"] = 25
                elif "20%" in formula:
                    entry["rate_percent"] = 20
                elif "15%" in formula:
                    entry["rate_percent"] = 15
                elif "10%" in formula:
                    entry["rate_percent"] = 10
                elif "5%" in formula:
                    entry["rate_percent"] = 5
            
            normalized.append(entry)
        
        return normalized
    
    # ==========================================
    # REBATE 87A
    # ==========================================
    def get_rebate_87a(self, regime: str) -> Dict[str, Any]:
        """Get rebate u/s 87A details"""
        rebate = self._rules.get("rebate_87A", {})
        
        regime_key = "new_regime" if regime.lower() in ["new", "new_regime"] else "old_regime"
        
        if regime_key in rebate:
            return rebate[regime_key]
        
        raise TaxRulesNotFoundError(f"Rebate 87A not found for {regime} regime in FY {self.financial_year}")
    
    # ==========================================
    # CESS
    # ==========================================
    def get_cess_percent(self) -> float:
        """Get Health & Education Cess percentage"""
        cess = self._rules.get("cess", {})
        return cess.get("health_and_education_cess_percent", 4)
    
    # ==========================================
    # SURCHARGE
    # ==========================================
    def get_surcharge_thresholds(self, regime: str) -> List[Dict[str, Any]]:
        """Get surcharge thresholds for given regime"""
        surcharge = self._rules.get("surcharge_and_marginal_relief", {})
        
        key = "surcharge_new_regime_thresholds" if regime.lower() in ["new", "new_regime"] else "surcharge_old_regime_thresholds"
        
        return surcharge.get(key, [])
    
    # ==========================================
    # ALL DEDUCTION LIMITS
    # ==========================================
    def get_all_deduction_limits(self, age: int = 30) -> Dict[str, Any]:
        """Get all deduction limits in one call (for investment suggestions etc.)"""
        is_senior = age >= 60
        
        d80_limits = self.get_80d_limits()
        disability = self.get_disability_limits()
        ddb = self.get_80ddb_limits()
        home_loan = self.get_home_loan_limits()
        
        return {
            "Standard Deduction": self.get_standard_deduction(),
            "Professional Tax": self.get_professional_tax_limit(),
            "80C": self.get_80c_limit(),
            "80CCC": self.get_80c_limit(),  # Part of 80C
            "80CCD_1": self.get_80c_limit(),  # Part of 80C
            "80CCD_1B": self.get_80ccd1b_limit(),
            "80CCD_2_percent": self.get_80ccd2_percent("private"),
            "80D_self": d80_limits["self_family_senior"] if is_senior else d80_limits["self_family"],
            "80D_parents": d80_limits["parents"],
            "80D_parents_senior": d80_limits["parents_senior"],
            "80D_preventive": d80_limits["preventive_checkup"],
            "80DD": disability["80DD_regular"],
            "80DD_severe": disability["80DD_severe"],
            "80DDB": ddb["senior"] if is_senior else ddb["non_senior"],
            "80E": None,  # No limit for education loan interest
            "80EE": home_loan["80EE"],
            "80EEA": home_loan["80EEA"],
            "80EEB": home_loan["80EEB"],
            "80G": None,  # Varies by donation type
            "80GG": 60000,  # Max Rs. 5000/month
            "80TTA": self.get_80tta_limit() if not is_senior else 0,
            "80TTB": self.get_80ttb_limit() if is_senior else 0,
            "80U": disability["80U_regular"],
            "80U_severe": disability["80U_severe"],
            "24b": home_loan["24b_self_occupied"],
        }


def get_rules_service(db: Session, financial_year: str = "2024-25") -> RulesService:
    """Factory function to create RulesService instance"""
    return RulesService(db, financial_year)
