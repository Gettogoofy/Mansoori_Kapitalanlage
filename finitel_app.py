"""
FinIntel GmbH – KI-gestützte Kapitalanlageberatung
User-Centered Redesign · Demo-Prototyp (Streamlit) für eine Universitätspräsentation.

Die Oberfläche ist um die Arbeitsabläufe der Nutzer herum gebaut (aufgabenorientiert)
statt um technische Features:

    🏠 Cockpit            – Tagesstart, Marktlage, nächste sinnvolle Aktion
    🧭 Kunde beraten       – geführter 3-Schritt-Wizard (Profil → KI-Vorschlag → Freigabe)
    📡 Portfolio überwachen – Markt/Krise & ESG (Tabs)
    ✅ Freigabe & Compliance – eigenständiger MiFID-II-Check

Zusätzlich ein Ansichts-Umschalter (👔 Berater / 🙋 Kunde), der Sprache und Detailtiefe
an die jeweilige Person anpasst (Hybrid / User-Centered).

WICHTIG: Alle Daten sind Dummy-/Demodaten. Keine externen APIs, kein echtes ML.
Start:  streamlit run finitel_app.py
"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------- #
# Reproduzierbarkeit der Dummy-Daten & Farben
# --------------------------------------------------------------------------- #
np.random.seed(42)

NAVY = "#1E2761"
BLUE = "#4A90D9"
NAVY_PALETTE = ["#1E2761", "#3A4A99", "#4A90D9", "#9BC1E8"]

# --------------------------------------------------------------------------- #
# Seitenkonfiguration
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="FinIntel – KI-Kapitalanlageberatung",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------- #
# Session-State-Initialisierung
# --------------------------------------------------------------------------- #
st.session_state.setdefault("mode", "👔 Berater")
st.session_state.setdefault("nav_page", "🏠 Cockpit")
st.session_state.setdefault("wizard_step", 1)
st.session_state.setdefault("advisory_done", False)

NAV_OPTIONS = [
    "🏠 Cockpit",
    "🧭 Kunde beraten",
    "📡 Portfolio überwachen",
    "✅ Freigabe & Compliance",
]

# --------------------------------------------------------------------------- #
# Custom CSS (Navy professionell, aufgeräumt)
# --------------------------------------------------------------------------- #
st.markdown(
    f"""
    <style>
    .block-container {{ padding-top: 1.5rem; padding-bottom: 2.5rem; max-width: 1280px; }}
    html, body, [class*="css"] {{ font-size: 16px; }}

    /* Lesbarkeit erzwingen (Fallback, falls .streamlit/config.toml nicht greift):
       helle Flächen + dunkle Standardschrift. Steht VOR den Klassen mit weißer
       Schrift, damit Hero/Banner/Buttons/Badges (weiß auf Farbe) gewinnen. */
    [data-testid="stAppViewContainer"], [data-testid="stMain"],
    [data-testid="stHeader"] {{ background-color:#ffffff; }}
    [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li, label,
    [data-testid="stWidgetLabel"] p {{ color:#262730; }}
    [data-testid="stExpander"] summary, [data-testid="stExpander"] p {{ color:#262730; }}

    /* ---------- Hero-Begrüßungsband ---------- */
    .fi-hero {{
        background: linear-gradient(120deg, {NAVY} 0%, #2b3a86 55%, {BLUE} 130%);
        color: #ffffff;
        border-radius: 16px;
        padding: 26px 30px;
        margin-bottom: 1.4rem;
        box-shadow: 0 6px 24px rgba(30,39,97,0.18);
    }}
    .fi-hero h1 {{ font-size: 1.9rem; font-weight: 800; margin: 0 0 4px 0; color:#fff; }}
    .fi-hero p  {{ font-size: 1.02rem; margin: 0; opacity: 0.92; }}
    .fi-hero .fi-eyebrow {{
        text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.72rem;
        font-weight: 700; opacity: 0.8; margin-bottom: 6px;
    }}

    /* ---------- Seiten-Header ---------- */
    .fi-title    {{ color:{NAVY}; font-size:1.7rem; font-weight:800; margin-bottom:2px; }}
    .fi-subtitle {{ color:#5a6072; font-size:1.0rem; margin:0 0 1.2rem 0; }}
    .fi-section  {{ color:{NAVY}; font-size:1.15rem; font-weight:700; margin:0.4rem 0 0.6rem 0; }}

    /* ---------- Cards ---------- */
    .fi-card {{
        background:#f8f9fc; border:1px solid #e7ebf5; border-radius:14px;
        padding:20px 22px; margin-bottom:1rem;
        box-shadow:0 2px 12px rgba(30,39,97,0.06);
    }}
    .fi-card h4 {{ color:{NAVY}; margin-top:0; }}

    /* ---------- Next-Best-Action Callout ---------- */
    .fi-nba {{
        display:flex; align-items:center; gap:16px;
        background:#eef3fd; border:1px solid #cfe0fa; border-left:6px solid {BLUE};
        border-radius:14px; padding:18px 22px; margin-bottom:1.2rem;
    }}
    .fi-nba .fi-nba-icon {{ font-size:2.0rem; }}
    .fi-nba .fi-nba-title {{ font-weight:800; color:{NAVY}; font-size:1.05rem; }}
    .fi-nba .fi-nba-text  {{ color:#48506a; font-size:0.95rem; }}

    /* ---------- Banner ---------- */
    .fi-banner {{
        background:linear-gradient(90deg,{NAVY} 0%,{BLUE} 100%); color:#fff;
        border-radius:12px; padding:14px 20px; font-size:0.97rem; margin-bottom:1rem;
    }}
    .fi-banner-soft {{
        background:#eef3fd; border:1px solid #cfe0fa; color:{NAVY};
        border-radius:12px; padding:14px 20px; font-size:0.97rem; margin-bottom:1rem;
    }}

    /* ---------- Erfolg / Blockiert ---------- */
    .fi-success {{ background:#e6f6ec; border-left:6px solid #1f9d55; color:#14633a;
                   border-radius:10px; padding:14px 18px; font-weight:600; margin-top:0.8rem; }}
    .fi-blocked {{ background:#fdecec; border-left:6px solid #d64545; color:#8a1f1f;
                   border-radius:10px; padding:14px 18px; font-weight:600; margin-top:0.8rem; }}

    /* ---------- Badges ---------- */
    .badge-green,.badge-red,.badge-orange,.badge-blue {{
        display:inline-block; padding:5px 14px; border-radius:999px;
        font-size:0.85rem; font-weight:700; color:#fff;
    }}
    .badge-green {{ background:#1f9d55; }}
    .badge-red {{ background:#d64545; }}
    .badge-orange {{ background:#e08e0b; }}
    .badge-blue {{ background:{BLUE}; }}

    /* ---------- KPI-Metriken ---------- */
    div[data-testid="stMetric"] {{
        background:#f8f9fc; border:1px solid #e7ebf5; border-radius:14px;
        padding:16px 18px; box-shadow:0 2px 8px rgba(30,39,97,0.06);
    }}
    div[data-testid="stMetricValue"] {{ font-size:1.7rem; color:{NAVY}; font-weight:800; }}
    div[data-testid="stMetricLabel"] {{ font-weight:600; color:#5a6072; }}

    /* ---------- Step-Indicator (Wizard) ---------- */
    .fi-steps {{ display:flex; align-items:flex-start; justify-content:space-between;
                 margin:0.2rem 0 1.4rem 0; }}
    .fi-step {{ display:flex; flex-direction:column; align-items:center; width:120px; }}
    .fi-step .circle {{
        width:42px; height:42px; border-radius:50%; display:flex; align-items:center;
        justify-content:center; font-weight:800; font-size:1.05rem;
        background:#e3e8f4; color:#9aa3bd; border:2px solid #e3e8f4;
    }}
    .fi-step .lbl {{ margin-top:8px; font-size:0.85rem; color:#9aa3bd; font-weight:600;
                     text-align:center; }}
    .fi-step.active .circle {{ background:{NAVY}; color:#fff; border-color:{NAVY};
                               box-shadow:0 0 0 4px rgba(30,39,97,0.15); }}
    .fi-step.active .lbl {{ color:{NAVY}; }}
    .fi-step.done .circle {{ background:{BLUE}; color:#fff; border-color:{BLUE}; }}
    .fi-step.done .lbl {{ color:{BLUE}; }}
    .fi-line {{ flex:1; height:3px; background:#e3e8f4; margin:21px 6px 0 6px; border-radius:2px; }}
    .fi-line.done {{ background:{BLUE}; }}

    /* ---------- Tabs ---------- */
    button[data-baseweb="tab"] {{ font-weight:700; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color:{NAVY}; }}
    div[data-baseweb="tab-highlight"] {{ background-color:{NAVY}; }}

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {{ background:#eef1f8; }}
    .fi-logo {{ color:{NAVY}; font-size:1.45rem; font-weight:800; line-height:1.1; }}
    .fi-logo-sub {{ color:{BLUE}; font-size:0.9rem; font-weight:600; margin-bottom:0.4rem; }}
    .fi-side-info {{ font-size:0.85rem; color:#404a66; line-height:1.7; }}
    .fi-footer {{ font-size:0.78rem; color:#8a92a8; margin-top:1rem; }}

    /* ---------- Primär-Buttons ---------- */
    div.stButton > button[kind="primary"] {{
        background:{NAVY}; border:none; color:#fff; font-weight:700;
        border-radius:9px; padding:0.62rem 1rem; width:100%;
    }}
    div.stButton > button[kind="primary"]:hover {{ background:{BLUE}; color:#fff; }}
    div.stButton > button[kind="secondary"] {{
        border-radius:9px; font-weight:600; width:100%;
    }}

    /* WICHTIG: Weiße Schrift auf farbigen Flächen muss den dunklen Text-Fallback
       (oben) schlagen – sonst dunkle Schrift auf Navy = unlesbar. Daher !important
       auf genau den Elementen, die auf farbigem Grund stehen. */
    .fi-hero, .fi-hero *,
    .fi-banner, .fi-banner *,
    .badge-green, .badge-red, .badge-orange, .badge-blue,
    .fi-step.active .circle, .fi-step.done .circle,
    div.stButton > button[kind="primary"],
    div.stButton > button[kind="primary"] * {{ color:#ffffff !important; }}
    /* Sekundär-Buttons (heller Grund) -> dunkle, lesbare Schrift */
    div.stButton > button[kind="secondary"],
    div.stButton > button[kind="secondary"] * {{ color:{NAVY} !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- #
# Helfer
# --------------------------------------------------------------------------- #
def is_advisor() -> bool:
    """True im Berater-Modus, False in der Kundensicht."""
    return st.session_state.get("mode", "👔 Berater").startswith("👔")


def t(advisor_text: str, client_text: str) -> str:
    """Wählt Text je nach aktiver Ansicht (User-Centered)."""
    return advisor_text if is_advisor() else client_text


def header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="fi-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="fi-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def hero(eyebrow: str, title: str, text: str) -> None:
    st.markdown(
        f'<div class="fi-hero"><div class="fi-eyebrow">{eyebrow}</div>'
        f'<h1>{title}</h1><p>{text}</p></div>',
        unsafe_allow_html=True,
    )


def style_plotly(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(color=NAVY),
        title_font=dict(color=NAVY, size=16),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return fig


def status_badge(text: str) -> str:
    if "KRITISCH" in text:
        return "background-color:#d64545;color:white;font-weight:700;"
    if "WARNUNG" in text:
        return "background-color:#e08e0b;color:white;font-weight:700;"
    return "background-color:#1f9d55;color:white;font-weight:700;"


def step_indicator(current: int) -> None:
    steps = [("1", "Profil"), ("2", "KI-Vorschlag"), ("3", "Freigabe")]
    html = '<div class="fi-steps">'
    for i, (num, label) in enumerate(steps, start=1):
        state = "done" if i < current else ("active" if i == current else "")
        html += (f'<div class="fi-step {state}"><div class="circle">{num}</div>'
                 f'<div class="lbl">{label}</div></div>')
        if i < len(steps):
            html += f'<div class="fi-line {"done" if i < current else ""}"></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def goto(page: str, wizard_step: int | None = None) -> None:
    """Navigations-Wunsch hinterlegen (wird vor dem Sidebar-Widget angewandt)."""
    st.session_state["_goto"] = page
    if wizard_step is not None:
        st.session_state["wizard_step"] = wizard_step
    st.rerun()


# --------------------------------------------------------------------------- #
# Daten-Konstanten (wiederverwendet aus der Erstversion)
# --------------------------------------------------------------------------- #
RISK_ALLOC = {
    "Konservativ (Klasse 1-2)": {"Aktien": 20, "Anleihen": 55, "ETFs": 15, "Cash": 10},
    "Moderat (Klasse 3)":       {"Aktien": 40, "Anleihen": 35, "ETFs": 20, "Cash": 5},
    "Wachstumsorientiert (Klasse 4)": {"Aktien": 55, "Anleihen": 20, "ETFs": 22, "Cash": 3},
    "Aggressiv (Klasse 5)":     {"Aktien": 70, "Anleihen": 8, "ETFs": 20, "Cash": 2},
}
RISK_TO_CLASS = {
    "Konservativ (Klasse 1-2)": 2,
    "Moderat (Klasse 3)": 3,
    "Wachstumsorientiert (Klasse 4)": 4,
    "Aggressiv (Klasse 5)": 5,
}

COMPLIANCE_PRODUCTS = {
    "iShares Core MSCI World ETF (Klasse 4)": 4,
    "Xtrackers DAX UCITS ETF (Klasse 4)": 4,
    "DWS Zinseinkommen (Klasse 2)": 2,
    "Allianz Interglobal A EUR (Klasse 3)": 3,
    "Deka-Geldmarktfonds (Klasse 1)": 1,
    "DWS Top Dividende (Klasse 3)": 3,
}
COMPLIANCE_PROFILES = {
    "Dr. Maria Schmidt – Klasse 3": 3,
    "Klaus Weber – Klasse 2": 2,
    "Julia Bauer – Klasse 4": 4,
}


def portfolio_performance_fig() -> go.Figure:
    months = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
              "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    port_ret = np.random.normal(0.9, 1.6, 12)
    bench_ret = np.random.normal(0.6, 1.3, 12)
    portfolio = 100 * np.cumprod(1 + port_ret / 100)
    benchmark = 100 * np.cumprod(1 + bench_ret / 100)
    portfolio[0], benchmark[0] = 100, 100
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=portfolio, name="Portfolio",
                             line=dict(color=BLUE, width=3), mode="lines+markers"))
    fig.add_trace(go.Scatter(x=months, y=benchmark, name="Benchmark",
                             line=dict(color="#888", width=2, dash="dash"), mode="lines"))
    fig.update_layout(title="Wertentwicklung vs. Vergleichsindex (Start = 100)")
    fig.update_yaxes(title="Index")
    return fig


def allocation_pie(alloc: dict, title: str, hole: float = 0.0) -> go.Figure:
    fig = go.Figure(data=[go.Pie(
        labels=list(alloc.keys()), values=list(alloc.values()), hole=hole,
        marker=dict(colors=NAVY_PALETTE), textinfo="label+percent")])
    fig.update_layout(title=title)
    return fig


# --------------------------------------------------------------------------- #
# Bereich 1: Cockpit
# --------------------------------------------------------------------------- #
def page_cockpit() -> None:
    today = datetime.now().strftime("%A, %d.%m.%Y")
    if is_advisor():
        hero("FinIntel Cockpit · Berater-Ansicht",
             "Guten Tag 👋 Ihr Beratungs-Cockpit",
             f"{today} — Marktlage, Warnungen und Ihre nächste sinnvolle Aktion auf einen Blick.")
    else:
        hero("Mein FinIntel · Kundenansicht",
             "Willkommen, Dr. Maria Schmidt 👋",
             f"{today} — So steht es heute um Ihre Geldanlage. Alles verständlich erklärt.")

    # Next-Best-Action
    nba_title = t("Nächster Schritt: Neue Kundenanfrage bearbeiten",
                  "Empfehlung: Lassen Sie sich einen Anlagevorschlag erstellen")
    nba_text = t("Für Dr. Maria Schmidt liegt eine vollständige Anfrage vor – starten Sie die geführte Beratung.",
                 "In wenigen Schritten erhalten Sie einen persönlichen, geprüften Vorschlag.")
    c_icon, c_txt, c_btn = st.columns([0.07, 0.73, 0.20])
    with c_icon:
        st.markdown('<div style="font-size:2.4rem;text-align:center;">🧭</div>',
                    unsafe_allow_html=True)
    with c_txt:
        st.markdown(f'<div class="fi-nba-title">{nba_title}</div>'
                    f'<div class="fi-nba-text">{nba_text}</div>', unsafe_allow_html=True)
    with c_btn:
        st.write("")
        if st.button(t("Beratung starten →", "Vorschlag erhalten →"),
                     type="primary", key="nba_btn"):
            goto("🧭 Kunde beraten", wizard_step=1)

    st.markdown(f'<div class="fi-section">{t("Marktlage & Kennzahlen", "Mein Überblick")}</div>',
                unsafe_allow_html=True)

    # KPI-Zeile
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(t("Portfolio-Wert", "Mein Vermögen"), "1.247.500 €", "+3,2 % diese Woche")
    k2.metric(t("YTD-Rendite", "Ertrag dieses Jahr"), "+7,3 %",
              t("Benchmark: +5,1 %", "Markt: +5,1 %"))
    k3.metric(t("Risikoscore", "Risiko-Stufe"), "Moderat", "Klasse 3 / 5", delta_color="off")
    k4.metric("ESG-Score", "72 / 100", "+4 " + t("seit letztem Monat", "Punkte"))

    st.write("")

    # Charts
    c1, c2 = st.columns([3, 2])
    with c1:
        st.plotly_chart(style_plotly(portfolio_performance_fig()), width="stretch")
    with c2:
        alloc = {"Aktien": 45, "Anleihen": 30, "ETFs": 15, "Cash": 10}
        st.plotly_chart(style_plotly(allocation_pie(alloc, t("Asset-Allokation", "Meine Aufteilung"))),
                        width="stretch")

    # Alerts
    st.markdown(f'<div class="fi-section">{t("Aktive Warnungen", "Wichtige Hinweise")}</div>',
                unsafe_allow_html=True)
    if is_advisor():
        st.error("🔴 **KRITISCH** — DAX -5,2 % in 24h · Krisenwarnung für 12 Portfolios ausgelöst")
        st.warning("🟠 **WARNUNG** — Zinskurven-Inversion erkannt · LSTM-Konfidenz 82 %")
        st.info("🔵 **INFO** — ESG-Score Siemens -8 Punkte · Umschichtung prüfen")
    else:
        st.warning("🟠 Die Märkte schwanken aktuell stärker als üblich – Ihr Portfolio ist breit gestreut und gut aufgestellt.")
        st.info("🔵 Eine Position (Siemens) erfüllt Ihre Nachhaltigkeits-Kriterien nicht mehr ganz – Ihr Berater hat einen Tausch vorbereitet.")

    # ECA-Log nur im Berater-Modus
    if is_advisor():
        with st.expander("⚡ Systemereignisse (ECA-Ereignislog)"):
            log = pd.DataFrame([
                ["09.06.2026 08:23", "Kursrückgang", "DAX -5,2 % in 24h",
                 "🔴 KRITISCH", "Krisenwarnung + Berater-Alert"],
                ["09.06.2026 07:15", "ESG-Score Änderung", "Siemens ESG -8 Punkte",
                 "🟠 WARNUNG", "Umschichtungsvorschlag generiert"],
                ["08.06.2026 16:44", "Makro-Indikator", "Zinskurven-Inversion",
                 "🟠 WARNUNG", "LSTM-Frühwarnung ausgelöst"],
                ["08.06.2026 11:02", "Neue Kundenanfrage", "Kundenprofil vollständig",
                 "🟢 OK", "ML-Inference abgeschlossen"],
                ["07.06.2026 09:30", "Compliance-Check", "Portfolio-Rebalancing",
                 "🟢 OK", "MiFID-II Freigabe erteilt"],
            ], columns=["Zeitstempel", "Ereignistyp", "Auslöser-Wert", "Status", "Aktion"])
            st.dataframe(log.style.map(status_badge, subset=["Status"]),
                         width="stretch", hide_index=True)


# --------------------------------------------------------------------------- #
# Bereich 2: Kunde beraten (Wizard)
# --------------------------------------------------------------------------- #
def page_wizard() -> None:
    header(t("Kunde beraten", "Ihr persönlicher Anlagevorschlag"),
           t("Geführter Ablauf: Profil → KI-Vorschlag → MiFID-II-Freigabe",
             "In drei einfachen Schritten zu Ihrer geprüften Empfehlung"))

    step = st.session_state["wizard_step"]
    step_indicator(step)

    if step == 1:
        _wizard_step1()
    elif step == 2:
        _wizard_step2()
    else:
        _wizard_step3()


def _wizard_step1() -> None:
    st.markdown(f'<div class="fi-section">① {t("Kundenprofil erfassen", "Ihre Angaben")}</div>',
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Kundenname", value="Dr. Maria Schmidt", key="w_name",
                      help="Name der zu beratenden Person.")
        st.slider("Anlagebetrag (€)", 10_000, 1_000_000, 250_000, step=5000,
                  format="%d €", key="w_amount",
                  help="Wie viel soll insgesamt angelegt werden?")
    with c2:
        st.selectbox("Anlagehorizont",
                     ["1–3 Jahre", "3–5 Jahre", "5–10 Jahre", "> 10 Jahre"],
                     index=2, key="w_horizon",
                     help="Wie lange kann das Geld investiert bleiben?")
        st.radio("Risikobereitschaft", list(RISK_ALLOC.keys()), index=1, key="w_risk",
                 help=t("Bestimmt die MiFID-II-Risikoklasse des Kunden.",
                        "Wie stark dürfen Ihre Anlagen schwanken?"))
    st.checkbox(t("ESG-Präferenz aktivieren", "Mir ist Nachhaltigkeit wichtig (ESG)"),
                value=True, key="w_esg")

    st.write("")
    _, right = st.columns([0.7, 0.3])
    with right:
        if st.button(t("Weiter → KI-Vorschlag", "Weiter →"), type="primary", key="s1_next"):
            st.session_state["advisory_done"] = True
            st.session_state["wizard_step"] = 2
            st.rerun()


def _wizard_step2() -> None:
    risk = st.session_state.get("w_risk", "Moderat (Klasse 3)")
    name = st.session_state.get("w_name", "Dr. Maria Schmidt")

    st.markdown(f'<div class="fi-section">② {t("KI-Anlagevorschlag", "Ihr Vorschlag")}</div>',
                unsafe_allow_html=True)

    if is_advisor():
        st.markdown('<span class="badge-green">KONFIDENZ: 87 % · ML-Modell: XGBoost v2.3</span>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="badge-blue">Persönlich abgestimmt für {name}</span>',
                    unsafe_allow_html=True)
    st.write("")

    c1, c2 = st.columns([2, 3])
    with c1:
        alloc = RISK_ALLOC[risk]
        st.plotly_chart(
            style_plotly(allocation_pie(alloc, t("Empfohlene Allokation", "So legen wir an"),
                                        hole=0.55), height=320),
            width="stretch")
    with c2:
        st.markdown(t("##### Konkrete Produktempfehlungen", "##### Das ist enthalten"))
        products = pd.DataFrame([
            ["iShares Core MSCI World ETF", "IE00B4L5Y983", "30 %", "7,2 % p.a.", "4"],
            ["Xtrackers DAX UCITS ETF", "LU0274211480", "15 %", "6,8 % p.a.", "4"],
            ["DWS Zinseinkommen", "DE0008474560", "25 %", "3,1 % p.a.", "2"],
            ["Allianz Interglobal A EUR", "DE0008475070", "20 %", "5,4 % p.a.", "3"],
            ["Cash / Tagesgeld", "–", "10 %", "2,5 % p.a.", "1"],
        ], columns=["Produkt", "ISIN", "Gewichtung", "Erw. Rendite", "Risikoklasse"])
        if not is_advisor():
            products = products[["Produkt", "Gewichtung", "Erw. Rendite"]]
        st.dataframe(products, width="stretch", hide_index=True)

    if not is_advisor():
        with st.expander("ℹ️ Einfach erklärt: Was bedeutet das?"):
            st.write("Ihr Geld wird auf mehrere Anlagen verteilt (Streuung). "
                     "Das senkt das Risiko, weil nicht alles von einer einzigen Entwicklung abhängt. "
                     "Die Mischung passt zu Ihrer gewählten Risikobereitschaft.")

    st.write("")
    left, _, right = st.columns([0.25, 0.45, 0.30])
    with left:
        if st.button("← Zurück", key="s2_back"):
            st.session_state["wizard_step"] = 1
            st.rerun()
    with right:
        if st.button(t("Weiter → Freigabe", "Weiter →"), type="primary", key="s2_next"):
            st.session_state["wizard_step"] = 3
            st.rerun()


def _wizard_step3() -> None:
    risk = st.session_state.get("w_risk", "Moderat (Klasse 3)")
    cust_class = RISK_TO_CLASS[risk]

    st.markdown(f'<div class="fi-section">③ {t("MiFID-II Compliance-Freigabe", "Prüfung & Freigabe")}</div>',
                unsafe_allow_html=True)

    if is_advisor():
        st.markdown(f"**Kundenrisikoklasse: {cust_class}** vs. "
                    f"**max. Produktrisikoklasse: {cust_class}** → ✅ Match")
        checklist = [
            "✅ MiFID-II Dokumentation vorhanden",
            "✅ KYC-Status: Verifiziert (gültig bis 01.2027)",
            f"✅ Risikoklassen-Match: Kunde Klasse {cust_class} = Vorschlag Klasse {cust_class}",
            "✅ Suitability-Test: Bestanden (Score: 94/100)",
            "✅ Negative-Screening: Keine Ausschlusskriterien verletzt",
            "✅ Interessenkonflikt-Prüfung: Negativ",
        ]
    else:
        checklist = [
            "✅ Der Vorschlag passt zu Ihrer Risikobereitschaft",
            "✅ Ihre Identität ist verifiziert",
            "✅ Gesetzliche Eignungsprüfung bestanden",
            "✅ Nachhaltigkeits-Kriterien berücksichtigt",
            "✅ Keine Interessenkonflikte",
        ]

    st.markdown(t("##### Prüfergebnisse", "##### Das haben wir für Sie geprüft"))
    for item in checklist:
        st.markdown(item)

    st.markdown(
        '<div class="fi-success">✅ ' +
        t("FREIGEGEBEN – Anlagevorschlag kann dem Kunden präsentiert werden · "
          "Compliance-Protokoll #CP-2026-0847 erstellt",
          "Alles geprüft und freigegeben – Ihr Vorschlag ist startklar.") +
        '</div>', unsafe_allow_html=True)

    st.write("")
    left, _, right = st.columns([0.25, 0.45, 0.30])
    with left:
        if st.button("← Zurück", key="s3_back"):
            st.session_state["wizard_step"] = 2
            st.rerun()
    with right:
        if st.button(t("✓ Beratung abschließen", "✓ Fertig"), type="primary", key="s3_done"):
            st.success(t("Beratung dokumentiert. Protokoll #CP-2026-0847 abgelegt.",
                         "Vielen Dank! Ihr Vorschlag wurde gespeichert."))
            st.balloons()


# --------------------------------------------------------------------------- #
# Bereich 3: Portfolio überwachen
# --------------------------------------------------------------------------- #
def page_monitor() -> None:
    header(t("Portfolio überwachen", "Sicherheit & Nachhaltigkeit"),
           t("Markt-/Krisenfrüherkennung und ESG-Analyse laufender Portfolios",
             "Wie sicher und wie nachhaltig Ihre Geldanlage gerade ist"))

    tab_risk, tab_esg = st.tabs([t("📉 Markt & Krise", "📉 Sicherheit"),
                                 t("🌱 ESG / Nachhaltigkeit", "🌱 Nachhaltigkeit")])

    # ------------------- Tab: Markt & Krise -------------------
    with tab_risk:
        if is_advisor():
            st.markdown('<div class="fi-banner">🧠 <b>LSTM-Modell aktiv</b> · '
                        'Zeitreihen-Tiefe: 60 Tage · Konfidenz: 82 % · '
                        'Letzter Trainingslauf: 08.06.2026</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="fi-banner-soft">🛡️ Unser Frühwarnsystem beobachtet '
                        'die Märkte rund um die Uhr und meldet ungewöhnliche Entwicklungen '
                        'frühzeitig.</div>', unsafe_allow_html=True)

        gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=34,
            title={"text": t("Systemweiter Krisenindikator", "Aktuelle Marktstabilität") +
                           "<br><span style='font-size:0.85em;color:#e08e0b'>"
                           "Stufe: Erhöhte Aufmerksamkeit</span>"},
            gauge={"axis": {"range": [0, 100]}, "bar": {"color": NAVY},
                   "steps": [{"range": [0, 25], "color": "#c8e6c9"},
                             {"range": [25, 60], "color": "#fff3c4"},
                             {"range": [60, 85], "color": "#ffd8a8"},
                             {"range": [85, 100], "color": "#f5bcbc"}],
                   "threshold": {"line": {"color": NAVY, "width": 4},
                                 "thickness": 0.8, "value": 34}}))
        st.plotly_chart(style_plotly(gauge, height=320), width="stretch")

        c1, c2 = st.columns([3, 2])
        with c1:
            days = 180
            dates = [datetime(2026, 6, 9) - timedelta(days=days - i) for i in range(days)]
            spread = np.linspace(0.9, -0.4, days) + np.random.normal(0, 0.08, days)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=spread, name="10J–2J Spread",
                                     line=dict(color=BLUE, width=2)))
            fig.add_hline(y=0, line_dash="dash", line_color="#888",
                          annotation_text="Neutral", annotation_position="top left")
            fig.add_vrect(x0=dates[-30], x1=dates[-1], fillcolor="#d64545",
                          opacity=0.12, line_width=0,
                          annotation_text="⚠️ Inversions-Phase", annotation_position="top right")
            fig.update_layout(title=t("Zinskurven-Analyse & Anomalie-Detection",
                                      "Markt-Frühindikator (Zinskurve)"))
            fig.update_yaxes(title="Spread (%-Punkte)")
            st.plotly_chart(style_plotly(fig, height=360), width="stretch")
        with c2:
            st.markdown(t("##### 🚨 Aktive Alerts", "##### Was das für Sie heißt"))
            if is_advisor():
                st.error("🔴 **KRITISCH** — DAX -5,2 % in 24h · 12 Portfolios betroffen")
                st.warning("🟠 **WARNUNG** — Zinskurven-Inversion · LSTM-Konfidenz 82 %")
                st.warning("🟠 **WARNUNG** — ESG-Risiko Siemens -8 · Umschichtung empfohlen")
                st.info("🔵 **INFO** — Modell-Retraining: 10.06.2026 02:00 UTC")
            else:
                st.warning("🟠 Die Märkte sind aktuell unruhiger. Kein Grund zur Sorge – "
                           "Ihr Portfolio ist breit gestreut.")
                st.info("🔵 Ihr Berater beobachtet die Lage und meldet sich, falls etwas zu "
                        "tun ist.")

    # ------------------- Tab: ESG -------------------
    with tab_esg:
        if is_advisor():
            st.markdown('<div class="fi-banner-soft">ECA-Trigger: ESG-Score-Änderung → '
                        'Delta-Analyse → Umschichtungsvorschlag</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="fi-banner-soft">🌱 So nachhaltig ist Ihre Geldanlage – '
                        'bewertet nach Umwelt, Sozialem und Unternehmensführung.</div>',
                        unsafe_allow_html=True)

        g1, g2, g3, g4 = st.columns(4)
        g1.metric("🌍 Umwelt (E)", "78 / 100", "+3")
        g2.metric("👥 Sozial (S)", "65 / 100", "-2")
        g3.metric("🏛️ Governance (G)", "74 / 100", "0", delta_color="off")
        g4.metric("⭐ Gesamt-ESG", "72 / 100", "+4")

        st.write("")
        positions = ["iShares MSCI World", "Siemens AG", "DWS Zinseinkommen",
                     "Allianz SE", "Deutsche Telekom"]
        scores = [82, 51, 74, 79, 68]
        threshold = 60
        colors = ["#1f9d55" if s >= threshold else "#d64545" for s in scores]
        fig = go.Figure(go.Bar(x=scores, y=positions, orientation="h",
                               marker=dict(color=colors), text=scores, textposition="auto"))
        fig.add_vline(x=threshold, line_dash="dash", line_color=NAVY,
                      annotation_text="Mindest-Score 60", annotation_position="top")
        fig.update_layout(title=t("ESG-Scores der Portfolio-Positionen",
                                  "Nachhaltigkeit Ihrer Anlagen"))
        fig.update_xaxes(range=[0, 100], title="ESG-Score")
        st.plotly_chart(style_plotly(fig, height=360), width="stretch")

        if st.toggle(t("ESG-Filter aktivieren (Mindest-Score: 60)",
                       "Nur nachhaltige Anlagen anzeigen (ab Score 60)")):
            st.info(t("2 Positionen unterschreiten den ESG-Mindest-Score. "
                      "Rebalancing-Vorschlag wird angezeigt.",
                      "2 Ihrer Anlagen sind aktuell weniger nachhaltig. "
                      "Hier ein Tausch-Vorschlag:"))
            rebal = pd.DataFrame([
                ["VERKAUFEN", "Siemens AG", "500 Stk.", "ESG-Score 51 < 60",
                 "Schneider Electric (ESG: 88)"],
                ["KAUFEN", "Schneider El.", "380 Stk.", "ESG-konformer Ersatz", "–"],
            ], columns=["Aktion", "Position", "Menge", "Grund", "Vorgeschlagener Ersatz"])

            def color_action(val: str) -> str:
                if val == "VERKAUFEN":
                    return "background-color:#d64545;color:white;font-weight:700;"
                if val == "KAUFEN":
                    return "background-color:#1f9d55;color:white;font-weight:700;"
                return ""

            st.dataframe(rebal.style.map(color_action, subset=["Aktion"]),
                         width="stretch", hide_index=True)


# --------------------------------------------------------------------------- #
# Bereich 4: Freigabe & Compliance
# --------------------------------------------------------------------------- #
def page_compliance() -> None:
    header("Freigabe & Compliance",
           "MiFID-II Regelwerk-Engine · Eignungsprüfung vor jeder Empfehlung")

    if not is_advisor():
        st.info("Dieser Bereich ist für Ihren Berater. Er stellt sicher, dass jede Empfehlung "
                "gesetzlich zu Ihrem Profil passt, bevor sie Ihnen vorgeschlagen wird.")

    left, right = st.columns([2, 3])
    with left:
        product = st.selectbox("Anlageprodukt auswählen", list(COMPLIANCE_PRODUCTS.keys()))
        profile = st.selectbox("Kundenprofil", list(COMPLIANCE_PROFILES.keys()))
        if st.button("🔍 Compliance-Check durchführen", type="primary"):
            st.session_state["compliance_done"] = True
            st.session_state["compliance_product"] = product
            st.session_state["compliance_profile"] = profile

    with right:
        if not st.session_state.get("compliance_done"):
            st.info("Produkt und Kundenprofil auswählen, dann **Compliance-Check durchführen**.")
        else:
            product = st.session_state["compliance_product"]
            profile = st.session_state["compliance_profile"]
            prod_class = COMPLIANCE_PRODUCTS[product]
            cust_class = COMPLIANCE_PROFILES[profile]
            match = prod_class <= cust_class

            symbol = "✅ Match" if match else "❌ Mismatch"
            st.markdown(f"**Kundenrisikoklasse: {cust_class}** vs. "
                        f"**Produktrisikoklasse: {prod_class}** → {symbol}")

            mark = "✅" if match else "❌"
            rel = "≥" if match else "<"
            checklist = [
                "✅ MiFID-II Dokumentation vorhanden",
                "✅ KYC-Status: Verifiziert (gültig bis 01.2027)",
                f"{mark} Risikoklassen-Match: Kunde Klasse {cust_class} {rel} "
                f"Produkt Klasse {prod_class}",
                "✅ Suitability-Test: Bestanden (Score: 94/100)",
                "✅ Negative-Screening: Keine Ausschlusskriterien verletzt",
                "✅ Interessenkonflikt-Prüfung: Negativ",
            ]
            st.markdown("##### Prüfergebnisse")
            for item in checklist:
                st.markdown(item)

            if match:
                st.markdown('<div class="fi-success">✅ FREIGEGEBEN – Anlagevorschlag kann dem '
                            'Kunden präsentiert werden · Compliance-Protokoll #CP-2026-0847 '
                            'erstellt</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="fi-blocked">❌ BLOCKIERT – Risikoklassen-Mismatch. '
                            'Produkt nicht geeignet für dieses Kundenprofil.</div>',
                            unsafe_allow_html=True)

    if is_advisor():
        with st.expander("📋 Compliance-Protokoll-Historie"):
            hist = pd.DataFrame([
                ["#CP-2026-0847", "07.06.2026 09:30", "Dr. Maria Schmidt", "Allianz Interglobal",
                 "🟢 FREIGEGEBEN"],
                ["#CP-2026-0846", "06.06.2026 14:12", "Julia Bauer", "iShares MSCI World",
                 "🟢 FREIGEGEBEN"],
                ["#CP-2026-0845", "05.06.2026 11:48", "Klaus Weber", "Xtrackers DAX ETF",
                 "🔴 BLOCKIERT"],
            ], columns=["Protokoll", "Zeitstempel", "Kunde", "Produkt", "Ergebnis"])

            def color_res(val: str) -> str:
                if "BLOCKIERT" in val:
                    return "background-color:#d64545;color:white;font-weight:700;"
                return "background-color:#1f9d55;color:white;font-weight:700;"

            st.dataframe(hist.style.map(color_res, subset=["Ergebnis"]),
                         width="stretch", hide_index=True)


# --------------------------------------------------------------------------- #
# Sidebar & Routing
# --------------------------------------------------------------------------- #
def main() -> None:
    # ausstehenden Navigations-Wunsch anwenden (vor Widget-Instanziierung)
    if "_goto" in st.session_state:
        st.session_state["nav_page"] = st.session_state.pop("_goto")

    with st.sidebar:
        st.markdown('<div class="fi-logo">📈 FinIntel GmbH</div>', unsafe_allow_html=True)
        st.markdown('<div class="fi-logo-sub">KI-Kapitalanlageberatung</div>',
                    unsafe_allow_html=True)
        st.markdown("---")

        st.radio("Ansicht", ["👔 Berater", "🙋 Kunde"], key="mode",
                 help="Wechselt zwischen Fach-Ansicht (Berater) und vereinfachter Kundensicht.")
        st.markdown("**Navigation**")
        st.radio("Navigation", NAV_OPTIONS, key="nav_page", label_visibility="collapsed")

        st.markdown("---")
        now = datetime.now().strftime("%H:%M Uhr")
        st.markdown(
            f'<div class="fi-side-info"><b>ML-Modell Status:</b> 🟢 Online<br>'
            f'<b>Letztes Update:</b> heute, {now}<br>'
            f'<b>Projektphase:</b> MS2 → MS3</div>', unsafe_allow_html=True)
        st.markdown('<div class="fi-footer">FinIntel GmbH · Prototyp v0.1 · MS2→MS3</div>',
                    unsafe_allow_html=True)

    pages = {
        "🏠 Cockpit": page_cockpit,
        "🧭 Kunde beraten": page_wizard,
        "📡 Portfolio überwachen": page_monitor,
        "✅ Freigabe & Compliance": page_compliance,
    }
    pages[st.session_state["nav_page"]]()


if __name__ == "__main__":
    main()
