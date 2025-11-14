"""Loan business logic utilities."""


def calculate_interest(principal):
    """
    Calculate interest rate based on principal amount (tiered).
    
    Args:
        principal: Loan principal amount
    
    Returns:
        float: Annual interest rate
    """
    if 10000 <= principal < 1000000:
        return 8.45
    elif 1000000 <= principal < 2500000:
        return 10.0
    else:
        return 12.0


def calculate_emi(principal, months, rate):
    """
    Calculate monthly EMI (Equated Monthly Installment).
    
    Formula: EMI = P * R * (1+R)^N / ((1+R)^N - 1)
    where R = monthly rate (annual_rate / 12 / 100)
    
    Args:
        principal: Loan amount
        months: Loan tenure in months
        rate: Annual interest rate
    
    Returns:
        float: Monthly EMI amount
    """
    if months == 0:
        return 0
    
    rate_per_month = float(rate) / 1200
    numerator = float((1 + rate_per_month) ** months)
    denominator = numerator - 1
    
    if denominator == 0:
        return principal / months
    
    emi = principal * rate_per_month * (numerator / denominator)
    return round(emi, 2)
