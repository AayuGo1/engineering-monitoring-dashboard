
import streamlit as st
from datetime import datetime

# ==========================================
# 1. PAGE & THEME CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Industrial Engineering Monitoring Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ultra-Premium Dark SCADA Design & Animated Industrial Background
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;700&display=swap');
        
        /* Base Reset & Animated Technical Grid Background */
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #060913 !important;
            color: #f1f5f9 !important;
            background-image: 
                linear-gradient(rgba(59, 130, 246, 0.015) 1px, transparent 1px),
                linear-gradient(90deg, rgba(59, 130, 246, 0.015) 1px, transparent 1px);
            background-size: 40px 40px;
            background-position: center;
            animation: backgroundScroll 20s linear infinite;
        }
        
        /* Ambient Radial Core Light Glow */
        [data-testid="stAppViewContainer"]::before {
            content: "";
            position: absolute;
            top: -20%;
            left: 30%;
            width: 60vw;
            height: 60vh;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.05) 0%, rgba(16, 185, 129, 0.02) 50%, transparent 100%);
            pointer-events: none;
            z-index: 0;
        }

        @keyframes backgroundScroll {
            0% { background-position: 0px 0px; }
            100% { background-position: 40px 40px; }
        }
        
        /* Premium Clean Sidebar */
        [data-testid="stSidebar"] {
            background-color: #090d1a !important;
            border-right: 1px solid rgba(255, 255, 255, 0.04) !important;
        }
        
        [data-testid="stHeader"] {
            background: transparent !important;
        }
        
        /* 1. Ultra Clean Top Navigation Bar */
        .top-nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1.25rem 2rem;
            background: rgba(13, 20, 38, 0.6);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 16px;
            margin: 0.5rem 0 3.5rem 0;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
        }
        .nav-left {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .logo-placeholder {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #2563eb, #059669);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Space Grotesk', sans-serif;
            font-weight: 700;
            font-size: 1.2rem;
            color: white;
            box-shadow: 0 0 20px rgba(37, 99, 235, 0.3);
        }
        .nav-title {
            font-size: 1.35rem;
            font-weight: 600;
            letter-spacing: -0.5px;
            color: #ffffff;
        }
        .nav-right {
            display: flex;
            align-items: center;
            gap: 28px;
            font-size: 0.88rem;
            color: #94a3b8;
        }
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.06);
            color: #34d399;
            padding: 6px 14px;
            border-radius: 30px;
            font-weight: 500;
            border: 1px solid rgba(16, 185, 129, 0.15);
            letter-spacing: 0.3px;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            background-color: #10b981;
            border-radius: 50%;
            box-shadow: 0 0 10px #10b981;
            animation: pulse 2s infinite;
        }
        
        /* 2. Premium Hero Section */
        .hero-section {
            text-align: center;
            padding: 2.5rem 1rem 4.5rem 1rem;
        }
        .hero-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 3.5rem;
            font-weight: 700;
            background: linear-gradient(180deg, #ffffff 0%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
            letter-spacing: -1.5px;
        }
        .hero-subtitle {
            font-size: 1.2rem;
            color: #64748b;
            max-width: 680px;
            margin: 0 auto;
            line-height: 1.6;
            font-weight: 400;
        }
        
        /* 3. Massive Overhauled Navigation Cards & Glows */
        .nav-card {
            background: rgba(15, 23, 42, 0.45);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 24px;
            padding: 3.5rem 2rem 2.5rem 2rem;
            text-align: center;
            transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }
        .nav-card:hover {
            transform: translateY(-8px);
            background: rgba(20, 30, 54, 0.6);
            border-color: rgba(59, 130, 246, 0.35);
            box-shadow: 0 20px 50px rgba(37, 99, 235, 0.15);
        }
        .card-icon {
            font-size: 3.5rem;
            margin-bottom: 1.5rem;
            display: inline-block;
            transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }
        .nav-card:hover .card-icon {
            transform: scale(1.22);
        }
        .card-title {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1.5rem;
            font-weight: 600;
            color: #f8fafc;
            margin-bottom: 0.75rem;
            letter-spacing: -0.3px;
        }
        .card-desc {
            font-size: 0.92rem;
            color: #94a3b8;
            line-height: 1.6;
            margin-bottom: 2rem;
            padding: 0 0.5rem;
        }
        
        /* Elegant CTA Styling integrated with Streamlit Base */
        .stButton>button {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            color: #cbd5e1 !important;
            border-radius: 12px !important;
            padding: 0.6rem 1.5rem !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            transition: all 0.3s ease !important;
            letter-spacing: 0.2px;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
            border-color: #3b82f6 !important;
            color: white !important;
            box-shadow: 0 0 15px rgba(37, 99, 235, 0.4) !important;
        }
        
        /* Clean Footer Layout */
        .custom-footer {
            border-top: 1px solid rgba(255, 255, 255, 0.04);
            padding: 2rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #475569;
            font-size: 0.88rem;
            margin-top: 6rem;
            letter-spacing: 0.3px;
        }

        @keyframes pulse {
            0% { transform: scale(0.96); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
            70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.96); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }
    </style>
