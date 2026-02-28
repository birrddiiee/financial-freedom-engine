# ==========================================
# 🇮🇳 INDIAN TAX CONFIGURATION & ENGINE
# Update these constants annually after the Union Budget
# ==========================================

# --- CURRENT BUDGET CONSTANTS ---
LTCG_EQUITY = 0.125       # 12.5% Long Term Capital Gains on Equity
LTCG_ARBITRAGE = 0.125    # 12.5% Tax on Arbitrage Funds
LTCG_GOLD = 0.125         # 12.5% Tax on Financial Gold (SGBs, ETFs)
CESS = 0.04               # 4% Health and Education Cess

def calculate_india_tax(income):
    """
    Calculates progressive Indian income tax under the New Tax Regime.
    This applies to FD interest, salary, and other standard income.
    """
    if income <= 700000:
        return 0.0  # 87A Rebate makes income up to 7L tax-free

    tax = 0.0
    rem = income
    
    if rem > 1500000:
        tax += (rem - 1500000) * 0.30
        rem = 1500000
    if rem > 1200000:
        tax += (rem - 1200000) * 0.20
        rem = 1200000
    if rem > 900000:
        tax += (rem - 900000) * 0.15
        rem = 900000
    if rem > 600000:
        tax += (rem - 600000) * 0.10
        rem = 600000
    if rem > 300000:
        tax += (rem - 300000) * 0.05
        
    return tax * (1 + CESS)

def calculate_post_tax_rate(rate, asset_type, tax_slab, use_post_tax):
    """
    Reduces the gross expected return of an asset by its specific tax drag.
    Used for pre-retirement accumulation phase calculations.
    """
    if not use_post_tax:
        return rate
        
    if asset_type == "Equity": 
        return rate * (1 - LTCG_EQUITY) 
    elif asset_type == "Arbitrage": 
        return rate * (1 - LTCG_ARBITRAGE) 
    elif asset_type in ["FD", "Debt"]: 
        return rate * (1 - tax_slab)  # Taxed at marginal slab rate
    elif asset_type == "Gold": 
        return rate * (1 - LTCG_GOLD)
    elif asset_type == "EPF": 
        return rate  # EPF is assumed EEE (Exempt-Exempt-Exempt) for typical brackets
    else: 
        return rate