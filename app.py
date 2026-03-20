import streamlit as st
import io
import requests
import base64
import time
from PIL import Image
import numpy as np

st.set_page_config(page_title="Vizualka Express", layout="centered")
st.title("🏠 Vizualka.cz - Fix Modelu")

# Token ze Secrets nebo vstupu
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token:", type="password")

st.info("Nahrajte dům, kde jste v galerii černou barvou zamalovali fasádu, a fotku vzoru.")

# --- NAHRÁVÁNÍ ---
upravena_fotka = st.file_uploader("📸 1. Dům se ZAMALOVANOU fasádou:", type=["jpg", "png", "jpeg"])
texture_file = st.file_uploader("🎨 2. Fotka VZORU (textury):", type=["jpg", "png", "jpeg"])

if upravena_fotka and texture_file:
    if st.button("🚀 SPUSTIT VIZUALIZACI", use_container_width=True):
        if not api_token:
            st.error("Chybí Token! Vložte ho do pole vlevo.")
        else:
            with st.spinner("🤖 AI pracuje na nové verzi modelu..."):
                try:
                    def prep_img(file):
                        img = Image.open(file).convert("RGB")
                        img.thumbnail((768, 768)) # Optimální pro SDXL Inpainting
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

                    # VYTVOŘENÍ MASKY Z TVÉ ČERNÉ BARVY
                    img_pil = Image.open(upravena_fotka).convert("RGB")
                    img_np = np.array(img_pil)
                    
                    # Detekce černé (vše pod prahem 50 ve všech RGB kanálech)
                    mask_np = np.where(np.all(img_np < [50, 50, 50], axis=-1), 255, 0).astype(np.uint8)
                    mask_pil = Image.fromarray(mask_np)
                    
                    buf_mask = io.BytesIO()
                    mask_pil.save(buf_mask, format="PNG")
                    mask_b64 = "data:image/png;base64," + base64.b64encode(buf_mask.getvalue()).decode()

                    headers = {"Authorization": f"Token {api_token}", "Content-Type": "application/json"}
                    
                    # 🔥 AKTUALIZOVANÝ MODEL: SDXL Inpainting (velmi stabilní) 🔥
                    payload = {
                        "version": "60e92731804d9c0250785189284240212759905d4b476726189b2513f576e27a",
                        "input": {
                            "image": prep_img(upravena_fotka),
                            "mask": mask_b64,
                            "prompt": "realistic architectural photography, replace the black painted area with this texture, high detail, 8k",
                            "image_reference": prep_img(texture_file),
                            "num_outputs": 1,
                            "guidance_scale": 7.5,
                            "num_inference_steps": 30
                        }
                    }

                    resp = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload)
                    data = resp.json()
                    
                    if "urls" in data:
                        poll_url = data["urls"]["get"]
                        for _ in range(40):
                            time.sleep(2)
                            data = requests.get(poll_url, headers=headers).json()
                            if data["status"] == "succeeded":
                                st.image(data["output"][0], use_container_width=True)
                                st.success("Hotovo! 🔥")
                                break
                            elif data["status"] == "failed":
                                st.error("Generování selhalo. Zkuste to znovu.")
                                break
                    else:
                        st.error(f"Chyba: {data.get('detail', 'Model neexistuje nebo špatný Token')}")

                except Exception as e:
                    st.error(f"Chyba: {e}")
