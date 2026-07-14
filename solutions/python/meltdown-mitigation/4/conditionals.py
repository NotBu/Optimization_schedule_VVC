"""Functions to prevent a nuclear meltdown."""


def is_criticality_balanced(temperature, neutrons_emitted):
    """Verify criticality is balanced."""
    return temperature < 800 and neutrons_emitted > 500 and (temperature * neutrons_emitted) < 500000
    
def reactor_efficiency(voltage, current, theoretical_max_power):
    """Assess reactor efficiency zone."""
    generated_power = voltage * current
    value = (generated_power/theoretical_max_power)*100
    if value >= 80 :
        return "green"
    if value >= 60 :
        return "orange"
    if value >= 30 :
        return "red"
        
    return "black"
        
def fail_safe(temperature, neutrons_produced_per_second, threshold):
    """Assess and return status code for the reactor."""
    product = temperature * neutrons_produced_per_second
    if product < 0.9 * threshold :
        return "LOW"
    elif 0.9 * threshold < product < 1.1 * threshold:
        return "NORMAL"
        
    return "DANGER"