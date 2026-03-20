import streamlit as st
import io
import requests
import base64
import time
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- FIX PRO ZOBRAZENÍ V PYTHONU 3.11 ---
import streamlit.elements.image as st_image
if not hasattr(st_image, 'image_to_url'):
    from streamlit.runtime.media_file_storage import get_instance
    def image_to_url(data, width, height, clamp, channels, output_format, image_id):
        return get_instance().add(data, output_format, image_id)
    st_image.image_to_url = image_to_url

st.set_page_config(page_title="Vizualka Pro", layout="centered")

st.title("🏠 Vizualka.cz Pro")

# Token
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token:", type="password")

# --- NAHRÁVÁNÍ ---
bg_file = st.file_uploader("📸 1. Nahrajte fotku domu:", type=["jpg", "png", "jpeg"], key="h_up")
texture_file = st.file_uploader("🎨 2. Nahrajte fotku vzoru:", type=["jpg", "png", "jpeg"], key="t_up")

if bg_file and texture_file:
    # Načtení a zmenšení fotky
    img_pil = Image.open(bg_file).convert("RGB")
    w, h = img_pil.size
    
    # Menší rozlišení pro absolutní stabilitu na mobilu
    max_dim = 500 
    if w > h:
        new_w, new_h = max_dim, int(h * (max_dim / w))
    else:
        new_w, new_h = int(w * (max_dim / h)), max_dim
    img_res = img_pil.resize((new_w, new_h))

    st.markdown("---")
    st.write("### 🖍️ 3. Zamalujte plochu pro změnu:")

    # Kreslicí plocha - teď posíláme přímo img_res
    canvas_result = st_canvas(
        fill_color="rgba(0, 200, 83, 0.3)",
        stroke_width=10,
        background_image=img_res, # TADY JE TA OPRAVA
        height=new_h,
        width=new_w,
        drawing_mode="freedraw",
        key=f"canvas_v311_{bg_file.name}", 
    )

    if st.button("🚀 4. SPUSTIT VIZUALIZACI", use_container_width=True):
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
                            "prompt": "realistic architectural photo, apply texture to facade",
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
                            st.image(data["output"][0], use_container_width=True)
                            st.success("Hotovo! 🔥")
                except Exception as e:
                    st.error(f"Chyba: {e}")
