import streamlit as st

# --- OPRAVA PRO KRESLENÍ (PATCH) ---
try:
    import streamlit.elements.image as st_image
    if not hasattr(st_image, 'image_to_url'):
        from streamlit.runtime.media_file_storage import get_instance
        def image_to_url(data, width, height, clamp, channels, output_format, image_id):
            return get_instance().add(data, output_format, image_id)
        st_image.image_to_url = image_to_url
except Exception:
    pass

import io
import requests
import base64
import time
from PIL import Image
from streamlit_drawable_canvas import st_canvas

st.set_page_config(page_title="Vizualka.cz Pro", layout="wide")

st.title("🏠 Vizualka.cz Pro")
st.write("🖍️ Zamaluj plochu, kterou chceš změnit (např. fasádu).")

# --- TOKEN (Z Secrets) ---
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token:", type="password")

with st.sidebar:
    st.header("🎨 Vzor (Textura)")
    texture_file = st.file_uploader("Nahraj vzor:", type=["jpg", "png", "jpeg"])

bg_file = st.file_uploader("📸 Nahraj fotku domu:", type=["jpg", "png", "jpeg"])

if bg_file:
    img = Image.open(bg_file).convert("RGB")
    # Optimalizace velikosti pro kreslení
    w, h = img.size
    max_dim = 800
    if w > h:
        new_w, new_h = max_dim, int(h * (max_dim / w))
    else:
        new_w, new_h = int(w * (max_dim / h)), max_dim
    img_res = img.resize((new_w, new_h))

    # Kreslicí plocha
    canvas_result = st_canvas(
        fill_color="rgba(0, 200, 83, 0.3)",
        stroke_width=25,
        background_image=img_res,
        height=new_h,
        width=new_w,
        drawing_mode="freedraw",
        key="pro_canvas",
    )

    if st.button("🚀 VIZUALIZOVAT OZNAČENÉ"):
        if not api_token:
            st.error("Chybí API Token!")
        elif not texture_file:
            st.error("Nahraj vzor vlevo!")
        elif canvas_result.image_data is not None:
            with st.spinner("🤖 AI nanáší vzor na označenou plochu..."):
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
                            "prompt": "change the facade of the house to this exact texture, architectural photography, realistic",
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
                except Exception as e:
                    st.error(f"Chyba: {e}")
