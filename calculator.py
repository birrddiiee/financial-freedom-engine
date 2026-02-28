import pandas as pd
import taxes

def get_actual_return(cash, fd, fixed_income, arbitrage, gold, equity, sip_corpus, epf, 
                      r_cash, r_fd, r_fixed, r_arb, r_gold, r_eq, r_sip, r_epf, 
                      safe_retire_mode, curr_age, target_retire_age):
    total = cash + fd + fixed_income + arbitrage + gold + equity + sip_corpus + epf
    if total <= 0: 
        return r_fixed if (safe_retire_mode and curr_age >= target_retire_age) else r_eq
    return (cash*r_cash + fd*r_fd + fixed_income*r_fixed + arbitrage*r_arb + 
            gold*r_gold + equity*r_eq + sip_corpus*r_sip + epf*r_epf) / total

def simulate_survival(data, extra_sip, test_retire_age):
    age = data['age']
    retire_mode = data.get('retire_mode', 'off') 
    
    cash, fd, epf = data['cash'], data['fd'], data['epf']
    equity = data['mutual_funds'] + data['stocks']
    gold, arbitrage, fixed_income = data.get('gold', 0), data.get('arbitrage', 0), data.get('fixed_income', 0)
    
    r_cash, r_eq = data['rate_savings'], data['rate_equity']
    r_sip = data.get('rate_new_sip', r_eq) 
    r_epf, r_gold, r_arb = data['rate_epf'], data.get('rate_gold', 0.08), data.get('rate_arbitrage', 0.07)
    gross_fd_rate = data['rate_fd_gross'] 
    
    monthly_pf = data['monthly_pf']
    annual_sip = (data['current_sip'] + extra_sip) * 12
    step_up = data['step_up']
    
    curr_exp = data['living_expense'] * 12
    curr_rent = data['rent'] * 12
    inflation = data['inflation']
    rent_inflation = data['rent_inflation']
    house_cost = data['house_cost']
    housing_goal = data['housing_goal']
    
    sip_corpus = 0.0
    
    for yr in range(100 - age + 1):
        current_age = age + yr
        annual_need = curr_exp + (curr_rent if housing_goal == "Rent Forever" else 0)
        
        # 🛡️ RETIREMENT PORTFOLIO SHIFT
        if current_age == test_retire_age:
            total_wealth = cash + fd + epf + equity + gold + arbitrage + fixed_income + sip_corpus
            if retire_mode == "100_fd":
                fd = total_wealth
                cash = epf = equity = gold = arbitrage = fixed_income = sip_corpus = 0
            elif retire_mode == "dynamic":
                eq_alloc = data.get('equity_alloc', 0.4)
                fd = total_wealth * (1.0 - eq_alloc)
                equity = total_wealth * eq_alloc
                cash = epf = gold = arbitrage = fixed_income = sip_corpus = 0

        # ACCUMULATION 
        if current_age < test_retire_age:
            epf += (epf * r_epf) + (monthly_pf * 12)
            sip_corpus += (sip_corpus * r_sip) + annual_sip
            annual_sip *= (1 + step_up)
            
            cash += cash * r_cash
            fd += fd * (gross_fd_rate * 0.7) 
            fixed_income += fixed_income * (gross_fd_rate * 0.7)
            arbitrage += arbitrage * r_arb
            gold += gold * r_gold
            equity += equity * r_eq
            
        # DECUMULATION
        else:
            outflow = annual_need
            if housing_goal == "Buy a Home" and current_age == test_retire_age:
                outflow += house_cost * ((1+inflation)**yr)
            
            rem = outflow
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
            
            if rem > 0.01:
                return False 
            
            fd_gross_interest = fd * gross_fd_rate
            tax_amount = taxes.calculate_india_tax(fd_gross_interest)
            fd_net_interest = fd_gross_interest - tax_amount
            
            cash += cash * r_cash
            fd += fd_net_interest
            fixed_income += fixed_income * (gross_fd_rate * 0.7)
            arbitrage += arbitrage * r_arb
            gold += gold * r_gold
            equity += equity * r_eq
            sip_corpus += sip_corpus * r_sip
            epf += epf * r_epf
            
        if current_age == 100:
            terminal_target = annual_need * 1.1
            final_wealth = cash + fd + epf + equity + gold + arbitrage + fixed_income + sip_corpus
            return final_wealth >= terminal_target
            
        curr_exp *= (1 + inflation)
        curr_rent *= (1 + rent_inflation)
        
    return True

def calculate_true_fi_age(data):
    age = data['age']
    for test_age in range(age, 100):
        if simulate_survival(data, 0.0, test_age):
            return test_age
    return 100

def solve_extra_sip_needed(data):
    desired_age = data['retire_age']
    if desired_age <= data['age']: return 0.0
    if simulate_survival(data, 0.0, desired_age): return 0.0 
        
    low, high = 0.0, 10000000.0 
    best = high
    for _ in range(60): 
        mid = (low + high) / 2
        if simulate_survival(data, mid, desired_age):
            best = mid
            high = mid
        else:
            low = mid
    return round(best, 2)

def find_optimal_allocation(data):
    """
    Sweeps through Equity allocations (10% to 80%) to find the absolute mathematically safest 
    portfolio that either requires ZERO extra SIP, or minimizes the extra SIP needed.
    """
    best_eq = 0.5 
    lowest_sip = float('inf')
    
    for eq in range(10, 85, 5):
        eq_pct = eq / 100.0
        test_data = data.copy()
        test_data['retire_mode'] = 'dynamic'
        test_data['equity_alloc'] = eq_pct
        
        req_sip = solve_extra_sip_needed(test_data)
        
        if req_sip == 0:
            return eq_pct # Found the safest portfolio that guarantees survival
        
        if req_sip < lowest_sip:
            lowest_sip = req_sip
            best_eq = eq_pct
            
    return best_eq

