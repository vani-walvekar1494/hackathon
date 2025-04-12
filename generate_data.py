import pandas as pd
import numpy as np

np.random.seed(42)

n_samples = 1000
marketing_spend = np.random.normal(200000, 50000, n_samples)
rnd_investment = np.random.normal(150000, 40000, n_samples)
employee_count = np.random.randint(50, 500, n_samples)
operational_costs = np.random.normal(300000, 60000, n_samples)
customer_satisfaction = np.random.uniform(1, 5, n_samples)
market_share = np.random.uniform(0.01, 0.2, n_samples)

revenue = (
    marketing_spend * 0.5 +
    rnd_investment * 0.3 +
    employee_count * 1000 +
    customer_satisfaction * 20000 +
    market_share * 1e6 -
    operational_costs * 0.7 +
    np.random.normal(0, 10000, n_samples)
)

data = pd.DataFrame({
    'Marketing Spend': marketing_spend,
    'R&D Investment': rnd_investment,
    'Employee Count': employee_count,
    'Operational Costs': operational_costs,
    'Customer Satisfaction': customer_satisfaction,
    'Market Share': market_share,
    'Revenue': revenue
})

data.to_csv('synthetic_company_data.csv', index=False)
print("Synthetic dataset generated and saved.")
