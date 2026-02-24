import pandas as pd

def get_actual_return(cash, fd, fixed_income, arbitrage, gold, equity, sip_corpus, epf,
                      r_cash, r_fd, r_fixed, r_arb, r_gold, r_eq, r_sip, r_epf):
    """Calculates the exact weighted average return of the current portfolio."""
    total = cash + fd + fixed_income + arbitrage + gold + equity + sip_corpus + epf
    if total <= 0:
        return r_eq # Fallback assumption if no assets exist yet
    return (cash*r_cash + fd*r_fd + fixed_income*r_fixed + arbitrage*r_arb + 
            gold*r_gold + equity*r_eq + sip_corpus*r_sip + epf*r_epf) / total

def calculate_true_fi_age(data):
    age = data['age']
    living_expense = data['living_expense']
    rent = data['rent']
    sip = data['current_sip']
    step_up = data['step_up']
    inflation = data['inflation']
    rent_inflation = data['rent_inflation']
    swr = data['swr']
    house_cost = data['house_cost']
    housing_goal = data['housing_goal']
    monthly_pf = data['monthly_pf']
    dwz_mode = data.get('dwz_mode', False)
    
    cash, fd, epf = data['cash'], data['fd'], data['epf']
    equity = data['mutual_funds'] + data['stocks']
    gold, arbitrage, fixed_income = data.get('gold', 0), data.get('arbitrage', 0), data.get('fixed_income', 0)
    
    r_cash, r_fd, r_epf, r_eq = data['rate_savings'], data['rate_fd'], data['rate_epf'], data['rate_equity']
    r_sip = data.get('rate_new_sip', r_eq) 
    r_gold, r_arb, r_fixed = data.get('rate_gold', 0.08), data.get('rate_arbitrage', 0.07), data.get('rate_fixed', 0.07)
    
    current_expense = living_expense * 12
    current_rent = rent * 12
    sip_corpus = 0.0
    annual_sip = sip * 12
    
    for yr in range(120 - age + 1):
        current_age = age + yr
        total_wealth = cash + fd + epf + equity + gold + arbitrage + fixed_income + sip_corpus
        
        # Calculate the exact return of the portfolio this year
        actual_return = get_actual_return(cash, fd, fixed_income, arbitrage, gold, equity, sip_corpus, epf,
                                          r_cash, r_fd, r_fixed, r_arb, r_gold, r_eq, r_sip, r_epf)
        
        baseline_annual_need = current_expense
        if housing_goal == "Rent Forever":
            baseline_annual_need += current_rent
            
        years_remaining = max(0, 120 - current_age)
        
        if dwz_mode:
            if abs(actual_return - inflation) < 0.0001:
                current_multiple = years_remaining
            else:
                # True Present Value of growing annuity due
                ratio = (1 + inflation) / (1 + actual_return)
                current_multiple = ((1 - (ratio ** years_remaining)) / (actual_return - inflation)) * (1 + actual_return)
        else:
            max_multiple = 1 / swr
            current_multiple = min(max_multiple, years_remaining)
            
        req_corpus = baseline_annual_need * current_multiple
        if housing_goal == "Buy a Home":
            req_corpus += house_cost
            
        if total_wealth >= req_corpus:
            return current_age
            
        epf += (epf * r_epf) + (monthly_pf * 12)
        sip_corpus += (sip_corpus * r_sip) + annual_sip
        annual_sip *= (1 + step_up) 
        
        cash += cash * r_cash
        fd += fd * r_fd
        fixed_income += fixed_income * r_fixed
        arbitrage += arbitrage * r_arb
        gold += gold * r_gold
        equity += equity * r_eq
        
        current_expense *= (1 + inflation)
        current_rent *= (1 + rent_inflation)
        if housing_goal == "Buy a Home":
            house_cost *= (1 + inflation)
            
    return 120

