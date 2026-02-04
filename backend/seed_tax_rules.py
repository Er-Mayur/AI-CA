"""
Script to seed tax rules into the database
"""
from database import SessionLocal, engine
from models import Base, TaxRule
import json

# ==========================================
# Tax Rules for Previous FY (2023-24)
# ==========================================
TAX_RULES_2023_24 = {
  "schema_version": "1.0.0",
  "assessment_year": "2024-25",
  "financial_year": "2023-24",
  "source": {
    "title": "Salaried Individuals for AY 2024-25 | Income Tax Department",
    "page_url": "https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-1#taxdeductions",
    "page_last_reviewed_dates": ["2024-03-31"],
    "note": "Back-dated for previous year calculations"
  },
  "regime_default_and_switching": {
    "default_regime": "new_regime_115BAC",
    "effective_from_ay": "2024-25",
    "who_default_applies_to": ["Individual", "HUF"],
    "non_business_taxpayers_switching": {
      "how": "Choose regime directly in ITR each year",
      "condition": "ITR filed on or before due date u/s 139(1)"
    },
    "business_or_profession_switching": {
      "opt_out_from_default": {"form": "Form 10-IEA", "deadline": "Due date u/s 139(1)"}
    }
  },
  "cess": {"health_and_education_cess_percent": 4},
  "rebate_87A": {
    "old_regime": {"max_total_income": 500000,"rebate_cap": 12500,"resident_only": True,"nr_not_eligible": True},
    "new_regime": {"max_total_income": 700000,"rebate_cap": 25000,"resident_only": True,"nr_not_eligible": True}
  },
  "surcharge_and_marginal_relief": {
    "surcharge_old_regime_thresholds": [
      {"min_exclusive": 5000000, "rate_percent": 10},
      {"min_exclusive": 10000000, "rate_percent": 15},
      {"min_exclusive": 20000000, "rate_percent": 25},
      {"min_exclusive": 50000000, "rate_percent": 37}
    ],
    "surcharge_new_regime_thresholds": [
      {"min_exclusive": 5000000, "rate_percent": 10},
      {"min_exclusive": 10000000, "rate_percent": 15},
      {"min_exclusive": 20000000, "rate_percent": 25}
    ],
    "surcharge_cap_15_percent_applies_to": [
      "Section 111A short term capital gains",
      "Section 112 long term capital gains", 
      "Dividend Income"
    ],
    "marginal_relief_applicable": True
  },
  "income_tax_slabs": {
    "old_regime": {
      "general": {
        "age_category": "Below 60 years",
        "slabs": [
          {"min": 0, "max": 250000, "rate_percent": 0},
          {"min": 250001, "max": 500000, "rate_percent": 5},
          {"min": 500001, "max": 1000000, "rate_percent": 20},
          {"min": 1000001, "max": None, "rate_percent": 30}
        ]
      },
      "senior_citizen": {
        "age_category": "60 to 80 years",
        "slabs": [
          {"min": 0, "max": 300000, "rate_percent": 0},
          {"min": 300001, "max": 500000, "rate_percent": 5},
          {"min": 500001, "max": 1000000, "rate_percent": 20},
          {"min": 1000001, "max": None, "rate_percent": 30}
        ]
      },
      "super_senior_citizen": {
        "age_category": "Above 80 years",
        "slabs": [
          {"min": 0, "max": 500000, "rate_percent": 0},
          {"min": 500001, "max": 1000000, "rate_percent": 20},
          {"min": 1000001, "max": None, "rate_percent": 30}
        ]
      }
    },
    "new_regime": {
      "general": {
        "age_category": "All ages",
        "slabs": [
          {"min": 0, "max": 300000, "rate_percent": 0},
          {"min": 300001, "max": 600000, "rate_percent": 5},
          {"min": 600001, "max": 900000, "rate_percent": 10},
          {"min": 900001, "max": 1200000, "rate_percent": 15},
          {"min": 1200001, "max": 1500000, "rate_percent": 20},
          {"min": 1500001, "max": None, "rate_percent": 30}
        ]
      }
    }
  },
  "common_deductions_exemptions": {
    "standard_deduction_salaried": {"section": "16(ia)", "max_amount": 50000, "regimes_allowed": ["old_regime", "new_regime"]},
    "professional_tax": {"section": "16(iii)", "max_amount": 2500, "regimes_allowed": ["old_regime"]},
    "hra": {"section": "10(13A)", "calculation_method": "min_of_3_with_city_logic", "regimes_allowed": ["old_regime"]},
    "lta": {"section": "10(5)", "notes": "Two journeys in block of 4 years", "regimes_allowed": ["old_regime"]},
    "80C": {"section": "80C", "max_amount": 150000, "includes": ["EPF", "PPF", "LIC", "ELSS", "Tuition Fees", "Principal Repayment of Home Loan"], "regimes_allowed": ["old_regime"]},
    "80D": {"section": "80D", "max_amount_self_family": 25000, "max_amount_parents": 25000, "max_amount_parents_senior": 50000, "regimes_allowed": ["old_regime"]},
    "80CCD(1B)": {"section": "80CCD(1B)", "max_amount": 50000, "notes": "NPS additional deduction", "regimes_allowed": ["old_regime", "new_regime"]},
    "80CCD(2)": {"section": "80CCD(2)", "max_amount_percent_salary": 14, "notes": "Employer contribution to NPS (Central/State Govt: 14%, Others: 10%)", "regimes_allowed": ["old_regime", "new_regime"]},
    "80TTA": {"section": "80TTA", "max_amount": 10000, "notes": "Savings bank interest for non-seniors", "regimes_allowed": ["old_regime"]},
    "80TTB": {"section": "80TTB", "max_amount": 50000, "notes": "Interest income for senior citizens", "regimes_allowed": ["old_regime"]}
  }
}

