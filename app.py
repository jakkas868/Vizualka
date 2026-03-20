import streamlit as st
import io
import requests
import base64
import time
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- ⚡️ STABILIZAČNÍ PATCH PRO PYTHON 3.11 ⚡️ ---
import streamlit.elements.image as st_image
if not hasattr(st_image, 'image_to_url'):
    from streamlit.runtime.media_file_storage import get_instance
    def image_to_url(data, width, height, clamp, channels, output_format, image_id):
        return get_instance().add(data, output_format, image_id)
    st_image.image_to_url = image_to_url

# --- DESIGN ---
st.set_page_config(page_title="Vizualka.cz Pro", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: white; color: black; }
    .stMarkdown, p, h1, h3 { text-align: center; color: black !important; }
    div.stButton > button {
        background-color: #00c853 !important;
        color: white !important;
        width: 100%; max-width: 400px; height: 3.5em;
        border-radius: 12px; font-weight: bold;
        display: block; margin: 2em auto; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏠 Vizualka.cz Pro")

# Token ze Secrets
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token:", type="password")

# --- KROK 1: NAHRÁVÁNÍ ---
st.markdown("### 📸 1. Nahrajte dům a vzor")
col_u1, col_u2 = st.columns(2)
with col_u1:
    bg_file = st.file_uploader("Fotka DOMU", type=["jpg", "png", "jpeg"], key="house_up")
with col_u2:
    texture_file = st.file_uploader("Fotka VZORU", type=["jpg", "png", "jpeg"], key="tex_up")

if bg_file and texture_file:
    # Zpracování fotky domu
    img_pil = Image.open(bg_file).convert("RGB")
    w, h = img_pil.size
    max_dim = 800 # Ideální velikost, aby to mobil utáhl
    if w > h:
        new_w, new_h = max_dim, int(h * (max_dim / w))
    else:
        new_w, new_h = int(w * (max_dim / h)), max_dim
    img_res = img_pil.resize((new_w, new_h))

    st.markdown("---")
    st.markdown("### 🖍️ 2. Zamalujte plochu pro změnu")
    
    # CENTROVÁNÍ KRESBY
    _, canvas_col, _ = st.columns([1, 10, 1])
    with canvas_col:
        # KLÍČ (key) vynutí překreslení při nahrání nové fotky
        canvas_result = st_canvas(
            fill_color="rgba(0, 200, 83, 0.3)",
            stroke_width=10, # Jemná čára
            background_image=img_res,
            height=new_h,
            width=new_w,
            drawing_mode="freedraw",
            key=f"canvas_{bg_file.name}", 
        )

    # --- KROK 3: VIZUALIZACE ---
    if st.button("🚀 SPUSTIT VIZUALIZACI"):
        if not api_token:
            st.error("Chybí Token!")
        elif canvas_result.image_data is not None:
            with st.spinner("🤖 AI pracuje..."):
                try:
                    def pil_to_b64(pil_img):
                        buf = io.BytesIO()
                        pil_img.save(buf, format="PNG")
                        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

                    mask_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    
                    headers = {"Authorization": f"Token {api_token}", "Content-Type": "application/json"}
                    payload = {
                        "version": "95b7223184cc756c70b992010d24213030ca5734e1d4d627a061fac313f81537",
                        "input": {
                            "image": pil_to_b64(img_res),
                            "mask": pil_to_b64(mask_img),
                            "prompt": "Apply the texture from reference image to the house facade, highly realistic architectural photography",
                            "image_reference": pil_to_b64(Image.open(texture_file).convert("RGB")),
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
                            st.markdown("---")
                            st.subheader("✨ Výsledek:")
                            st.image(data["output"][0], use_container_width=True)
                            st.success("Vizualizace hotova! 🔥")
                except Exception as e:
                    st.error(f"Chyba: {e}")
