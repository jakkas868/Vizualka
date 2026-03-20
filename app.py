import streamlit as st
import replicate
from PIL import Image, ImageDraw
from streamlit_drawable_canvas import st_canvas
import io
import requests

# --- NASTAVENÍ ---
st.set_page_config(page_title="Vizualka.cz | AI Pro", layout="centered")

# --- MODERNÍ DESIGN (Dark Mode) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap');
    body, .stApp { font-family: 'Sora', sans-serif !important; background-color: #0c0d10 !important; color: #f8f9fa !important; }
    .stFileUploader, div[data-testid="stSidebar"], .stButton > button, canvas { border-radius: 12px !important; }
    div.stButton > button { width: 100% !important; height: 3.5em; font-size: 1.2rem !important; background-color: #00c853 !important; color: white !important; font-weight: 700 !important; border: none !important; }
    div.stButton > button:hover { background-color: #00e676 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏠 Vizualka.cz")
st.markdown("<p style='color: #ccc;'>Nahrajte fotku, zamalujte plochu a vizualizujte změnu.</p>", unsafe_allow_html=True)

# --- BOČNÍ MENU ---
with st.sidebar:
    st.header("⚙️ Nastavení")
    api_token = st.text_input("Vlož Replicate Token (r8_...):", type="password")
    prompt = st.text_input("Zadání pro AI:", "modern house facade, elegant grey plaster, detailed texture")
    watermark = st.text_input("Tvůj vodoznak:", "Vizualka.cz")

# --- LOGIKA APLIKACE ---
uploaded_file = st.file_uploader("📸 Nahrajte fotku baráku:", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    # Optimalizace pro AI (max 1024px)
    w, h = img.size
    ratio = min(1024/w, 1024/h)
    new_size = (int(w*ratio), int(h*ratio))
    img_res = img.resize(new_size)

    st.subheader("🖍️ Zamalujte plochu, kterou chcete změnit:")
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.4)", # Oranžová maska
        stroke_width=20,
        background_image=img_res,
        height=new_size[1],
        width=new_size[0],
        drawing_mode="freedraw",
        key="canvas",
    )

    if st.button("🚀 VIZUALIZOVAT"):
        if not api_token:
            st.error("⚠️ Chybí Replicate Token v bočním menu!")
        elif canvas_result.image_data is not None:
            with st.spinner("🤖 AI právě přetírá váš dům..."):
                # 1. Příprava fotky a masky
                img_byte = io.BytesIO()
                img_res.save(img_byte, format='PNG')
                
                mask_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                mask_byte = io.BytesIO()
                mask_img.save(mask_byte, format='PNG')

                try:
                    # 2. Volání AI modelu (SDXL Inpainting)
                    client = replicate.Client(api_token=api_token)
                    output = client.run(
                        "stability-ai/sdxl-inpainting:95b7223184cc756c70b992010d24213030ca5734e1d4d627a061fac313f81537",
                        input={
                            "image": img_byte,
                            "mask": mask_byte,
                            "prompt": prompt,
                            "negative_prompt": "distorted, ugly, blurry, low quality",
                            "num_outputs": 1
                        }
                    )
                    
                    if output:
                        st.subheader("✨ Výsledek:")
                        res_img = Image.open(requests.get(output[0], stream=True).raw)
                        
                        # 3. Přidání vodoznaku
                        draw = ImageDraw.Draw(res_img)
                        draw.text((20, 20), watermark, fill=(255, 255, 255, 128))
                        
                        st.image(res_img, use_container_width=True)
                        st.success("Hotovo! 🔥")
                except Exception as e:
                    st.error(f"Chyba při volání AI: {e}")

st.markdown("<hr style='border-color: #2c2f37;'>", unsafe_allow_html=True)
st.caption("© 2026 Vizualka.cz")