""", unsafe_html=True)

# ==========================================
# 2. STATE MANAGEMENT FOR INTER-PAGE NAV
# ==========================================
if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Home"

def navigate_to(page_name):
    st.session_state.current_page = page_name

# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("<div style='padding: 1.5rem 0 2.5rem 0; text-align: center;'><h3 style='color:#f8fafc; font-family:\"Space Grotesk\"; font-weight:600; margin:0;'>⚡ Core Menu</h3></div>", unsafe_html=True)
    
    navigation_options = [
        "🏠 Home", 
        "📊 Overview", 
        "🏭 Department Analysis", 
        "🌀 Air Compressor", 
        "❄ Freon Monitoring", 
        "⚙ Settings"
    ]
    
    current_index = navigation_options.index(st.session_state.current_page)
    selected_menu = st.radio(
        label="Select Workspace",
        options=navigation_options,
        index=current_index,
        label_visibility="collapsed"
    )
    
    if selected_menu != st.session_state.current_page:
        st.session_state.current_page = selected_menu
        st.rerun()

# ==========================================
# 4. TOP NAVIGATION BAR (GLOBAL GLOBAL)
# ==========================================
current_date_str = datetime.now().strftime("%A, %b %d, %Y")
current_time_str = datetime.now().strftime("%H:%M:%S UTC")

st.markdown(f"""
    <div class="top-nav">
        <div class="nav-left">
            <div class="logo-placeholder">Ω</div>
            <div class="nav-title">Plant Engineering Analytics Platform</div>
        </div>
        <div class="nav-right">
            <div>📅 &nbsp;{current_date_str}</div>
            <div>🕒 &nbsp;<span style="color: #ffffff; font-weight:500;">{current_time_str}</span></div>
            <div class="status-indicator">
                <div class="status-dot"></div>
                Live Telemetry Connection
            </div>
            <div style="font-size: 0.82rem; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); padding: 4px 10px; border-radius: 6px; color:#64748b;">Updated: Just Now</div>
        </div>
    </div>
""", unsafe_html=True)

# ==========================================
# 5. RENDER CHOSEN WORKSPACE WINDOW
# ==========================================

if st.session_state.current_page == "🏠 Home":
    # Refined Premium Hero Block
    st.markdown("""
        <div class="hero-section">
            <div class="hero-title">Engineering Monitoring Dashboard</div>
            <div class="hero-subtitle">High-fidelity SCADA optimization & industrial telemetry environment. Select an infrastructure module node below to analyze deep telemetry.</div>
        </div>
    """, unsafe_html=True)
    
    # 4 Oversized Premium Columns
    col1, col2, col3, col4 = st.columns(4, gap="large")
    
    with col1:
        st.markdown("""
            <div class="nav-card">
                <div>
                    <div class="card-icon">📊</div>
                    <div class="card-title">Overview</div>
                    <div class="card-desc">Macro-level system health metrics, overall plant efficiency metrics, and aggregate power demand allocations.</div>
                </div>
            </div>
        """, unsafe_html=True)
        if st.button("Enter Overview Console", key="btn_ov", use_container_width=True):
            navigate_to("📊 Overview")
            st.rerun()
            
    with col2:
        st.markdown("""
            <div class="nav-card">
                <div>
                    <div class="card-icon">🏭</div>
                    <div class="card-title">Department Analysis</div>
                    <div class="card-desc">Granular machine consumption logs, asset runtime distributions, and sub-department line mapping indices.</div>
                </div>
            </div>
        """, unsafe_html=True)
        if st.button("Enter Department Analytics", key="btn_dept", use_container_width=True):
            navigate_to("🏭 Department Analysis")
            st.rerun()
            
    with col3:
        st.markdown("""
            <div class="nav-card">
                <div>
                    <div class="card-icon">🌀</div>
                    <div class="card-title">Air Compressor</div>
                    <div class="card-desc">Pneumatic performance telemetry, line system pressure monitoring, and cycling frequency profiles.</div>
                </div>
            </div>
        """, unsafe_html=True)
        if st.button("Enter Compressor Metrics", key="btn_comp", use_container_width=True):
            navigate_to("🌀 Air Compressor")
            st.rerun()
            
    with col4:
        st.markdown("""
            <div class="nav-card">
                <div>
                    <div class="card-icon">❄</div>
                    <div class="card-title">Freon Monitoring</div>
                    <div class="card-desc">Thermodynamic cooling cycle logs, chiller efficiency matrices, and containment pressure indices.</div>
                </div>
            </div>
        """, unsafe_html=True)
        if st.button("Enter Freon Analytics", key="btn_freon", use_container_width=True):
            navigate_to("❄ Freon Monitoring")
            st.rerun()

else:
    # Keeps architectural baseline intact for specific submodule targets
    st.markdown(f"## {st.session_state.current_page}")
    st.info(f"UI Container Frame mapped to **{st.session_state.current_page}**. Ready for pipeline deployment referencing 'Daily energy Monitoring.xlsx'.")
    
    if st.button("← Back to Global Infrastructure Control"):
        navigate_to("🏠 Home")
        st.rerun()

# ==========================================
# 6. FOOTER
# ==========================================
st.markdown("""
    <div class="custom-footer">
        <div>Developed for Internship Project</div>
        <div style="color: #64748b;">Core Architecture Engine: <span style="color: #3b82f6; font-weight:500;">v2.5.0-Industrial</span></div>
    </div>
""", unsafe_html=True)
