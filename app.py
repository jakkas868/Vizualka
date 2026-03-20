import streamlit as st
import io
import requests
import base64
import time
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- NASTAVENÍ ---
st.set_page_config(page_title="Vizualka.cz Pro", layout="centered")

# --- OPRAVA CHYBY KRESLENÍ (PATCH) ---
import streamlit.elements.image as st_image
if not hasattr(st_image, 'image_to_url'):
    def image_to_url(data, width, height, clamp, channels, output_format, image_id):
        return st.runtime.media_file_storage.get_instance().add(data, output_format, image_id)
    st_image.image_to_url = image_to_url

# --- ČISTÝ DESIGN ---
st.markdown("<style>body, .stApp { background-color: white !important; color: black !important; font-family: sans-serif; }</style>", unsafe_allow_html=True)
st.title("🏠 Vizualka.cz Pro")

# --- TOKEN (Z Secrets) ---
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token:", type="password")

# --- BOČNÍ MENU ---
with st.sidebar:
    st.header("🎨 Vzor")
    texture_file = st.file_uploader("Nahraj vzor (omítka/dřevo):", type=["jpg", "png", "jpeg"])

# --- NAHRÁNÍ FOTKY DOMU ---
bg_file = st.file_uploader("📸 1. Nahraj fotku domu:", type=["jpg", "png", "jpeg"])

if bg_file:
    img = Image.open(bg_file).convert("RGB")
    w, h = img.size
    ratio = min(700/w, 700/h)
    new_size = (int(w*ratio), int(h*ratio))
    img_res = img.resize(new_size)

    st.write("🖍️ 2. Zamaluj plochu pro změnu:")
    canvas_result = st_canvas(
        fill_color="rgba(0, 200, 83, 0.3)",
        stroke_width=20,
        background_image=img_res,
        height=new_size[1],
        width=new_size[0],
        drawing_mode="freedraw",
        key="canvas_v2026",
    )

    if st.button("🚀 3. VIZUALIZOVAT"):
        if not api_token:
            st.error("Chybí Token v nastavení (Secrets)!")
        elif not texture_file:
            st.error("Nahraj nejdřív vzor vlevo v menu!")
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
                            "prompt": "Highly detailed house facade, applying the exact texture from the reference image, hyperrealistic architectural photography",
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
                            st.success("Vizualizace hotova! 🔥")
                except Exception as e:
                    st.error(f"Chyba při volání AI: {e}")
