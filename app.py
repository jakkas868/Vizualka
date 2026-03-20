import streamlit as st
import io
import requests
import base64
import time
from PIL import Image
import numpy as np

st.set_page_config(page_title="Vizualka Express", layout="centered")
st.title("🏠 Vizualka.cz - Rychlá maska")

api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token:", type="password")

st.markdown("""
1. V galerii mobilu vezmi fotku domu a **černým štětcem** zamaluj fasádu.
2. Tuto upravenou fotku nahraj do prvního pole.
""")

# --- NAHRÁVÁNÍ ---
upravena_fotka = st.file_uploader("📸 1. Nahraj dům se ZAMALOVANOU fasádou:", type=["jpg", "png", "jpeg"])
texture_file = st.file_uploader("🎨 2. Nahraj fotku VZORU:", type=["jpg", "png", "jpeg"])

if upravena_fotka and texture_file:
    if st.button("🚀 SPUSTIT VIZUALIZACI", use_container_width=True):
        if not api_token:
            st.error("Chybí Token!")
        else:
            with st.spinner("🤖 AI kouzlí..."):
                try:
                    # Funkce pro převod a zmenšení
                    def prep_img(file):
                        img = Image.open(file).convert("RGB")
                        img.thumbnail((800, 800))
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

                    # VYTVOŘENÍ MASKY Z ČERNÉ BARVY
                    # AI potřebuje vědět, kde přesně jsi maloval černou
                    img_pil = Image.open(upravena_fotka).convert("RGB")
                    img_np = np.array(img_pil)
                    
                    # Najdeme pixely, které jsou skoro černé (v galerii mobilu to nebývá čistá 0,0,0)
                    mask_np = np.where(np.all(img_np < [50, 50, 50], axis=-1), 255, 0).astype(np.uint8)
                    mask_pil = Image.fromarray(mask_np)
                    
                    buf_mask = io.BytesIO()
                    mask_pil.save(buf_mask, format="PNG")
                    mask_b64 = "data:image/png;base64," + base64.b64encode(buf_mask.getvalue()).decode()

                    headers = {"Authorization": f"Token {api_token}", "Content-Type": "application/json"}
                    payload = {
                        "version": "95b7223184cc756c70b992010d24213030ca5734e1d4d627a061fac313f81537",
                        "input": {
                            "image": prep_img(upravena_fotka),
                            "mask": mask_b64,
                            "prompt": "highly realistic architectural photography, replace the black painted area with this texture, 8k resolution",
                            "image_reference": prep_img(texture_file),
                        }
                    }

                    resp = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload)
                    data = resp.json()
                    
                    if "urls" in data:
                        poll_url = data["urls"]["get"]
                        # Prodloužený polling na 60 sekund
                        for _ in range(30):
                            time.sleep(2)
                            data = requests.get(poll_url, headers=headers).json()
                            if data["status"] == "succeeded":
                                st.image(data["output"][0], use_container_width=True)
                                st.success("Vizualizace je hotová! 🔥")
                                break
                            elif data["status"] == "failed":
                                st.error("AI generování selhalo.")
                                break
                    else:
                        st.error(f"Chyba serveru: {data.get('detail', 'Neznámá chyba')}")

                except Exception as e:
                    st.error(f"Chyba v aplikaci: {e}")

st.write("---")
st.caption("Tip: Pokud AI nic nevyhodí, zkontroluj na Replicate.com, jestli ti neprošel limit nebo není výpadek.")
