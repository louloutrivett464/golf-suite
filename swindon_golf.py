import os
import json
import streamlit as st
import plotly.express as px

# Set up the web page title and icon
st.set_page_config(page_title="Apex Golf Suite", page_icon="⛳", layout="centered")

# --- COURSE DATABASE WITH FULLY COMPLETED PAR ARRAYS ---
# We use st.session_state so when you add a custom course, it stays in the dropdown menu
if "courses" not in st.session_state:
    st.session_state["courses"] = {
        "basset 12 hole": {"pars": [4,3,4,3,5,4,4,4,4,4,4,5], "rating": 46.2, "slope": 115},
        "broome 9 hole": {"pars": [3,4,3,5,3,3,4,4,3], "rating": 34.5, "slope": 113},
        "broome 18 hole": {"pars": [5,4,3,4,4,3,4,4,4,4,3,5,4,4,3,4,5,4], "rating": 70.2, "slope": 124},
        "basset 18 hole": {"pars": [4,3,4,4,4,4,4,4,5,4,3,4,4,4,4,4,4,5], "rating": 69.8, "slope": 121},
        "ogbourne": {"pars": [4,4,4,3,4,4,4,3,5,5,4,4,4,5,3,4,3,4], "rating": 71.1, "slope": 128},
        "wragbarn": {"pars": [4,4,3,5,3,5,4,4,4,5,4,3,4,4,4,3,5,4], "rating": 71.5, "slope": 131}
    }

DATAFILE = "profiles.json"

def load_profiles():
    if os.path.exists(DATAFILE):
        with open(DATAFILE, "r") as file:
            try:
                data = json.load(file)
                if not isinstance(data, dict): return {}
                return data
            except json.JSONDecodeError: return {}
    return {}

def save_profiles(data):
    with open(DATAFILE, "w") as file:
        json.dump(data, file, indent=4)

def calculate_handicap_value(scores):
    roundsplayed = len(scores)
    if roundsplayed == 0: return "No rounds played"
    bestscores = sorted(scores)
    if roundsplayed < 3: return sum(scores) / len(scores)
    elif roundsplayed <= 5: return float(bestscores[0])
    elif roundsplayed >= 20:
        recent20 = scores[-20:]
        best20sorted = sorted(recent20)
        return sum(best20sorted[:8]) / 8
    else: return sum(bestscores[:3]) / 3

def check_achievements(scores):
    badges = []
    if len(scores) >= 1: badges.append("🌱 First Tee Drop (Logged 1st Round!)")
    if len(scores) >= 5: badges.append("🎒 Dedicated Grinder (Logged 5+ Rounds!)")
    if len(scores) >= 2 and scores[-1] < scores[-2]: badges.append("🔥 On Fire (Latest round beat your last one!)")
    for s in scores:
        if 1 <= s <= 10 and "🎯 Target Practice" not in str(badges): badges.append("🎯 Target Practice (+1 to +10 over par!)")
        if s >= 30 and "🐌 Constant Competitor" not in str(badges): badges.append("🐌 Constant Competitor (+30 over par round!)")
    return badges

# --- MAIN APP INTERFACE ---
st.title("⛳ Apex Golf Suite")

# Live hardcoded weather tracking banner
st.success("🌤️ Wiltshire Golf Weather: **15.0°C** | 💨 Wind: **12.0 km/h** (Perfect day for a round!)")

profiles = load_profiles()

st.sidebar.header("🔐 User Authentication")
name_input = st.sidebar.text_input("Enter Profile Name:").strip().lower()
password_input = st.sidebar.text_input("Enter Password:", type="password")

if not name_input:
    st.info("Please log in via the sidebar to access your profile data.")
    st.stop()

display_name = name_input.capitalize()

if name_input in profiles:
    if isinstance(profiles[name_input], dict) and "password" in profiles[name_input]:
        if password_input != profiles[name_input]["password"]:
            st.sidebar.error("Incorrect password!")
            st.stop()
        else:
            st.sidebar.success(f"Logged in as {display_name}")
    else:
        st.sidebar.warning("Set a password for your profile:")
        if st.sidebar.button("Secure Account") and password_input:
            old_scores = profiles[name_input] if isinstance(profiles[name_input], list) else []
            profiles[name_input] = {"password": password_input, "scores": old_scores}
            save_profiles(profiles)
            st.rerun()
        st.stop()
else:
    if st.sidebar.button("Create Profile") and password_input:
        profiles[name_input] = {"password": password_input, "scores": []}
        save_profiles(profiles)
        st.rerun()
    st.stop()

# --- NO INDENTATION TABS ---
user_data = profiles.get(name_input, {})
user_scores = user_data.get("scores", [])

tab1, tab2, tab3, tab4 = st.tabs(["📱 Live Scorecard", "📊 My Stats & Badges", "🏆 Leaderboard & Versus", "⚙️ Manage Data"])

