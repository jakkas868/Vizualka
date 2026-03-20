import streamlit as st
import io
import requests
import base64
import time
from PIL import Image

st.set_page_config(page_title="Vizualka Maska", layout="centered")
st.title("🏠 Vizualka.cz Pro (Verze s Maskou)")

api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token:", type="password")

st.info("Nahrajte fotku domu, vzoru a masku z galerie.")

# --- NAHRÁVÁNÍ 3 SOUBORŮ ---
col1, col2 = st.columns(2)
with col1:
    bg_file = st.file_uploader("📸 1. Fotka domu:", type=["jpg", "png", "jpeg"])
with col2:
    texture_file = st.file_uploader("🎨 2. Fotka vzoru:", type=["jpg", "png", "jpeg"])

mask_file = st.file_uploader("🌑 3. Nahrajte MASKU z galerie (zamalovanou fasádu):", type=["jpg", "png", "jpeg"])

if bg_file and texture_file and mask_file:
    st.success("Všechny soubory nahrány! Můžete spustit vizualizaci.")
    
    if st.button("🚀 SPUSTIT VIZUALIZACI", use_container_width=True):
        if not api_token:
            st.error("Chybí Token!")
        else:
            with st.spinner("🤖 AI nanáší vzor na dům..."):
                try:
                    def pil_to_b64(file):
                        img = Image.open(file).convert("RGB")
                        # Zmenšíme pro stabilitu na mobilu
                        img.thumbnail((1024, 1024))
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

                    headers = {"Authorization": f"Token {api_token}", "Content-Type": "application/json"}
                    
                    # API volání pro inpainting
                    payload = {
                        "version": "95b7223184cc756c70b992010d24213030ca5734e1d4d627a061fac313f81537",
                        "input": {
                            "image": pil_to_b64(bg_file),
                            "mask": pil_to_b64(mask_file),
                            "prompt": "Highly realistic architectural photography, perfectly apply the texture from reference image to the wall, windows and roof remain the same",
                            "image_reference": pil_to_b64(texture_file),
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
                            # Výsledek vycentrovaný na celou šířku
                            st.image(data["output"][0], use_container_width=True)
                            st.success("Hotovo! 🔥")
                except Exception as e:
                    st.error(f"Chyba: {e}")