# Use the existing variable for current year, renaming variable for clarity if modifying script extensively.
# Keeping existing TAX_RULES_2024_25 block intact below this insertion.

# Tax rules for FY 2024-25
TAX_RULES_2024_25 = {
  "schema_version": "1.0.0",
  "assessment_year": "2025-26",
  "financial_year": "2024-25",
  "source": {
    "title": "Salaried Individuals for AY 2025-26 | Income Tax Department",
    "page_url": "https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-1#taxdeductions",
    "page_last_reviewed_dates": [
      "2025-09-19",
      "2025-11-04"
    ],
    "note": "This JSON encodes only what appears in the official AY 2025-26 salaried individuals help page/PDF."
  },
  "regime_default_and_switching": {
    "default_regime": "new_regime_115BAC(1A)",
    "effective_from_ay": "2024-25",
    "who_default_applies_to": [
      "Individual",
      "HUF",
      "AOP (non-cooperative)",
      "BOI",
      "Artificial Juridical Person"
    ],
    "non_business_taxpayers_switching": {
      "how": "Choose regime directly in ITR each year",
      "condition": "ITR filed on or before due date u/s 139(1)"
    },
    "business_or_profession_switching": {
      "opt_out_from_default": {
        "form": "Form 10-IEA",
        "deadline": "Due date u/s 139(1)"
      },
      "re-enter_new_regime": {
        "form": "Form 10-IEA",
        "deadline": "Due date u/s 139(4)",
        "lifetime_limit": "Only once in subsequent AYs"
      }
    }
  },
  "cess": {
    "health_and_education_cess_percent": 4
  },
  "rebate_87A": {
    "old_regime": {
      "max_total_income": 500000,
      "rebate_cap": 12500,
      "resident_only": True,
      "nr_not_eligible": True
    },
    "new_regime": {
      "max_total_income": 700000,
      "rebate_cap": 20000,
      "resident_only": True,
      "nr_not_eligible": True
    }
  },
  "surcharge_and_marginal_relief": {
    "surcharge_old_regime_thresholds": [
      {
        "min_exclusive": 5000000,
        "rate_percent": 10
      },
      {
        "min_exclusive": 10000000,
        "rate_percent": 15
      },
      {
        "min_exclusive": 20000000,
        "rate_percent": 25
      },
      {
        "min_exclusive": 50000000,
        "rate_percent": 37
      }
    ],
    "surcharge_new_regime_thresholds": [
      {
        "min_exclusive": 5000000,
        "rate_percent": 10
      },
      {
        "min_exclusive": 10000000,
        "rate_percent": 15
      },
      {
        "min_exclusive": 20000000,
        "rate_percent": 25
      }
    ],
    "surcharge_cap_15_percent_applies_to": [
      "Section 111A short term capital gains",
      "Section 112 long term capital gains",
      "Section 112A long term capital gains",
      "Dividend income"
    ],
    "marginal_relief": {
      "old_regime": [
        {
          "over": 5000000,
          "up_to": 10000000
        },
        {
          "over": 10000000,
          "up_to": 20000000
        },
        {
          "over": 20000000,
          "up_to": 50000000
        },
        {
          "over": 50000000,
          "up_to": None
        }
      ],
      "new_regime": [
        {
          "over": 5000000,
          "up_to": 10000000
        },
        {
          "over": 10000000,
          "up_to": 20000000
        },
        {
          "over": 20000000,
          "up_to": None
        }
      ],
      "rule": "Tax + surcharge at the slab should not exceed tax at lower threshold by more than income exceeding that threshold."
    }
  },
  "slabs": {
    "notes": [
      "Rates here are exclusive of surcharge and 4% H&EC.",
      "Old regime has age-based basic exemption; new regime slabs are uniform for age groups below."
    ],
    "individual_below_60": {
      "old_regime": [
        {
          "upto": 250000,
          "rate_percent": 0
        },
        {
          "over": 250000,
          "up_to": 500000,
          "rate_percent": 5
        },
        {
          "over": 500000,
          "up_to": 1000000,
          "rate_percent": 20
        },
        {
          "over": 1000000,
          "rate_percent": 30
        }
      ],
      "new_regime_115BAC(1A)": [
        {
          "upto": 300000,
          "rate_percent": 0
        },
        {
          "over": 300000,
          "up_to": 700000,
          "rate_percent": 5
        },
        {
          "over": 700000,
          "up_to": 1000000,
          "formula": "20000 + 10% of amount over 700000"
        },
        {
          "over": 1000000,
          "up_to": 1200000,
          "formula": "50000 + 15% of amount over 1000000"
        },
        {
          "over": 1200000,
          "up_to": 1500000,
          "formula": "80000 + 20% of amount over 1200000"
        },
        {
          "over": 1500000,
          "formula": "140000 + 30% of amount over 1500000"
        }
      ]
    },
    "individual_60_to_79": {
      "old_regime": [
        {
          "upto": 300000,
          "rate_percent": 0
        },
        {
          "over": 300000,
          "up_to": 500000,
          "rate_percent": 5
        },
        {
          "over": 500000,
          "up_to": 1000000,
          "rate_percent": 20
        },
        {
          "over": 1000000,
          "rate_percent": 30
        }
      ],
      "new_regime_115BAC(1A)": "Same as individual_below_60 new regime slabs"
    },
    "individual_80_and_above": {
      "old_regime": [
        {
          "upto": 500000,
          "rate_percent": 0
        },
        {
          "over": 500000,
          "up_to": 1000000,
          "rate_percent": 20
        },
        {
          "over": 1000000,
          "rate_percent": 30
        }
      ],
      "new_regime_115BAC(1A)": "Same as individual_below_60 new regime slabs"
    }
  },
  "itr_forms_applicability": {
    "itr_1_sahaj": {
      "applicable_to": "Resident Individual (other than Not Ordinarily Resident) with Total Income up to ₹50 lakh from Salary/Pension, One House Property, Other Sources, Agricultural Income up to ₹5,000, and Long-term capital gain u/s 112A up to ₹1,25,000.",
      "cannot_be_used_if_any": [
        "Director in a company",
        "Has short term capital gain",
        "Has long-term capital gain u/s 112A exceeding ₹1,25,000",
        "Held any unlisted equity shares at any time during the previous year",
        "Has any asset (including financial interest in any entity) located outside India",
        "Has signing authority in any account located outside India",
        "Has income from any source outside India",
        "Tax has been deducted u/s 194N",
        "Payment or deduction of tax on ESOP deferred",
        "Has any brought forward loss or loss to be carried forward under any head of income",
        "Total income exceeds ₹50 lakh"
      ]
    },
    "itr_2": {
      "applicable_to": [
        "Individuals and HUFs having income under any head other than Profits and Gains of Business or Profession",
        "Individuals not eligible for ITR-1"
      ]
    },
    "itr_3": {
      "applicable_to": [
        "Individuals and HUFs having income under Salary/Pension, House Property, Profits or Gains of Business or Profession, Capital Gains or Income from Other Sources",
        "Who are not eligible for filing ITR-1, ITR-2 or ITR-4"
      ]
    },
    "itr_4_sugam": {
      "applicable_to": "Individual or HUF (Resident other than NOR) or Firm (other than LLP) Resident with presumptive income u/s 44AD/44ADA/44AE and also having Salary/Pension, One House Property, Other Sources, Agricultural income up to ₹5,000.",
      "notes": [
        "ITR-4 (Sugam) is optional; simplified return for eligible presumptive cases."
      ],
      "cannot_be_used_if_any": [
        "Director in a company",
        "Has short term capital gains",
        "Has long-term capital gain u/s 112A exceeding ₹1,25,000",
        "Held any unlisted equity shares at any time during the previous year",
        "Has any asset (including financial interest in any entity) located outside India",
        "Has signing authority in any account located outside India",
        "Has income from any source outside India",
        "Payment or deduction of tax on ESOP deferred",
        "Has any brought forward loss or loss to be carried forward under any head of income",
        "Total income exceeds ₹50 lakh"
      ]
    }
  },
  "forms_and_information": [
    {
      "form": "Form 12BB",
      "purpose": "Employee's evidence/particulars to employer for HRA, LTC, home loan interest, and tax-saving claims for TDS computation"
    },
    {
      "form": "Form 16",
      "purpose": "Certificate of TDS on Salary with income, deductions/exemptions, and TDS for tax payable/refund computation",
      "section": "203"
    },
    {
      "form": "Form 16A",
      "purpose": "Quarterly TDS certificate for income other than salary; amount and nature of TDS and deposits"
    },
    {
      "form": "Form 67",
      "purpose": "Statement of foreign income and Foreign Tax Credit; to be filed on or before due date u/s 139(1)"
    },
    {
      "form": "Form 26AS",
      "purpose": "TDS/TCS and tax payments; available via e-filing portal"
    },
    {
      "form": "AIS",
      "purpose": "TDS/TCS, SFT, payment of taxes, demand/refund, other info incl. proceedings/GST/foreign govt info"
    },
    {
      "form": "Form 15G",
      "purpose": "Declaration by resident (non-company/non-firm) to bank for no TDS on interest when below basic exemption; includes estimated income for FY"
    },
    {
      "form": "Form 15H",
      "purpose": "Declaration by resident individual 60+ to bank for no TDS on interest; includes estimated income for FY"
    },
    {
      "form": "Form 10E",
      "purpose": "Furnish particulars for relief u/s 89(1) when salary is paid in arrears or advance; covers gratuity, termination compensation, commuted pension"
    }
  ],
  "deductions": {
    "new_regime_115BAC(1A)_allowed": {
      "section_24b_house_property_interest": {
        "property_type": "Let Out",
        "limit": "No monetary limit on interest deduction in HP head",
        "setoff_carryforward": "Loss under HP cannot be set-off against other heads (schedule CYLA) and cannot be carried forward"
      },
      "section_80CCD_2_employer_nps": {
        "limit": [
          {
            "employer_type": "Central or State Government",
            "percent_of_salary": 14
          },
          {
            "employer_type": "PSU or Others",
            "percent_of_salary": 10
          }
        ]
      },
      "section_80CCH_agnipath": {
        "employee_contribution": "Full amount paid/deposited allowed",
        "government_contribution": "Full amount contributed allowed"
      }
    },
    "old_regime_chapter_VIA_and_others": {
      "section_24b_house_property_interest": {
        "self_occupied": [
          {
            "loan_sanction_on_or_after": "1999-04-01",
            "purpose": "Construction/Purchase",
            "limit": 200000
          },
          {
            "loan_sanction_on_or_after": "1999-04-01",
            "purpose": "Repairs",
            "limit": 30000
          },
          {
            "loan_sanction_before": "1999-04-01",
            "purpose": "Construction/Purchase",
            "limit": 30000
          },
          {
            "loan_sanction_before": "1999-04-01",
            "purpose": "Repairs",
            "limit": 30000
          }
        ],
        "let_out": {
          "limit": "Actual interest (no cap)",
          "setoff_cap_against_other_heads_per_ay": 200000,
          "carry_forward_years": 8
        }
      },
      "section_80C_80CCC_80CCD1": {
        "combined_limit": 150000,
        "eligible_examples": [
          "Life Insurance Premium",
          "Provident Fund",
          "Subscription to certain equity shares",
          "Tuition Fees",
          "National Savings Certificate",
          "Housing Loan Principal",
          "Other specified items"
        ],
        "itr_details_required": [
          "Policy/document identification number",
          "Amount eligible under 80C"
        ],
        "ccd1_details_required": [
          "Contribution amount",
          "PRAN"
        ]
      },
      "section_80CCD1B": {
        "additional_limit": 50000
      },
      "section_80CCD2_employer_nps": {
        "limits": [
          {
            "employer_type": "PSU or Others",
            "percent_of_salary": 10
          },
          {
            "employer_type": "Central or State Government",
            "percent_of_salary": 14
          }
        ]
      },
      "section_80CCH_agnipath": {
        "employee_contribution": "Full amount allowed",
        "government_contribution": "Full amount allowed"
      },
      "section_80D_health_insurance": {
        "self_family": {
          "limit": 25000,
          "senior_citizen_limit": 50000,
          "preventive_checkup_included_limit": 5000
        },
        "parents": {
          "limit": 25000,
          "senior_citizen_limit": 50000,
          "preventive_checkup_included_limit": 5000
        },
        "medical_expenditure_no_insurance_for_senior": {
          "self_family": 50000,
          "parents": 50000
        },
        "itr_details_required": [
          "Insurer name",
          "Policy number",
          "Health insurance amount"
        ]
      },
      "section_80DD_disabled_dependent": {
        "regular_disability": 75000,
        "severe_disability_80_percent_or_more": 125000,
        "itr_details_required": [
          "Nature of disability",
          "Type of disability",
          "Amount of deduction",
          "Type of dependent",
          "PAN of dependent",
          "Aadhaar of dependent",
          "Form 10IA acknowledgement no. (where applicable)",
          "UDID number (if available)"
        ]
      },
      "section_80DDB_specified_diseases": {
        "non_senior_citizen_limit": 40000,
        "senior_citizen_limit": 100000
      },
      "section_80E_education_loan_interest": {
        "amount": "Total interest paid on eligible education loan",
        "itr_details_required": [
          "Lender type (bank/financial institution)",
          "Lender name",
          "Loan account number",
          "Sanction date",
          "Total loan amount",
          "Outstanding as of FY end",
          "Interest u/s 80E"
        ]
      },
      "section_80EE_home_loan_interest_extra": {
        "loan_sanction_window": [
          "2016-04-01",
          "2017-03-31"
        ],
        "limit": 50000,
        "itr_details_required": [
          "Lender type/name",
          "Loan account number",
          "Sanction date",
          "Total loan amount",
          "Outstanding as of FY end",
          "Interest u/s 80EE"
        ]
      },
      "section_80EEA_first_time_home_buyer_interest": {
        "loan_sanction_window": [
          "2019-04-01",
          "2022-03-31"
        ],
        "limit": 150000,
        "conditions": [
          "Only if 24(b) limit exhausted",
          "Mutually exclusive with 80EE",
          "Stamp value of residential house must be provided"
        ],
        "itr_details_required": [
          "Stamp value of house property",
          "Lender type/name",
          "Loan account number",
          "Sanction date",
          "Total loan amount",
          "Outstanding as of FY end",
          "Interest u/s 80EEA"
        ]
      },
      "section_80EEB_ev_loan_interest": {
        "loan_sanction_window": [
          "2019-04-01",
          "2023-03-31"
        ],
        "limit": 150000,
        "itr_details_required": [
          "Lender type/name",
          "Loan account number",
          "Sanction date",
          "Total loan amount",
          "Outstanding as of FY end",
          "Interest u/s 80EEB"
        ]
      },
      "section_80G_donations": {
        "cash_donation_limit": 2000,
        "categories": [
          "100% deduction without qualifying limit",
          "50% deduction without qualifying limit",
          "100% deduction subject to qualifying limit",
          "50% deduction subject to qualifying limit"
        ]
      },
      "section_80GG_rent_no_hra": {
        "least_of": [
          "Rent paid minus 10% of Total Income before this deduction",
          "₹5,000 per month",
          "25% of Total Income (excluding LTCG, STCG u/s 111A, income u/s 115A/115D)"
        ],
        "form_requirement": "Form 10BA must be filed; acknowledgement number to be entered in Schedule 80GG"
      },
      "section_80GGA_scientific_research_rural_development": {
        "categories": [
          "Research association/university/college/institution for scientific research",
          "Research association/university/college/institution for social science or statistical research",
          "Association/institution for rural development",
          "Conservation of natural resources or afforestation",
          "PSU or Local Authority or association/institution approved by National Committee for eligible project",
          "Funds notified by Central Government for afforestation/rural development",
          "National Urban Poverty Eradication Fund notified by Central Government"
        ],
        "cash_donation_limit": 2000,
        "not_allowed_if": "Gross Total Income includes income from profits/gains of business/profession"
      },
      "section_80GGC_political_contribution": {
        "note": "No deduction allowed if contribution made in cash"
      },
      "section_80TTA_savings_interest_non_senior": {
        "limit": 10000
      },
      "section_80TTB_deposit_interest_senior": {
        "limit": 50000
      },
      "section_80U_taxpayer_with_disability": {
        "regular_disability": 75000,
        "severe_disability_80_percent_or_more": 125000,
        "itr_details_required": [
          "Nature of disability",
          "Type of disability",
          "Amount of deduction",
          "Form 10IA acknowledgement no. (for autism, cerebral palsy, multiple disabilities)",
          "UDID number (if available)"
        ]
      }
    }
  },
  "procedural_and_definitions": {
    "definitions_in_scope_examples": [
      "Assessment Year (AY) vs Financial Year (FY)",
      "Total Income",
      "Resident / Not Ordinarily Resident / Non-Resident (conceptual reference)"
    ],
    "filing_guidance_examples": [
      "ITR due date u/s 139(1) (e.g., 31 July for non-audit)",
      "Belated/revised return timelines and 234F late fee (general awareness)",
      "e-Verification and ITR acknowledgement steps"
    ],
    "note": "The PDF focuses primarily on applicability, slabs, deductions, and forms; detailed definitions and step-by-step filing procedures are referenced at a high level."
  }
}

def seed_tax_rules():
    """Seed tax rules into database"""
    # Create all tables first
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if tax rules already exist
        existing_rule = db.query(TaxRule).filter(
            TaxRule.financial_year == "2024-25"
        ).first()
        
        if existing_rule:
            print("Tax rules for FY 2024-25 already exist. Updating...")
            existing_rule.rules_json = TAX_RULES_2024_25
            existing_rule.is_active = True
        else:
            print("Creating tax rules for FY 2024-25...")
            tax_rule = TaxRule(
                financial_year="2024-25",
                assessment_year="2025-26",
                rules_json=TAX_RULES_2024_25,
                is_active=True
            )
            db.add(tax_rule)
        
        db.commit()
        print("[SUCCESS] Tax rules seeded successfully!")
        
    except Exception as e:
        print(f"[ERROR] Error seeding tax rules: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Seeding tax rules...")
    seed_tax_rules()