def generate_forecast(data):
    age = data['age']
    target_retire_age = data['retire_age']
    retire_mode = data.get('retire_mode', 'off')
    
    cash, fd, epf = data['cash'], data['fd'], data['epf']
    equity = data['mutual_funds'] + data['stocks']
    gold, arbitrage, fixed_income = data.get('gold', 0), data.get('arbitrage', 0), data.get('fixed_income', 0)
    
    r_cash, r_eq = data['rate_savings'], data['rate_equity']
    r_sip = data.get('rate_new_sip', r_eq) 
    r_epf, r_gold, r_arb = data['rate_epf'], data.get('rate_gold', 0.08), data.get('rate_arbitrage', 0.07)
    gross_fd_rate = data['rate_fd_gross']
    
    monthly_pf = data['monthly_pf']
    annual_sip = data['current_sip'] * 12
    step_up = data['step_up']
    
    curr_exp = data['living_expense'] * 12
    curr_rent = data['rent'] * 12
    inflation = data['inflation']
    rent_inflation = data['rent_inflation']
    house_cost = data['house_cost']
    housing_goal = data['housing_goal']
    
    sip_corpus = 0.0
    
    raw_wealth = []
    raw_expenses = []
    raw_outflows = []
    raw_returns = []
    
    for yr in range(100 - age + 1):
        current_age = age + yr
        annual_need = curr_exp + (curr_rent if housing_goal == "Rent Forever" else 0)
        raw_expenses.append(annual_need)
        
        if current_age == target_retire_age:
            total_wealth = cash + fd + epf + equity + gold + arbitrage + fixed_income + sip_corpus
            if retire_mode == "100_fd":
                fd = total_wealth
                cash = epf = equity = gold = arbitrage = fixed_income = sip_corpus = 0
            elif retire_mode == "dynamic":
                eq_alloc = data.get('equity_alloc', 0.4)
                fd = total_wealth * (1.0 - eq_alloc)
                equity = total_wealth * eq_alloc
                cash = epf = gold = arbitrage = fixed_income = sip_corpus = 0

        start_wealth = cash + fd + epf + equity + gold + arbitrage + fixed_income + sip_corpus
        raw_wealth.append(start_wealth)
        
        if current_age < target_retire_age:
            raw_outflows.append(0)
            epf += (epf * r_epf) + (monthly_pf * 12)
            sip_corpus += (sip_corpus * r_sip) + annual_sip
            annual_sip *= (1 + step_up)
            
            cash += cash * r_cash
            fd += fd * (gross_fd_rate * 0.7)
            fixed_income += fixed_income * (gross_fd_rate * 0.7)
            arbitrage += arbitrage * r_arb
            gold += gold * r_gold
            equity += equity * r_eq
            
            total_end = cash + fd + epf + equity + gold + arbitrage + fixed_income + sip_corpus
            eff_return = ((total_end - annual_sip - (monthly_pf*12)) / start_wealth) - 1 if start_wealth > 0 else r_eq
            raw_returns.append(eff_return)
            
        else:
            outflow = annual_need
            if housing_goal == "Buy a Home" and current_age == target_retire_age:
                outflow += house_cost * ((1+inflation)**yr)
            raw_outflows.append(outflow)
            
            rem = outflow
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
            
            fd_gross_interest = fd * gross_fd_rate
            tax_amount = taxes.calculate_india_tax(fd_gross_interest)
            fd_net_interest = fd_gross_interest - tax_amount
            
            cash += cash * r_cash
            fd += fd_net_interest
            fixed_income += fixed_income * (gross_fd_rate * 0.7)
            arbitrage += arbitrage * r_arb
            gold += gold * r_gold
            equity += equity * r_eq
            sip_corpus += sip_corpus * r_sip
            epf += epf * r_epf
            
            total_end = cash + fd + epf + equity + gold + arbitrage + fixed_income + sip_corpus
            
            # --- THE BUG FIX: Calculate effective return on the INVESTED capital, ignoring the outflow ---
            invested_capital = start_wealth - outflow
            
            if invested_capital > 0:
                eff_return = (total_end / invested_capital) - 1
            else:
                eff_return = (fd_net_interest/fd if fd > 0 else r_eq)
                
            raw_returns.append(max(0.0001, eff_return))

        curr_exp *= (1 + inflation)
        curr_rent *= (1 + rent_inflation)
        
    targets = [0.0] * len(raw_wealth)
    targets[-1] = raw_expenses[-1] * 1.1 
    
    for i in range(len(raw_wealth)-2, -1, -1):
        curr_age = age + i
        if curr_age >= target_retire_age:
            targets[i] = (targets[i+1] / (1 + raw_returns[i])) + raw_outflows[i]
            
    retire_idx = max(0, target_retire_age - age)
    target_at_retire = targets[retire_idx] if retire_idx < len(targets) else 0
    for i in range(retire_idx):
        if i < len(targets):
            targets[i] = target_at_retire

    forecast = []
    for i in range(len(raw_wealth)):
        curr_age = age + i
        forecast.append({
            "Age": curr_age,
            "Projected Wealth": raw_wealth[i],
            "Required Target": targets[i],
            "Annual Expense": raw_outflows[i] if curr_age >= target_retire_age else raw_expenses[i],
            "Gap": raw_wealth[i] - targets[i]
        })
        
    return pd.DataFrame(forecast)