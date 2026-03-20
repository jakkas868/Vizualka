import streamlit as st
import io
import requests
import base64
import time
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- OPRAVA CHYBY KRESLENÍ (PATCH PRO STARŠÍ STREAMLIT) ---
import streamlit.elements.image as st_image
if not hasattr(st_image, 'image_to_url'):
    from streamlit.runtime.media_file_storage import get_instance
    def image_to_url(data, width, height, clamp, channels, output_format, image_id):
        return get_instance().add(data, output_format, image_id)
    st_image.image_to_url = image_to_url
# --------------------------------------------------------

# --- NASTAVENÍ STRÁNKY ---
st.set_page_config(page_title="Vizualka.cz Pro", layout="wide")

# --- DESIGN A CENTROVÁNÍ (CSS) ---
st.markdown("""
    <style>
    body, .stApp { background-color: white !important; color: black !important; font-family: sans-serif; }
    h1, h2, h3, h4, h5, h6 { color: #1a1c22 !important; text-align: center; }
    p, span, div.stMarkdown, div.stText, div.stCaption { color: black !important; text-align: center; }
    
    /* Centrování nahrávače souborů a tlačítek */
    .stFileUploader, div.stButton {
        width: 100% !important;
        max-width: 600px;
        margin: 1.5em auto !important;
        display: block !important;
    }
    
    /* Zelený design pro tlačítko */
    div.stButton > button {
        width: 100% !important;
        height: 3.5em;
        background-color: #00c853 !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        border: none !important;
        display: block;
        margin: 0 auto;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏠 Vizualka.cz Pro")
st.write("Profesionální vizualizace fasády")

# --- TOKEN (Z Secrets) ---
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token:", type="password")

# --- NAHRÁVÁNÍ (Uprostřed stránky) ---
st.markdown("---")
col_upload1, col_upload2 = st.columns(2)

with col_upload1:
    bg_file = st.file_uploader("📸 Nahrajte fotku DOMU (Hlavní fotka)", type=["jpg", "png", "jpeg"], key="main_dom_upload")

with col_upload2:
    texture_file = st.file_uploader("🎨 Nahrajte fotku VZORU (Textury, omítky, obkladu)", type=["jpg", "png", "jpeg"], key="texture_upload")

if bg_file and texture_file:
    # --- PŘÍPRAVA FOTKY DOMU ---
    img = Image.open(bg_file).convert("RGB")
    w, h = img.size
    # Optimalizace velikosti pro kreslení (max 800px pro lepší detail)
    max_dim = 800
    if w > h:
        new_w, new_h = max_dim, int(h * (max_dim / w))
    else:
        new_w, new_h = int(w * (max_dim / h)), max_dim
    img_res = img.resize((new_w, new_h))

    # --- KRESLENÍ (Vycentrované) ---
    st.markdown("---")
    st.markdown("### 🖍️ Zamalujte na fotce plochu, kterou chcete změnit:")
    st.info("Obnovte stránku (Refresh), pokud dům nevidíte.")
    
    # Vycentrování kreslení
    col_c1, col_c2, col_c3 = st.columns([1, 10, 1])
    with col_c2:
        # Kreslicí plocha s JEMNĚJŠÍ ČÁROU
        canvas_result = st_canvas(
            fill_color="rgba(0, 200, 83, 0.3)",
            stroke_width=10, # 🔥 JEMNĚJŠÍ ŠTĚTEC (bylo 25) 🔥
            background_image=img_res, 
            height=new_h,
            width=new_w,
            drawing_mode="freedraw",
            # 🔥 UNIKÁTNÍ KLÍČ, KTERÝ RESETUJE KRESLENÍ PŘI ZMĚNĚ FOTKY 🔥
            key=f"pro_canvas_vFinal_{bg_file.name}",
        )

    # --- TLAČÍTKO VIZUALIZOVAT ---
    visualize_btn = st.button("🚀 VIZUALIZOVAT OZNAČENÉ")

    if visualize_btn:
        if not api_token:
            st.error("⚠️ Chybí API Token! Vložte ho v levém menu.")
        elif canvas_result.image_data is not None:
            with st.spinner("🤖 AI nanáší vzor... (může to trvat 20-30 sekund)"):
                try:
                    # Funkce pro Base64
                    def pil_to_b64(pil_img):
                        buf = io.BytesIO()
                        pil_img.save(buf, format="PNG")
                        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

                    mask_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    text_img = Image.open(texture_file).convert("RGB")
                    
                    # API volání Replicate
                    headers = {"Authorization": f"Token {api_token}", "Content-Type": "application/json"}
                    payload = {
                        "version": "95b7223184cc756c70b992010d24213030ca5734e1d4d627a061fac313f81537",
                        "input": {
                            "image": pil_to_b64(img_res),
                            "mask": pil_to_b64(mask_img),
                            "prompt": "change the facade of the house to this exact texture, highly realistic architectural photography",
                            "image_reference": pil_to_b64(text_img),
                        }
                    }

                    resp = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload)
                    data = resp.json()
                    
                    if "urls" in data:
                        poll_url = data["urls"]["get"]
                        # Čekání na výsledek
                        while data["status"] not in ["succeeded", "failed"]:
                            time.sleep(2)
                            data = requests.get(poll_url, headers=headers).json()
                        
                        if data["status"] == "succeeded":
                            st.markdown("---")
                            st.subheader("✨ Výsledek:")
                            st.image(data["output"][0], use_container_width=True)
                            st.success("Hotovo! 🔥")
                        else:
                            st.error("AI se nepodařilo obrázek vytvořit.")
                except Exception as e:
                    st.error(f"Chyba: {e}")
