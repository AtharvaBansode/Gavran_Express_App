from ..models import DeliverySetting

def calculate_delivery_charge(weight,distance):
    setting = DeliverySetting.objects.first()

    if not setting:
        return {
            "charge": 25,
            "vehicle": "Scooter"
        }
    
    # Scooter
    if weight <= setting.scooter_weight_limit:
        charge = distance * setting.scooter_rate_per_km
        vehicle = "Scooter"

    # Ricshaw
    elif weight <= setting.rickshaw_weight_limit:
        charge = distance * setting.rickshaw_rate_per_km
        vehicle = "Rickshaw"

    # Tempo
    else:
        charge = distance * setting.tempo_rate_per_km
        vehicle = "Tempo"

    if charge < setting.minimum_delivery_charge:
        charge = setting.minimum_delivery_charge
    
    return {
        "charge": round(charge,2),
        "vehicle": vehicle
    }

