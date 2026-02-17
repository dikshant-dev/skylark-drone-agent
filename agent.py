import os
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from conflicts import check_all_conflicts, format_alerts
from datetime import datetime

load_dotenv()

def load_data():
    pilots   = pd.read_csv("data/pilot_roster.csv")
    drones   = pd.read_csv("data/drone_fleet.csv")
    missions = pd.read_csv("data/missions.csv")
    return pilots, drones, missions

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are SkyBot, an expert AI Operations Coordinator for Skylark Drones.
You help manage drone pilots, drone fleet, and mission assignments.
You have access to pilot roster, drone fleet, and mission list data.
Be clear, concise, and professional. Use emoji warnings for alerts.
Current date: """ + datetime.now().strftime("%Y-%m-%d") + """
"""

class DroneAgent:
    def __init__(self):
        self.pilots, self.drones, self.missions = load_data()
        self.conversation_history = []
        self._try_sync_sheets()

    def _try_sync_sheets(self):
        try:
            import sheets as sh
            spreadsheet_name = os.getenv("GOOGLE_SHEET_NAME", "")
            if spreadsheet_name:
                pilots_gs = sh.read_sheet(spreadsheet_name, "Pilot Roster")
                drones_gs = sh.read_sheet(spreadsheet_name, "Drone Fleet")
                if not pilots_gs.empty:
                    self.pilots = pilots_gs
                if not drones_gs.empty:
                    self.drones = drones_gs
                print("[agent] Loaded from Google Sheets")
        except Exception as e:
            print(f"[agent] Using CSV: {e}")

    def _data_context(self):
        return f"""
=== PILOT ROSTER ===
{self.pilots.to_string(index=False)}

=== DRONE FLEET ===
{self.drones.to_string(index=False)}

