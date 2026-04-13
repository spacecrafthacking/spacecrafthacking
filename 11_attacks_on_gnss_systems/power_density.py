import math

def power_density(transmit_power, distance):
    """Calculate power density in dBm/m²."""
    # Calculate the power density in Watts per square meter
    density = transmit_power / (4 * math.pi * distance ** 2)
    density_dbm = 10 * math.log10(density * 1000)  # Convert Watts to dBm
    return density_dbm

# Constants
TRANSMITTER = 1  # Transmitter power in Watts
DISTANCES = [1000, 15]  # Distance in meters

# Compute and print the power density
for d in DISTANCES:
    p_d = power_density(TRANSMITTER, d)
    print(f"Power Density of {TRANSMITTER} W at {d} m: {p_d:.2f} dBm/m²")

# Constants
TRANSMITTER = 1  # Jammer power in Watts

DISTANCES = [10000, 1000]  # Distance in meters
ANTENNA_AREA = 0.0072  # Effective receiver aperture in m²
RECEIVED_SIGNAL = -130  # Received GNSS signal power in dBm

for d in DISTANCES:
    # Jammer power density in dBm/m²
    jammer_density_dbm_m2 = power_density(TRANSMITTER, d)
    # Received jammer power = density + 10*log10(area)
    jammer_received_dbm = jammer_density_dbm_m2 + 10 * math.log10(ANTENNA_AREA)
    # Calculate the J/S ratio
    js_ratio_db = jammer_received_dbm - RECEIVED_SIGNAL

    print(f"J/S of {TRANSMITTER} W at {d} m: {js_ratio_db:.2f} dB")
