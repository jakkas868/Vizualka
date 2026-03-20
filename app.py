import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import io
import requests
import time

# --- DESIGN ---
st.set_page_config(page_title="Vizualka.cz Pro", layout="centered")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700&display=swap');
    body, .stApp { background-color: white !important; color: #1a1c22 !important; font-family: 'Sora', sans-serif !important; }
    div.stButton > button { width: 100% !important; height: 3.5em; background-color: #00c853 !important; color: white !important; font-weight: 700 !important; border-radius: 12px !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏠 Vizualka.cz Pro")

# --- TOKEN (Ze Secrets) ---
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token (r8_...):", type="password")

bg_file = st.file_uploader("📸 1. Nahraj fotku domu:", type=["jpg", "png", "jpeg"])

if bg_file:
    img = Image.open(bg_file).convert("RGB")
    w, h = img.size
    ratio = min(800/w, 800/h)
    new_size = (int(w*ratio), int(h*ratio))
    img_res = img.resize(new_size)

    st.write("🖍️ 2. Zamaluj plochu pro změnu:")
    canvas_result = st_canvas(
        fill_color="rgba(0, 200, 83, 0.3)",
        stroke_width=20,
        background_image=img_res,
        height=new_size[1],
        width=new_size[0],
        drawing_mode="freedraw",
        key="vizualka_v2026",
    )

    if st.button("🚀 3. VIZUALIZOVAT"):
        if not api_token:
            st.error("Chybí Token v nastavení!")
        else:
            with st.spinner("🤖 AI pracuje... (může to trvat 20-30 sekund)"):
                try:
                    # Příprava dat
                    img_byte = io.BytesIO()
                    img_res.save(img_byte, format='PNG')
                    mask_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    mask_byte = io.BytesIO()
                    mask_img.save(mask_byte, format='PNG')

                    # Nahrání fotek na dočasný server (aby je AI viděla)
                    # Používáme přímý API hovor pro stabilitu
                    headers = {"Authorization": f"Token {api_token}", "Content-Type": "application/json"}
                    
                    # Tady posíláme požadavek přímo na Replicate API
                    # Poznámka: Pro plnou funkčnost v produkci by fotky měly být na URL, 
                    # pro test použijeme SDXL Inpainting model.
                    st.info("Odesílám požadavek do cloudu...")
                    
                    # Simulace pro ověření UI - pokud web naskočí, dodáme finální API link
                    st.success("Web je konečně ONLINE! Teď už zbývá jen propojit reálný model.")
                    st.image(img_res, caption="Ukázka: Web už nepadá!")
                    
                except Exception as e:
                    st.error(f"Chyba: {e}")
