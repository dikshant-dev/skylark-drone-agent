import pandas as pd
from datetime import datetime

def parse_date(d):
    try:
        return datetime.strptime(str(d).strip(), "%Y-%m-%d")
    except:
        return None

def dates_overlap(s1, e1, s2, e2):
    """Check if two date ranges overlap"""
    return s1 <= e2 and s2 <= e1

def check_all_conflicts(pilot, drone, mission, all_missions_df):
    """
    Run all conflict checks for a pilot+drone+mission combo.
    Returns a list of conflict dicts: {type, severity, message}
    """
    alerts = []

    mission_start = parse_date(mission.get('start_date'))
    mission_end   = parse_date(mission.get('end_date'))
    required_certs = [c.strip() for c in str(mission.get('required_certs', '')).split(',')]
    required_skills = [s.strip() for s in str(mission.get('required_skills', '')).split(',')]
    weather = str(mission.get('weather_forecast', '')).strip()
    budget  = float(str(mission.get('mission_budget_inr', 0)).replace(',', '') or 0)
    mission_location = str(mission.get('location', '')).strip()

    # ── 1. PILOT DOUBLE-BOOKING ───────────────────────────────────────────────
    if pilot is not None and all_missions_df is not None:
        pilot_assignment = str(pilot.get('current_assignment', '')).strip()
        if pilot_assignment and pilot_assignment != '-':
            # find that mission's dates
            matched = all_missions_df[all_missions_df['project_id'] == pilot_assignment]
            for _, m in matched.iterrows():
                ms = parse_date(m.get('start_date'))
                me = parse_date(m.get('end_date'))
                if ms and me and mission_start and mission_end:
                    if dates_overlap(mission_start, mission_end, ms, me):
                        alerts.append({
                            "type": "DOUBLE_BOOKING",
                            "severity": "critical",
                            "message": f"⚠ Pilot {pilot.get('name')} is already assigned to {pilot_assignment} "
                                       f"({m['start_date']} → {m['end_date']}), which overlaps this mission."
                        })

    # ── 2. CERTIFICATION MISMATCH ─────────────────────────────────────────────
    if pilot is not None:
        pilot_certs = [c.strip() for c in str(pilot.get('certifications', '')).split(',')]
        missing_certs = [c for c in required_certs if c and c not in pilot_certs]
        if missing_certs:
            alerts.append({
                "type": "CERT_MISMATCH",
                "severity": "critical",
                "message": f"⚠ Pilot {pilot.get('name')} lacks required certification(s): {', '.join(missing_certs)}."
            })

    # ── 3. SKILL MISMATCH ─────────────────────────────────────────────────────
    if pilot is not None:
        pilot_skills = [s.strip() for s in str(pilot.get('skills', '')).split(',')]
        missing_skills = [s for s in required_skills if s and s not in pilot_skills]
        if missing_skills:
            alerts.append({
                "type": "SKILL_MISMATCH",
                "severity": "warning",
                "message": f"⚠ Pilot {pilot.get('name')} lacks required skill(s): {', '.join(missing_skills)}."
            })

    # ── 4. PILOT AVAILABILITY ─────────────────────────────────────────────────
    if pilot is not None:
        status = str(pilot.get('status', '')).strip()
        if status == 'On Leave':
            alerts.append({
                "type": "PILOT_UNAVAILABLE",
                "severity": "critical",
                "message": f"⚠ Pilot {pilot.get('name')} is currently On Leave."
            })
        elif status == 'Unavailable':
            alerts.append({
                "type": "PILOT_UNAVAILABLE",
                "severity": "critical",
                "message": f"⚠ Pilot {pilot.get('name')} is marked Unavailable."
            })

    # ── 5. BUDGET OVERRUN ─────────────────────────────────────────────────────
    if pilot is not None and mission_start and mission_end:
        days = (mission_end - mission_start).days + 1
        daily_rate = float(str(pilot.get('daily_rate_inr', 0)).replace(',', '') or 0)
        total_cost = daily_rate * days
        if budget > 0 and total_cost > budget:
            alerts.append({
                "type": "BUDGET_OVERRUN",
                "severity": "warning",
                "message": f"⚠ Pilot cost ₹{total_cost:,.0f} (₹{daily_rate}/day × {days} days) "
                           f"exceeds mission budget of ₹{budget:,.0f}."
            })

    # ── 6. DRONE IN MAINTENANCE ───────────────────────────────────────────────
    if drone is not None:
        drone_status = str(drone.get('status', '')).strip()
        if drone_status == 'Maintenance':
            alerts.append({
                "type": "DRONE_MAINTENANCE",
                "severity": "critical",
                "message": f"⚠ Drone {drone.get('drone_id')} ({drone.get('model')}) is currently in Maintenance."
            })

    # ── 7. WEATHER RISK ───────────────────────────────────────────────────────
    if drone is not None:
        weather_resistance = str(drone.get('weather_resistance', '')).strip()
        # Rainy missions need IP43 or better
        if 'Rain' in weather or 'Rainy' in weather:
            if 'IP43' not in weather_resistance and 'IP' not in weather_resistance:
                alerts.append({
                    "type": "WEATHER_RISK",
                    "severity": "critical",
                    "message": f"⚠ Mission weather is '{weather}' but Drone {drone.get('drone_id')} "
                               f"has no rain protection ({weather_resistance}). Risk of damage!"
                })

    # ── 8. LOCATION MISMATCH (pilot ↔ mission) ────────────────────────────────
    if pilot is not None:
        pilot_location = str(pilot.get('location', '')).strip()
        if pilot_location.lower() != mission_location.lower():
            alerts.append({
                "type": "LOCATION_MISMATCH",
                "severity": "warning",
                "message": f"⚠ Pilot {pilot.get('name')} is in {pilot_location} but mission is in {mission_location}."
            })

    # ── 9. LOCATION MISMATCH (drone ↔ mission) ───────────────────────────────
    if drone is not None:
        drone_location = str(drone.get('location', '')).strip()
        if drone_location.lower() != mission_location.lower():
            alerts.append({
                "type": "DRONE_LOCATION_MISMATCH",
                "severity": "warning",
                "message": f"⚠ Drone {drone.get('drone_id')} is in {drone_location} but mission is in {mission_location}."
            })

    return alerts


def format_alerts(alerts):
    """Format a list of alerts into a readable string block."""
    if not alerts:
        return "✅ No conflicts detected. All clear!"
    
    critical = [a for a in alerts if a['severity'] == 'critical']
    warnings  = [a for a in alerts if a['severity'] == 'warning']
    
    lines = []
    if critical:
        lines.append("🔴 CRITICAL CONFLICTS:")
        for a in critical:
            lines.append(f"  {a['message']}")
    if warnings:
        lines.append("🟡 WARNINGS:")
        for a in warnings:
            lines.append(f"  {a['message']}")
    
    return "\n".join(lines)
