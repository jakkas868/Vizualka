import streamlit as st
import replicate
from PIL import Image, ImageDraw
from streamlit_drawable_canvas import st_canvas
import io
import requests

# --- NASTAVENÍ STRÁNKY (Nové, moderní) ---
st.set_page_config(page_title="Vizualka.cz | AI Pro", layout="centered")

# --- CSS TUNING (Profi, zaoblený, Dark Mode) ---
st.markdown("""
    <style>
    /* Základní styl, Dark Mode a moderní font */
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap');
    body, .stApp { font-family: 'Sora', sans-serif !important; background-color: #0c0d10 !important; color: #f8f9fa !important; }
    
    /* Karty a zaoblení */
    .stFileUploader, div[data-testid="stSidebar"], .stButton > button, div[data-testid="stMarkdownContainer"], canvas { border-radius: 12px !important; }
    .stFileUploader > div, div[data-testid="stSidebar"], div[data-testid="stMarkdownContainer"] { background-color: #1a1c22 !important; color: white !important; padding: 10px; }
    .stFileUploader svg, div[data-testid="stSidebar"] svg { fill: white !important; }

    /* Hlavní akční tlačítko */
    div.stButton > button { width: 100% !important; height: 3.5em; font-size: 1.2rem !important; background-color: #00c853 !important; color: white !important; font-weight: 700 !important; border-radius: 12px !important; text-transform: uppercase; }
    div.stButton > button:hover { background-color: #00e676 !important; border: none !important; color: white !important; }
    div.stButton > button:focus { outline: none !important; border: none !important; color: white !important; }

    /* Nadpisy */
    h1, h2, h3 { font-weight: 700 !important; color: #f8f9fa !important; }
    .stTitle h1 { font-size: 3rem !important; color: white !important; }

    /* Prvky formuláře */
    div[data-testid="stSidebar"] input, div[data-testid="stSidebar"] select { background-color: #2c2f37 !important; color: white !important; border: none !important; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ZÁHLAVÍ (Čisté, moderní) ---
st.title("🏠 Vizualka.cz")
st.markdown("<p style='font-size: 1.3rem; font-weight: 400; color: #ccc;'>Vyfoť barák, zamaluj fasádu, vizualizuj.</p>", unsafe_allow_html=True)

# --- BOČNÍ MENU (Čistý Sidebar) ---
with st.sidebar:
    st.image("https://jakkas86.github.io/Vizualka/logo.png", width=150) # Zde pak nahrajeme tvoje logo
    st.header("⚙️ Nastavení")
    token = st.text_input("Vlož API Token:", type="password")
    prompt_text = st.text_input("Co chceš vytvořit?", "modern house facade, gray plaster, detailed")
    watermark_text = st.text_input("Tvůj vodoznak:", "Vizualka.cz")

# --- 1. NAHRÁNÍ FOTKY (Čistá karta) ---
bg_file = st.file_uploader("📸 Nahraj fotku domu:", type=["jpg", "jpeg", "png"])

if bg_file:
    # --- LOGIKA STEJNÁ ---
    img = Image.open(bg_file)
    w, h = img.size
    ratio = min(800/w, 800/h)
    new_size = (int(w*ratio), int(h*ratio))
    img_resized = img.resize(new_size)

    # --- KRESLENÍ MASKY (Čistá karta) ---
    st.subheader("🖍️ Zamaluj prstem plochu pro změnu:")
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.4)",
        stroke_width=18,
        stroke_color="#000",
        background_image=img_resized,
        height=new_size[1],
        width=new_size[0],
        drawing_mode="freedraw",
        key="canvas",
    )

    # --- TLAČÍTKO VIZUALIZOVAT ---
    if st.button("🚀 Vizualizovat (1 Kredit)"):
        # --- ZATÍM SIMULACE ---
        st.info("Příprava propojení s AI...")

# --- PATIČKA ---
st.markdown("<hr style='border: 1px solid #2c2f37;'/>", unsafe_allow_html=True)
st.caption("© 2026 Vizualka.cz | Revoluce ve stavebnictví")
