import pandas as pd

def calculate_future_value(principal, annual_rate, years):
    return principal * ((1 + annual_rate) ** years)

def calculate_step_up_sip(monthly_investment, annual_return, years, annual_step_up):
    if years <= 0: return 0
    total_corpus = 0
    current_sip = monthly_investment
    for y in range(1, int(years) + 1):
        total_corpus = total_corpus * (1 + annual_return)
        # Add a year's worth of SIP, assuming mid-year average compounding for the new flows
        total_corpus += (current_sip * 12) * (1 + (annual_return / 2))
        current_sip *= (1 + annual_step_up)
    return total_corpus

def solve_extra_sip_needed(shortfall, years, rate, step_up):
    if shortfall <= 0 or years <= 0: return 0
    fv_unit = calculate_step_up_sip(1, rate, years, step_up)
    return shortfall / fv_unit if fv_unit > 0 else 0

def generate_forecast(data):
    age = data.get('age', 30)
    projection = [] 
    
    # Simulate year by year up to Age 100
    for y in range(101 - age):
        current_sim_age = age + y
        
        # Expenses (Inflated)
        fv_living = data['living_expense'] * ((1 + data['inflation']) ** y)
        fv_rent = (data['rent'] * ((1 + data['rent_inflation']) ** y)) if data.get('housing_goal') == "Rent Forever" else 0
        total_monthly_need = fv_living + fv_rent
        
        # Required Corpus at this age based on Safe Withdrawal Rate (SWR)
        corpus_req = (total_monthly_need * 12) / data['swr']
        
        # Add House Cost to the required corpus if buying a home
        if data.get('housing_goal') == "Buy a Home":
            corpus_req += data.get('house_cost', 0) * ((1 + data['rent_inflation']) ** y)
            
        # Accumulated Wealth at this age
        wealth = (
            calculate_future_value(data['cash'], data['rate_savings'], y) +
            calculate_future_value(data['fd'], data['rate_fd'], y) +
            calculate_future_value(data['epf'], data['rate_epf'], y) +
            calculate_future_value(data['mutual_funds'] + data['stocks'], data['rate_equity'], y) +
            calculate_future_value(data['gold'], data['rate_gold'], y) +
            calculate_future_value(data['arbitrage'], data['rate_arbitrage'], y) +
            calculate_step_up_sip(data['current_sip'], data['rate_new_sip'], y, data['step_up']) +
            calculate_step_up_sip(data['monthly_pf'], data['rate_epf'], y, data['step_up']) # 24% Auto-PF
        )
        
        projection.append({
            "Age": current_sim_age, 
            "Projected Wealth": round(wealth), 
            "Required Corpus": round(corpus_req), 
            "Gap": round(wealth - corpus_req)
        })
        
    return pd.DataFrame(projection)
