# custom_tools_globalKyc.py

from dotenv import load_dotenv
import os

import datetime
import requests

load_dotenv()
NINJAS_API_KEY = os.getenv("NINJAS_API_KEY")

def categorize_zone(city: str, country: str) -> str:
    """
    Categorizes a city as 'URBAN' or 'RURAL' based on population.

    Args:
    - city (str): Name of the city.
    - country (str): Country code. For example: DO for Dominican Republic, AR for Argentina and GB for the UK.

    Returns:
    - str: 'URBAN' if population > 50,000, else 'RURAL'.
    """
    url = 'https://api.api-ninjas.com/v1/city'
    headers = {'X-Api-Key': NINJAS_API_KEY}
    params = {
        'name': city,
        'country': country
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if data:
            print(data)
            population = data[0].get('population')
            if population is not None:
                return 'URBAN' if population > 50000 else 'RURAL'
        # No match for request
        return f"NO data is available for {city}, {country}."
    except requests.exceptions.RequestException as e:
        return f"API request error: {e}"

def design_leasing_offer(
    customer_id: str,
    birthdate: str,
    income: float,
    city: str,
    vehicle_year: int
) -> dict:
    """
    Designs a leasing offer based on customer and vehicle information.

    Parameters:
    - customer_id (str): Can be either a license-plate, an id-number or a name.
    - birthdate (str): Customer's date of birth in 'DD-MM-YYYY' format.
    - income (float): Customer's monthly income.
    - city (str): City of residence.
    - vehicle_year (int): The year the customer's current vehicle was manufactured.

    Returns:
    - dict: A dictionary containing the leasing offer details or ineligibility reason.
    """
    current_year = datetime.datetime.now().year
    vehicle_age = current_year - vehicle_year

    birthdate = datetime.datetime.strptime(birthdate, "%d-%m-%Y")
    today = datetime.datetime.today()
    customer_age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    
    # Eligibility Check
    if vehicle_age <= 5:
        return {
            "customer_id": customer_id,
            "eligible": False,
            "reason": "vehicle is less than or equal to 5 years old."
        }

    if customer_age < 18 or customer_age > 65:
        return {
            "customer_id": customer_id,
            "eligible": False,
            "reason": "customer age must be between 18 and 65."
        }
    
    # Income Segmentation
    if income < 10000:
        income_segment = "low"
        base_rate = 0.10
    elif 10000 <= income < 100000:
        income_segment = "medium"
        base_rate = 0.20
    else:
        income_segment = "high"
        base_rate = 0.30

    # Zone Classification
    zone_type = categorize_zone(city, "DO").lower()
    if zone_type == "urban":
        base_rate += 0.05  # 5% extra-charge for urban areas
    elif zone_type == "rural":
        pass
    else: zone_type = "unknown"

    # Monthly Payment Calculation
    monthly_payment = base_rate * income

    # Contract Term Determination
    if income_segment == "low":
        contract_term_years = 2
    elif income_segment == "medium":
        contract_term_years = 3
    else:
        contract_term_years = 5

    # Residual Value Estimation (Assuming 10% of original value per year of age)
    # Note: In a real scenario, this should be based on actual depreciation data.
    base_value = 1_000_000
    residual_value = max(0, 1 - (vehicle_age * 0.10)) * base_value

    return {
        "customer_id": customer_id,
        "eligible": True,
        "customer_age": customer_age,
        "vehicle_age": vehicle_age,
        "income_segment": income_segment,
        "zone_type": zone_type,
        "monthly_payment": round(monthly_payment, 2),
        "contract_term_years": contract_term_years,
        "residual_value": round(residual_value, 2),
        "purchase_option": True
    }