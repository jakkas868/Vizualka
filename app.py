import streamlit as st
import io
import requests
import base64
import time
from PIL import Image

# --- DESIGN ---
st.set_page_config(page_title="Vizualka.cz Pro | Automat", layout="centered")
st.markdown("<style>body, .stApp { background-color: white !important; color: black !important; font-family: sans-serif; }</style>", unsafe_allow_html=True)

st.title("🏠 Vizualka.cz Pro")
st.write("Automatická AI vizualizace (bez nutnosti malování).")

# --- TOKEN (Ze Secrets) ---
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token (r8_...):", type="password")

# --- NAHRÁVÁNÍ ---
col1, col2 = st.columns(2)

with col1:
    st.header("📸 1. Dům")
    bg_file = st.file_uploader("Nahraj fotku domu:", type=["jpg", "png", "jpeg"])
    if bg_file:
        st.image(bg_file, use_container_width=True)

with col2:
    st.header("🎨 2. Vzor")
    texture_file = st.file_uploader("Nahraj vzor (omítka/obklad):", type=["jpg", "png", "jpeg"])
    if texture_file:
        st.image(texture_file, use_container_width=True)

# --- VIZUALIZACE ---
if st.button("🚀 SPUSTIT VIZUALIZACI"):
    if not api_token:
        st.error("Chybí Token v nastavení!")
    elif not bg_file or not texture_file:
        st.error("Musíš nahrát dům i vzor!")
    else:
        with st.spinner("🤖 AI analyzuje dům a nanáší vzor..."):
            try:
                # Funkce pro Base64
                def img_to_b64(file):
                    return "data:image/png;base64," + base64.b64encode(file.getvalue()).decode()

                # API volání (Model SDXL - Image to Image)
                headers = {"Authorization": f"Token {api_token}", "Content-Type": "application/json"}
                
                payload = {
                    "version": "39ed52f2a78e934b3ba6e24ee33373cfaef6495f5d797ba05311261c79116ed5", # Stabilní SDXL model
                    "input": {
                        "image": img_to_b64(bg_file),
                        "prompt": "change the facade of this house to the texture and color from the reference image, high quality architecture photography, realistic",
                        "image_reference": img_to_b64(texture_file),
                        "prompt_strength": 0.45, # Jak moc má AI měnit původní fotku
                        "num_outputs": 1
                    }
                }

                resp = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload)
                data = resp.json()
                
                if "urls" in data:
                    poll_url = data["urls"]["get"]
                    while data["status"] not in ["succeeded", "failed"]:
                        time.sleep(2)
                        data = requests.get(poll_url, headers=headers).json()
                    
                    if data["status"] == "succeeded":
                        st.subheader("✨ Výsledek:")
                        st.image(data["output"][0], use_container_width=True)
                        st.success("Hotovo! AI automaticky rozpoznala fasádu.")
                    else:
                        st.error("AI se nepodařilo dům přebarvit.")
                else:
                    st.error(f"Chyba API: {data.get('detail', 'Neznámý problém')}")

            except Exception as e:
                st.error(f"Chyba: {e}")

st.markdown("---")
st.caption("© 2026 Vizualka.cz | Automatická verze")