def generate_forecast(data):
    age = data['age']
    desired_retire_age = data['retire_age']
    
    true_fi_age = calculate_true_fi_age(data)
    effective_retire_age = max(desired_retire_age, true_fi_age)
    
    living_expense = data['living_expense']
    rent = data['rent']
    sip = data['current_sip']
    step_up = data['step_up']
    inflation = data['inflation']
    rent_inflation = data['rent_inflation']
    swr = data['swr']
    house_cost = data['house_cost']
    housing_goal = data['housing_goal']
    monthly_pf = data['monthly_pf']
    dwz_mode = data.get('dwz_mode', False)
    
    cash, fd, epf = data['cash'], data['fd'], data['epf']
    equity = data['mutual_funds'] + data['stocks']
    gold, arbitrage, fixed_income = data.get('gold', 0), data.get('arbitrage', 0), data.get('fixed_income', 0)
    
    r_cash, r_fd, r_epf, r_eq = data['rate_savings'], data['rate_fd'], data['rate_epf'], data['rate_equity']
    r_sip = data.get('rate_new_sip', r_eq) 
    r_gold, r_arb, r_fixed = data.get('rate_gold', 0.08), data.get('rate_arbitrage', 0.07), data.get('rate_fixed', 0.07)
    
    forecast = []
    current_expense = living_expense * 12
    current_rent = rent * 12
    
    sip_corpus = 0.0
    annual_sip = sip * 12
    
    for yr in range(120 - age + 1):
        current_age = age + yr
        
        total_wealth = cash + fd + epf + equity + gold + arbitrage + fixed_income + sip_corpus
        
        actual_return = get_actual_return(cash, fd, fixed_income, arbitrage, gold, equity, sip_corpus, epf,
                                          r_cash, r_fd, r_fixed, r_arb, r_gold, r_eq, r_sip, r_epf)
        
        baseline_annual_need = current_expense
        if housing_goal == "Rent Forever":
            baseline_annual_need += current_rent
            
        years_remaining = max(0, 120 - current_age)
        
        if dwz_mode:
            if abs(actual_return - inflation) < 0.0001:
                current_multiple = years_remaining
            else:
                ratio = (1 + inflation) / (1 + actual_return)
                current_multiple = ((1 - (ratio ** years_remaining)) / (actual_return - inflation)) * (1 + actual_return)
        else:
            max_multiple = 1 / swr
            current_multiple = min(max_multiple, years_remaining)
        
        req_corpus = baseline_annual_need * current_multiple
        
        if housing_goal == "Buy a Home" and current_age <= effective_retire_age:
            req_corpus += house_cost
            
        # 🚀 PERFECTED DYNAMIC DECUMULATION
        actual_outflow = baseline_annual_need
        if dwz_mode and current_age >= effective_retire_age:
            if current_multiple > 0.001:
                dwz_dynamic_spend = total_wealth / current_multiple
                actual_outflow = max(baseline_annual_need, dwz_dynamic_spend)
            else:
                actual_outflow = total_wealth # Final year dump exactly at 120
        
        forecast.append({
            "Age": current_age,
            "Projected Wealth": total_wealth,
            "Required Corpus": req_corpus,
            "Annual Expense": actual_outflow,
            "Gap": total_wealth - req_corpus
        })
        
        if current_age == 120: 
            break
        
        if current_age < effective_retire_age:
            epf += (epf * r_epf) + (monthly_pf * 12)
            sip_corpus += (sip_corpus * r_sip) + annual_sip
            annual_sip *= (1 + step_up) 
            
            cash += cash * r_cash
            fd += fd * r_fd
            fixed_income += fixed_income * r_fixed
            arbitrage += arbitrage * r_arb
            gold += gold * r_gold
            equity += equity * r_eq
        else:
            total_outflow = actual_outflow
            if housing_goal == "Buy a Home" and current_age == effective_retire_age:
                total_outflow += house_cost 
                
            # Safely drain sequentially; prevents negative math
            rem = total_outflow
            
            if cash >= rem: cash -= rem; rem = 0
            elif cash > 0: rem -= cash; cash = 0
            
            if fd >= rem: fd -= rem; rem = 0
            elif fd > 0: rem -= fd; fd = 0
            
            if fixed_income >= rem: fixed_income -= rem; rem = 0
            elif fixed_income > 0: rem -= fixed_income; fixed_income = 0
            
            if arbitrage >= rem: arbitrage -= rem; rem = 0
            elif arbitrage > 0: rem -= arbitrage; arbitrage = 0
            
            if gold >= rem: gold -= rem; rem = 0
            elif gold > 0: rem -= gold; gold = 0
            
            if sip_corpus >= rem: sip_corpus -= rem; rem = 0
            elif sip_corpus > 0: rem -= sip_corpus; sip_corpus = 0
            
            if equity >= rem: equity -= rem; rem = 0
            elif equity > 0: rem -= equity; equity = 0
            
            if epf >= rem: epf -= rem; rem = 0
            elif epf > 0: rem -= epf; epf = 0
            
            cash += cash * r_cash
            fd += fd * r_fd
            fixed_income += fixed_income * r_fixed
            arbitrage += arbitrage * r_arb
            gold += gold * r_gold
            equity += equity * r_eq
            sip_corpus += sip_corpus * r_sip
            epf += epf * r_epf
            
        current_expense *= (1 + inflation)
        current_rent *= (1 + rent_inflation)
        if housing_goal == "Buy a Home" and current_age < effective_retire_age:
            house_cost *= (1 + inflation)
            
    return pd.DataFrame(forecast)

def solve_extra_sip_needed(gap, years, rate, step_up):
    if gap <= 0 or years <= 0: return 0.0
    low, high = 0.0, gap
    best = high
    for _ in range(50): 
        mid = (low + high) / 2
        fv = 0
        annual_sip = mid * 12
        for y in range(years):
            fv = (fv + annual_sip) * (1 + rate)
            annual_sip *= (1 + step_up)
        if fv >= gap:
            best = mid
            high = mid
        else:
            low = mid
    return round(best / 12, 2)