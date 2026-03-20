import streamlit as st

# ==========================================
# ⚡️ SUPER-PATCH: OPRAVA CHYBY KRESLENÍ ⚡️
# ==========================================
try:
    import streamlit.elements.image as st_image
    def universal_image_to_url(data, width, height, clamp, channels, output_format, image_id):
        from streamlit.runtime.media_file_storage import get_instance
        return get_instance().add(data, output_format, image_id)
    
    # Vnutíme to Streamlitu natvrdo
    st_image.image_to_url = universal_image_to_url
except Exception:
    pass
# ==========================================

import io
import requests
import base64
import time
from PIL import Image
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Vizualka.cz Pro", layout="centered")

# --- DESIGN ---
st.markdown("<style>body, .stApp { background-color: white !important; color: black !important; }</style>", unsafe_allow_html=True)
st.title("🏠 Vizualka.cz Pro")

# --- TOKEN ---
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token:", type="password")

# --- BOČNÍ MENU ---
with st.sidebar:
    st.header("🎨 Vzor (Textura)")
    texture_file = st.file_uploader("Nahraj vzor:", type=["jpg", "png", "jpeg"])

# --- HLAVNÍ PLOCHA ---
bg_file = st.file_uploader("📸 1. Nahraj fotku domu:", type=["jpg", "png", "jpeg"])

if bg_file:
    img = Image.open(bg_file).convert("RGB")
    w, h = img.size
    ratio = min(700/w, 700/h)
    new_size = (int(w*ratio), int(h*ratio))
    img_res = img.resize(new_size)

    st.write("🖍️ 2. Zamaluj plochu pro změnu:")
    
    # Kreslicí plocha s novým klíčem
    canvas_result = st_canvas(
        fill_color="rgba(0, 200, 83, 0.3)",
        stroke_width=20,
        background_image=img_res,
        height=new_size[1],
        width=new_size[0],
        drawing_mode="freedraw",
        key="canvas_ultimate_fix",
    )

    if st.button("🚀 3. VIZUALIZOVAT"):
        if not api_token:
            st.error("Chybí API Token!")
        elif not texture_file:
            st.error("Chybí vzor vlevo!")
        elif canvas_result.image_data is not None:
            with st.spinner("🤖 AI pracuje..."):
                try:
                    def pil_to_b64(pil_img):
                        buf = io.BytesIO()
                        pil_img.save(buf, format="PNG")
                        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

                    mask_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    text_img = Image.open(texture_file).convert("RGB")
                    
                    headers = {"Authorization": f"Token {api_token}", "Content-Type": "application/json"}
                    payload = {
                        "version": "95b7223184cc756c70b992010d24213030ca5734e1d4d627a061fac313f81537",
                        "input": {
                            "image": pil_to_b64(img_res),
                            "mask": pil_to_b64(mask_img),
                            "prompt": "Apply the exact texture from reference image to the house facade, professional architectural photo",
                            "image_reference": pil_to_b64(text_img),
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
                            st.success("Hotovo! 🔥")
                except Exception as e:
                    st.error(f"Chyba: {e}")
