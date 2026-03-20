import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import io
import requests
import base64
import time

# --- DESIGN ---
st.set_page_config(page_title="Vizualka.cz Pro", layout="centered")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700&display=swap');
    body, .stApp { background-color: white !important; color: #1a1c22 !important; font-family: 'Sora', sans-serif !important; }
    div.stButton > button { width: 100% !important; height: 3.5em; background-color: #00c853 !important; color: white !important; font-weight: 700 !important; border-radius: 12px !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏠 Vizualka.cz Pro")

# --- TOKEN (Z Secrets) ---
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token (r8_...):", type="password")

bg_file = st.file_uploader("📸 1. Nahraj fotku domu:", type=["jpg", "png", "jpeg"])

if bg_file:
    img = Image.open(bg_file).convert("RGB")
    w, h = img.size
    ratio = min(800/w, 800/h)
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
        key="vizualka_vFinal_2026",
    )

    if st.button("🚀 3. VIZUALIZOVAT"):
        if not api_token:
            st.error("Chybí Token v nastavení!")
        elif canvas_result.image_data is not None:
            with st.spinner("🤖 AI právě přetírá tvůj dům..."):
                try:
                    # Příprava fotky a masky na Base64
                    def pil_to_b64(pil_img):
                        buf = io.BytesIO()
                        pil_img.save(buf, format="PNG")
                        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

                    mask_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    
                    # Volání Replicate přes API
                    model_version = "95b7223184cc756c70b992010d24213030ca5734e1d4d627a061fac313f81537"
                    url = "https://api.replicate.com/v1/predictions"
                    headers = {"Authorization": f"Token {api_token}", "Content-Type": "application/json"}
                    
                    payload = {
                        "version": model_version,
                        "input": {
                            "image": pil_to_b64(img_res),
                            "mask": pil_to_b64(mask_img),
                            "prompt": "modern house facade, architectural lighting, highly detailed",
                            "num_outputs": 1
                        }
                    }

                    response = requests.post(url, headers=headers, json=payload)
                    prediction = response.json()
                    
                    # Čekání na výsledek (polling)
                    poll_url = prediction["urls"]["get"]
                    while prediction["status"] not in ["succeeded", "failed"]:
                        time.sleep(2)
                        prediction = requests.get(poll_url, headers=headers).json()

                    if prediction["status"] == "succeeded":
                        st.subheader("✨ Výsledek:")
                        st.image(prediction["output"][0], use_container_width=True)
                        st.success("Hotovo! 🔥")
                    else:
                        st.error("AI to nezvládla, zkus to znovu.")

                except Exception as e:
                    st.error(f"Chyba: {e}")