with tab1:
    st.header(f"Live Scorecard: {display_name}")
    
    # DYNAMIC COURSE SELECTOR
    course_options = list(st.session_state["courses"].keys()) + ["➕ Add Custom Local Course Layout..."]
    coursechose = st.selectbox("Select course layout:", course_options)
    
    if coursechose == "➕ Add Custom Local Course Layout...":
        st.subheader("🛠️ Register a New Local Course Layout")
        custom_name = st.text_input("Enter Course Name:").strip().lower()
        custom_holes = st.number_input("Number of Holes:", min_value=1, max_value=18, value=9)
        custom_input = st.text_input(f"Enter Pars for all {custom_holes} holes separated by commas (e.g., 4,3,4,5):")
        
        if st.button("Save New Course Layout") and custom_name and custom_input:
            try:
                pars_list = [int(p.strip()) for p in custom_input.split(",") if p.strip()]
                if len(pars_list) == custom_holes:
                    st.session_state["courses"][custom_name] = {"pars": pars_list, "rating": float(custom_holes*3.8), "slope": 113}
                    st.success(f"Successfully added '{custom_name.capitalize()}'! Choose it from the selector dropdown above.")
                    st.rerun()
                else:
                    st.error(f"Error: You entered {len(pars_list)} par values, but specified {custom_holes} holes.")
            except ValueError:
                st.error("Invalid entry. Use numbers and commas only.")
    else:
        # Normal hole input generation if an existing layout is selected
        course_pars = st.session_state["courses"][coursechose]["pars"]
        hole_scores = []
        cols = st.columns(3)
        for i in range(len(course_pars)):
            with cols[i % 3]:
                score_val = st.number_input(f"Hole {i+1} (Par {course_pars[i]})", min_value=1, max_value=15, value=int(course_pars[i]), key=f"h_{i}")
                hole_scores.append(score_val)
                
        total_gross = sum(hole_scores)
        shotsover = total_gross - sum([int(p) for p in course_pars])
        st.metric(label="Selected Strokes", value=total_gross, delta=f"{shotsover} Over Par")
        
        if st.button("Save Round Data"):
            profiles = load_profiles()
            profiles[name_input]["scores"].append(shotsover)
            save_profiles(profiles)
            st.success("Round successfully saved!")
            st.rerun()

with tab2:
    st.header(f"Handicap Metrics: {display_name}")
    roundsplayed = len(user_scores)
    if roundsplayed == 0:
        st.warning("No rounds played yet.")
    else:
        hc_val = calculate_handicap_value(user_scores)
        c1, c2 = st.columns(2)
        c1.metric("Handicap Index", f"{hc_val:.1f}" if isinstance(hc_val, float) else hc_val)
        c2.metric("Rounds Played", roundsplayed)
        
        st.subheader("🏅 Badges Unlocked")
        for badge in check_achievements(user_scores): st.info(badge)
        
        st.subheader("📉 Handicap Trend")
        if roundsplayed >= 2:
            trend = [calculate_handicap_value(user_scores[:i]) for i in range(1, roundsplayed + 1)]
            fig = px.line(x=list(range(1, roundsplayed + 1)), y=[t if isinstance(t, float) else 0.0 for t in trend], labels={"x":"Round", "y":"Handicap"}, markers=True)
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("🏆 Overall Standings")
    leaderboard_data = []
    for p_name, p_data in profiles.items():
        arr = p_data.get("scores", []) if isinstance(p_data, dict) else []
        hc = calculate_handicap_value(arr)
        leaderboard_data.append({"Player": p_name.capitalize(), "Handicap Index": f"{hc:.1f}" if isinstance(hc, float) else str(hc), "Rounds": len(arr)})
    
    if leaderboard_data:
        def skey(x):
            try: return float(x["Handicap Index"])
            except: return 999.0
        st.table(sorted(leaderboard_data, key=skey))
        
    st.divider()
    st.header("👥 Versus Match")
    opponents = [k.capitalize() for k in profiles.keys() if k != name_input]
    if opponents:
        target_friend = st.selectbox("Match against:", opponents).lower()
        f_scores = profiles.get(target_friend, {}).get("scores", [])
        my_hc = calculate_handicap_value(user_scores)
        friend_hc = calculate_handicap_value(f_scores)
        
        m_num = my_hc if isinstance(my_hc, (int, float)) else 0.0
        f_num = friend_hc if isinstance(friend_hc, (int, float)) else 0.0
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Your Rating", str(my_hc))
        col_m2.metric(f"{target_friend.capitalize()}'s Rating", str(friend_hc))
        
        diff = abs(round(m_num - f_num))
        if m_num > f_num: st.warning(f"You get {diff} free shots today.")
        elif f_num > m_num: st.success(f"{target_friend.capitalize()} gets {diff} free shots today.")
        else: st.info("Scratch Match! Even layout.")

with tab4:
    st.header("⚙️ Data Management")
    if user_scores:
        st.write(f"Latest entry: **{user_scores[-1]}**")
        if st.button("Delete Last Entry"):
            profiles = load_profiles()
            profiles[name_input]["scores"].pop()
            save_profiles(profiles)
            st.success("Entry removed!")
            st.rerun()
    else:
        st.caption("No history to modify.")
