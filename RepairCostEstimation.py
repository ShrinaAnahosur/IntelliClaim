import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

def preprocess_insurance_data(file_path):
    # Load dataset
    df = pd.read_csv(file_path)

    # Drop unnecessary columns
    df.drop(columns=["ID", "BIRTH"], inplace=True)

    # Convert currency fields to numeric
    currency_columns = ["INCOME", "HOME_VAL", "BLUEBOOK", "OLDCLAIM", "CLM_AMT"]
    for col in currency_columns:
        df[col] = df[col].replace({'\\$': '', ',' : ''}, regex=True).astype(float)

    # Fill missing values
    num_imputer = SimpleImputer(strategy='median')  # For numerical columns
    cat_imputer = SimpleImputer(strategy='most_frequent')  # For categorical columns

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    categorical_cols = df.select_dtypes(include=["object"]).columns

    df[numeric_cols] = num_imputer.fit_transform(df[numeric_cols])
    df[categorical_cols] = cat_imputer.fit_transform(df[categorical_cols])

    # One-hot encode categorical variables
    df = pd.get_dummies(df, columns=categorical_cols, drop_first=True)

    # Scale numerical features
    scaler = StandardScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

    return df, scaler

def train_repair_cost_model(df):
    """Train an AI model to predict repair cost"""

    # Features used for training
    features = ["CAR_AGE", "BLUEBOOK", "OLDCLAIM", "CLM_FREQ", "CLM_AMT"]
    target = "CLM_AMT"

    # Extracting only relevant numerical features
    scaler = StandardScaler()
    df[features] = scaler.fit_transform(df[features])

    # Splitting dataset
    X_train, X_test, y_train, y_test = train_test_split(df[features], df[target], test_size=0.2, random_state=42)

    # Train model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    return model, scaler  # Return the trained model and scaler for consistent feature scaling


def estimate_labor_cost(damage_severity):
    """Estimate labor cost based on AI predictions"""
    severity_mapping = {"Minor": 1, "Moderate": 2, "Severe": 3}
    return severity_mapping[damage_severity] * np.random.uniform(50, 150)

def scrape_spare_part_price(part_name):
    """Scrape spare part price from eBay (mock function for now)"""
    url = f"https://www.ebay.com/sch/i.html?_nkw={part_name.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        prices = soup.find_all("span", class_="s-item__price")
        if prices:
            return float(prices[0].text.replace("$", "").replace(",", ""))

    return np.random.uniform(50, 500)

def calculate_total_repair_cost(model, scaler, car_age, bluebook, old_claim, clm_freq, claim_amt, damage_severity, required_parts):
    """Calculate total repair cost using AI"""

    labor_cost = estimate_labor_cost(damage_severity)
    spare_parts_cost = sum(scrape_spare_part_price(part) for part in required_parts)
    #testing=[scrape_spare_part_price(part) for part in required_parts]
    #print(testing)
    # Scale input correctly
    input_data = scaler.transform([[car_age, bluebook, old_claim, clm_freq, claim_amt]])

    predicted_cost = model.predict(input_data)[0]

    return labor_cost + spare_parts_cost + predicted_cost



# Example Usage
file_path = "/content/car_insurance_claim.csv"
df, scaler = preprocess_insurance_data(file_path)
model, scaler = train_repair_cost_model(df)

total_cost = calculate_total_repair_cost(model, scaler, 5, 12000, 1000, 2, 2500, "Moderate", ["Front Bumper", "Headlight"])
print(f"Estimated Repair Cost: ${total_cost:.2f}")

