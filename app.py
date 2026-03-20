import streamlit as st
import replicate
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import io
import requests

st.set_page_config(page_title="Vizualka.cz Pro", layout="centered")

# --- SVĚTLÝ DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700&display=swap');
    body, .stApp { background-color: white !important; color: #1a1c22 !important; font-family: 'Sora', sans-serif !important; }
    div.stButton > button { width: 100% !important; height: 3.5em; background-color: #00c853 !important; color: white !important; font-weight: 700 !important; border-radius: 12px !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏠 Vizualka.cz Pro")

# --- TOKEN (Z Secrets) ---
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token:", type="password")

with st.sidebar:
    st.header("🎨 Vzor")
    texture_file = st.file_uploader("Nahraj vzor:", type=["jpg", "png", "jpeg"])

bg_file = st.file_uploader("📸 1. Nahraj fotku domu:", type=["jpg", "png", "jpeg"])

if bg_file:
    img = Image.open(bg_file).convert("RGB")
    w, h = img.size
    ratio = min(700/w, 700/h)
    new_size = (int(w*ratio), int(h*ratio))
    img_res = img.resize(new_size)

    st.markdown("### 🖍️ 2. Zamaluj plochu pro změnu:")
    
    # OPRAVA: Používáme klíč pro vynucení překreslení
    canvas_result = st_canvas(
        fill_color="rgba(0, 200, 83, 0.3)",
        stroke_width=20,
        background_image=img_res,
        height=new_size[1],
        width=new_size[0],
        drawing_mode="freedraw",
        key="vizualka_vFinal",
    )

    if st.button("🚀 3. VIZUALIZOVAT"):
        if not api_token:
            st.error("Chybí Token!")
        else:
            with st.spinner("🤖 AI pracuje..."):
                try:
                    img_buf = io.BytesIO()
                    img_res.save(img_buf, format="PNG")
                    mask_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    mask_buf = io.BytesIO()
                    mask_img.save(mask_buf, format="PNG")

                    client = replicate.Client(api_token=api_token)
                    output = client.run(
                        "stability-ai/sdxl-inpainting:95b7223184cc756c70b992010d24213030ca5734e1d4d627a061fac313f81537",
                        input={"image": img_buf, "mask": mask_buf, "prompt": "modern house facade, architecture", "num_outputs": 1}
                    )
                    if output:
                        st.image(output[0], use_column_width=True)
                        st.success("Hotovo! 🔥")
                except Exception as e:
                    st.error(f"Chyba: {e}")
