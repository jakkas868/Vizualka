import streamlit as st
import io
import requests
import base64
import time
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# ==================================================
# ⚡️ PATCH PRO STABILITU KRESLENÍ (STREAMLIT 1.28) ⚡️
# ==================================================
import streamlit.elements.image as st_image
if not hasattr(st_image, 'image_to_url'):
    from streamlit.runtime.media_file_storage import get_instance
    def image_to_url(data, width, height, clamp, channels, output_format, image_id):
        return get_instance().add(data, output_format, image_id)
    st_image.image_to_url = image_to_url
# ==================================================

# --- NASTAVENÍ STRÁNKY ---
st.set_page_config(page_title="Vizualka.cz Pro", layout="wide")

# Čistý bílý design a centrování prvků
st.markdown("""
    <style>
    body, .stApp { background-color: white !important; color: black !important; font-family: sans-serif; }
    h1 { color: #1a1c22 !important; text-align: center; }
    div[data-testid="stBlock"] { text-align: center; }
    /* Centrování nahrávače souborů */
    .stFileUploader { width: 60% !important; margin: 0 auto !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏠 Vizualka.cz Pro")
st.write("---")

# Token ze Secrets
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token:", type="password")

# --- KROK 1: NAHRÁVÁNÍ (Vycentrované) ---
col_u1, col_u2 = st.columns(2)
with col_u1:
    st.markdown("### 📸 Nahrajte fotku DOMU")
    bg_file = st.file_uploader("Vyberte dům:", type=["jpg", "png", "jpeg"], key="dom_upload")
with col_u2:
    st.markdown("### 🎨 Nahrajte fotku VZORU")
    texture_file = st.file_uploader("Vyberte vzor:", type=["jpg", "png", "jpeg"], key="vzor_upload")

if bg_file and texture_file:
    # Načtení fotky a optimalizace pro kreslení
    img_pil = Image.open(bg_file).convert("RGB")
    w, h = img_pil.size
    # Zvýšena maximální dimenze na 900px pro lepší detail
    max_dim = 900
    if w > h:
        new_w, new_h = max_dim, int(h * (max_dim / w))
    else:
        new_w, new_h = int(w * (max_dim / h)), max_dim
    
    img_res = img_pil.resize((new_w, new_h))

    st.markdown("---")
    st.markdown("### 🖍️ Zamalujte plochu pro změnu (např. fasádu):")
    st.info("Zkuste obtáhnout kontury fasády, AI se postará o zbytek. Pokud dům nevidíte, obnovte stránku (Refresh).")

    # --- KROK 2: KRESLENÍ (Profi Centrování) ---
    col_c1, col_c2, col_c3 = st.columns([1, 10, 1]) # Široký středový sloupec
    
    with col_c2:
        # Kreslicí plocha s JEMNĚJŠÍ ČÁROU a NOVÝM KLÍČEM
        canvas_result = st_canvas(
            fill_color="rgba(0, 200, 83, 0.3)", # Průhledná zelená pro masku
            stroke_width=12, # 🔥 JEMNĚJŠÍ ŠTĚTEC (z 25 na 12) 🔥
            background_image=img_res, 
            height=new_h,
            width=new_w,
            drawing_mode="freedraw",
            key="canvas_clean_design_v2", # Nový key vynutí reset po změně designu
        )

    st.markdown("---")
    
    # --- KROK 3: VIZUALIZACE (Vycentrované tlačítko) ---
    col_b1, col_b2, col_b3 = st.columns([2, 2, 2])
    with col_b2:
        visualize_btn = st.button("🚀 SPUSTIT VIZUALIZACI")

    if visualize_btn:
        if not api_token:
            st.error("⚠️ Chybí API Token! Vložte ho v levém menu.")
        elif not texture_file:
            st.error("⚠️ Nejdřív nahrajte vzor!")
        elif canvas_result.image_data is not None:
            # Kontrola, zda uživatel vůbec kreslil
            # canvas_result.image_data.shape[2] je 4 (RGBA)
            
            with st.spinner("🤖 AI nanáší vzor na dům... (může to trvat až 30 sekund)"):
                try:
                    # Funkce pro Base64
                    def pil_to_b64(pil_img):
                        buf = io.BytesIO()
                        pil_img.save(buf, format="PNG")
                        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

                    mask_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    text_img = Image.open(texture_file).convert("RGB")
                    
                    # API volání Replicate (Model Inpainting)
                    headers = {"Authorization": f"Token {api_token}", "Content-Type": "application/json"}
                    payload = {
                        "version": "95b7223184cc756c70b992010d24213030ca5734e1d4d627a061fac313f81537",
                        "input": {
                            "image": pil_to_b64(img_res),
                            "mask": pil_to_b64(mask_img),
                            # Prompt pro přesné nanášení textury
                            "prompt": "Apply the style and texture from the reference image to the masked area, architectural photo, highly detailed, photorealistic facade",
                            "image_reference": pil_to_b64(text_img),
                            "num_outputs": 1
                        }
                    }

                    resp = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload)
                    data = resp.json()
                    
                    if "urls" in data:
                        poll_url = data["urls"]["get"]
                        # Čekání na výsledek (polling)
                        while data["status"] not in ["succeeded", "failed"]:
                            time.sleep(2)
                            data = requests.get(poll_url, headers=headers).json()
                        
                        if data["status"] == "succeeded":
                            st.markdown("---")
                            st.subheader("✨ Výsledek:")
                            # Výsledek vycentrovaný
                            st.image(data["output"][0], use_container_width=True)
                            st.success("Hotovo! Vizualizace je na světě. 🔥")
                        else:
                            st.error("AI se nepodařilo obrázek vygenerovat, zkuste to znovu.")
                except Exception as e:
                    st.error(f"Něco se pokazilo: {e}")
else:
    st.info("Nahrajte fotku domu i vzoru a zobrazí se kreslicí plocha.")

st.markdown("---")
st.caption("© 2026 Vizualka.cz | Pro verze 1.1")