=== MISSIONS ===
{self.missions.to_string(index=False)}
"""

    def _build_messages(self, user_message):
        messages = [{"role": "system", "content": SYSTEM_PROMPT + self._data_context()}]
        messages += self.conversation_history[-10:]
        messages.append({"role": "user", "content": user_message})
        return messages

    def _handle_conflict_check(self, text):
        pilot_row = drone_row = mission_row = None
        for _, p in self.pilots.iterrows():
            if p['pilot_id'].lower() in text.lower() or p['name'].lower() in text.lower():
                pilot_row = p.to_dict(); break
        for _, d in self.drones.iterrows():
            if d['drone_id'].lower() in text.lower():
                drone_row = d.to_dict(); break
        for _, m in self.missions.iterrows():
            if m['project_id'].lower() in text.lower():
                mission_row = m.to_dict(); break
        if mission_row is None:
            return None
        alerts = check_all_conflicts(pilot_row, drone_row, mission_row, self.missions)
        return format_alerts(alerts)

    def _handle_status_update(self, text):
        text_lower = text.lower()
        statuses = ['on leave', 'unavailable', 'maintenance', 'assigned', 'available']
        found_status = next((s for s in statuses if s in text_lower), None)
        if not found_status:
            return None
        for _, p in self.pilots.iterrows():
            if p['pilot_id'].lower() in text_lower or p['name'].lower() == next((w for w in text_lower.split() if w in p['name'].lower()), ''):
                self.pilots.loc[self.pilots['pilot_id'] == p['pilot_id'], 'status'] = found_status.title()
                try:
                    import sheets as sh
                    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "")
                    if sheet_name:
                        sh.update_pilot_status(sheet_name, p['pilot_id'], found_status.title())
                        return f"✅ Updated {p['name']} to **{found_status.title()}** — synced to Google Sheets."
                except:
                    pass
                return f"✅ Updated {p['name']} to **{found_status.title()}** (local)."
        for _, d in self.drones.iterrows():
            if d['drone_id'].lower() in text_lower:
                self.drones.loc[self.drones['drone_id'] == d['drone_id'], 'status'] = found_status.title()
                return f"✅ Updated Drone {d['drone_id']} to **{found_status.title()}** (local)."
        return None

    def _handle_suggest_assignment(self, text):
        mission_row = None
        for _, m in self.missions.iterrows():
            if m['project_id'].lower() in text.lower() or m['client'].lower() in text.lower():
                mission_row = m.to_dict(); break
        if mission_row is None:
            return None
        results = []
        req_skills = [s.strip() for s in str(mission_row.get('required_skills','')).split(',')]
        req_certs  = [c.strip() for c in str(mission_row.get('required_certs','')).split(',')]
        m_loc = str(mission_row.get('location','')).strip()
        available_pilots = self.pilots[self.pilots['status'] == 'Available']
        available_drones = self.drones[self.drones['status'] == 'Available']
        for _, p in available_pilots.iterrows():
            p_skills = [s.strip() for s in str(p['skills']).split(',')]
            p_certs  = [c.strip() for c in str(p['certifications']).split(',')]
            if not (all(s in p_skills for s in req_skills) and all(c in p_certs for c in req_certs)):
                continue
            loc_drones = available_drones[available_drones['location'].str.strip() == m_loc]
            if loc_drones.empty:
                loc_drones = available_drones
            for _, d in loc_drones.iterrows():
                alerts = check_all_conflicts(p.to_dict(), d.to_dict(), mission_row, self.missions)
                results.append({'pilot': p['name'], 'drone': d['drone_id'], 'alerts': alerts,
                                'critical_count': len([a for a in alerts if a['severity']=='critical'])})
        if not results:
            return f"❌ No suitable pilot found for {mission_row['project_id']}."
        results.sort(key=lambda x: x['critical_count'])
        best = results[0]
        return (f"📋 **Best Assignment for {mission_row['project_id']} ({mission_row['client']}):**\n\n"
                f"👤 Pilot: **{best['pilot']}**\n🚁 Drone: **{best['drone']}**\n\n"
                f"**Conflict Check:**\n{format_alerts(best['alerts'])}")

    def _handle_urgent_reassignment(self, text):
        text_lower = text.lower()
        for _, p in self.pilots.iterrows():
            if (p['pilot_id'].lower() in text_lower or p['name'].lower() in text_lower):
                if any(w in text_lower for w in ['urgent','reassign','replace','unavailable','emergency','sick','injured']):
                    current_proj = str(p.get('current_assignment','-')).strip()
                    if current_proj == '-' or not current_proj:
                        return f"⚠ {p['name']} has no active assignment."
                    mission_row = None
                    for _, m in self.missions.iterrows():
                        if m['project_id'] == current_proj:
                            mission_row = m.to_dict(); break
                    if not mission_row:
                        return f"⚠ Mission {current_proj} not found."
                    self.pilots.loc[self.pilots['pilot_id'] == p['pilot_id'], 'status'] = 'Unavailable'
                    suggestion = self._handle_suggest_assignment(current_proj)
                    return (f"🚨 **URGENT REASSIGNMENT**\n\n❌ {p['name']} marked Unavailable for {current_proj}\n\n"
                            + (suggestion or "⚠ No replacement found!"))
        return None

    def handle_message(self, user_message):
        text_lower = user_message.lower()

        if any(w in text_lower for w in ['update status','mark','set status','change status','as available','as unavailable','as assigned','as on leave']):
            result = self._handle_status_update(user_message)
            if result:
                self.conversation_history += [{"role":"user","content":user_message},{"role":"assistant","content":result}]
                return {"reply": result, "type": "status_update"}

        if any(w in text_lower for w in ['conflict','check','alert','warning','issue']):
            result = self._handle_conflict_check(user_message)
            if result:
                self.conversation_history += [{"role":"user","content":user_message},{"role":"assistant","content":result}]
                return {"reply": result, "type": "conflict_check"}

        if any(w in text_lower for w in ['urgent','emergency','reassign','replace','sick','injured']):
            result = self._handle_urgent_reassignment(user_message)
            if result:
                self.conversation_history += [{"role":"user","content":user_message},{"role":"assistant","content":result}]
                return {"reply": result, "type": "urgent"}

        if any(w in text_lower for w in ['suggest','recommend','assign','who should','best pilot','best drone']):
            result = self._handle_suggest_assignment(user_message)
            if result:
                self.conversation_history += [{"role":"user","content":user_message},{"role":"assistant","content":result}]
                return {"reply": result, "type": "assignment"}

        try:
            messages = self._build_messages(user_message)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=800,
                temperature=0.3
            )
            reply = response.choices[0].message.content
            self.conversation_history += [{"role":"user","content":user_message},{"role":"assistant","content":reply}]
            return {"reply": reply, "type": "general"}
        except Exception as e:
            return {"reply": f"⚠ AI error: {str(e)}", "type": "error"}

    def get_dashboard_summary(self):
        return {
            "total_pilots":     len(self.pilots),
            "available_pilots": int((self.pilots['status'] == 'Available').sum()),
            "on_leave":         int((self.pilots['status'] == 'On Leave').sum()),
            "total_drones":     len(self.drones),
            "available_drones": int((self.drones['status'] == 'Available').sum()),
            "in_maintenance":   int((self.drones['status'] == 'Maintenance').sum()),
            "total_missions":   len(self.missions),
            "urgent_missions":  int((self.missions['priority'] == 'Urgent').sum()),
        }
