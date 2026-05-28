import math

FALL_ACCEL_THRESHOLD = 2.0   # g-force above normal gravity
FALL_GYRO_THRESHOLD  = 200   # deg/sec angular velocity

def detect_fall(ax: float, ay: float, az: float,
                gx: float, gy: float, gz: float) -> tuple[bool, str]:
    """
    Fall detection using magnitude of acceleration vector.
    A fall produces a sudden large acceleration followed by near-zero.
    """
    if ax is None:
        return False, ""

    # total acceleration magnitude
    accel_mag = math.sqrt(ax**2 + ay**2 + az**2)
    gyro_mag  = math.sqrt(gx**2 + gy**2 + gz**2)

    # free-fall: accel drops near 0 (patient airborne)
    free_fall = accel_mag < 0.3

    # impact: sudden large acceleration spike
    impact = accel_mag > FALL_ACCEL_THRESHOLD

    # high rotation (tumbling)
    high_rotation = gyro_mag > FALL_GYRO_THRESHOLD

    if impact or (free_fall and high_rotation):
        reason = (f"Fall detected — acceleration: {accel_mag:.2f}g, "
                  f"rotation: {gyro_mag:.1f} deg/s")
        return True, reason

    return False, ""

def classify_activity_motion(bpm: float,
                              ax: float, ay: float, az: float) -> str:
    """combine BPM + motion for better activity classification"""
    if ax is None:
        # fallback to BPM-only
        if bpm < 60:  return "sleeping"
        if bpm < 75:  return "resting"
        if bpm < 100: return "active"
        return "exercising"

    accel_mag = math.sqrt(ax**2 + ay**2 + az**2)

    if accel_mag < 0.1 and bpm < 65:  return "sleeping"
    if accel_mag < 0.3 and bpm < 80:  return "resting"
    if accel_mag > 1.5 or bpm > 100:  return "exercising"
    return "active"