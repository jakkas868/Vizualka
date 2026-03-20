import streamlit as st
import replicate
from PIL import Image, ImageDraw
from streamlit_drawable_canvas import st_canvas
import io
import requests

# --- KONFIGURACE ---
st.set_page_config(page_title="Vizualka.cz", layout="centered")

# --- CSS PRO MOBILY (Větší tlačítka) ---
st.markdown("""
    <style>
    div.stButton > button { width: 100% !important; height: 3em; font-size: 1.2rem !important; background-color: #28a745 !important; color: white !important; }
    .stApp { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏠 Vizualka.cz")
st.write("Vyfoť barák, zamaluj fasádu a vizualizuj.")

# --- SIDEBAR (NASTAVENÍ) ---
with st.sidebar:
    st.header("🔑 Nastavení")
    token = st.text_input("Replicate Token:", type="password")
    watermark = st.text_input("Tvůj vodoznak:", "Vizualka.cz")

# --- 1. NAHRÁNÍ FOTKY ---
bg_file = st.file_uploader("📸 Nahraj fotku domu:", type=["jpg", "jpeg", "png"])

if bg_file:
    img = Image.open(bg_file)
    w, h = img.size
    max_size = 800
    ratio = min(max_size/w, max_size/h)
    new_size = (int(w*ratio), int(h*ratio))
    img_resized = img.resize(new_size)

    st.subheader("🖍️ Zamaluj prstem plochu pro změnu:")
    
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.4)",
        stroke_width=15,
        stroke_color="#000",
        background_image=img_resized,
        height=new_size[1],
        width=new_size[0],
        drawing_mode="freedraw",
        key="canvas",
    )

    if st.button("🚀 VIZUALIZOVAT"):
        if not token:
            st.warning("⚠️ Nejdřív vlož Replicate Token v menu vlevo!")
        else:
            with st.spinner("AI pracuje..."):
                st.info("Odesílám do AI motoru...")
                st.image(img_resized, caption="Tady se objeví výsledek s vodoznakem: " + watermark)
                st.success("Web funguje! Teď už zbývá jen propojit reálný Replicate model.")

# --- PATIČKA ---
st.markdown("---")
st.caption("© 2026 Vizualka.cz | Provozováno na AI")
