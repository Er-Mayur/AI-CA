from typing import List, Dict, Any

def aggregate_document_data(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates financial data from a list of documents.

    Args:
        documents: A list of Document objects from the database.

    Returns:
        A dictionary with the aggregated financial data.
    """
    aggregated_data = {
        "salary_income": 0.0,
        "other_income": 0.0,
        "capital_gains": 0.0,
        "house_property_income": 0.0,
        "total_tds": 0.0,
        "deductions": {
            "80c": 0.0,
            "80d": 0.0,
            "80e": 0.0,
            "80g": 0.0,
            "80tta": 0.0,
            "80ccd_1b": 0.0,
            "employer_nps_80ccd_2": 0.0,
            "home_loan_interest": 0.0,
            "hra_exemption": 0.0,
        },
        "raw_deductions": [],
        "all_incomes": [],
        "all_tds": [],
    }

    for doc in documents:
        if not doc.extracted_data:
            continue

        data = doc.extracted_data

        # Aggregate Salary Income (usually from Form 16)
        salary = data.get("salary", 0.0) or data.get("income_chargeable_under_head_salaries", 0.0)
        if isinstance(salary, (int, float)):
            aggregated_data["salary_income"] += salary

        # Aggregate Other Income (from AIS, Form 26AS)
        other_income = data.get("income_from_other_sources", 0.0)
        if isinstance(other_income, (int, float)):
            aggregated_data["other_income"] += other_income
            
        # Aggregate Capital Gains
        cg = data.get("capital_gains", 0.0)
        if isinstance(cg, (int, float)):
            aggregated_data["capital_gains"] += cg

        # Aggregate TDS (from Form 16, Form 26AS)
        tds = data.get("tax_deducted_at_source", 0.0) or data.get("total_tds", 0.0)
        if isinstance(tds, (int, float)):
            aggregated_data["total_tds"] += tds

        # Aggregate Deductions
        if "deductions" in data and isinstance(data["deductions"], dict):
            for key, value in data["deductions"].items():
                if key in aggregated_data["deductions"] and isinstance(value, (int, float)):
                    aggregated_data["deductions"][key] += value
        
        # Collect raw values for more complex scenarios if needed
        aggregated_data["raw_deductions"].extend(data.get("raw_deductions", []))
        aggregated_data["all_incomes"].extend(data.get("all_incomes", []))
        aggregated_data["all_tds"].extend(data.get("all_tds", []))


    # Post-processing and consolidation can be added here if needed
    # For example, handling cases where salary is reported in multiple documents.

    print(f"✅ Aggregation complete:\n   Gross Total Income: ₹{aggregated_data['salary_income'] + aggregated_data['other_income']}\n   Salary Income: ₹{aggregated_data['salary_income']}\n   Total TDS: ₹{aggregated_data['total_tds']}\n   Deductions found: {sum(aggregated_data['deductions'].values())}")

    return aggregated_data
