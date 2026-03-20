import streamlit as st
import replicate
from PIL import Image, ImageDraw
from streamlit_drawable_canvas import st_canvas
import io
import requests

# --- KONFIGURACE ---
st.set_page_config(page_title="Vizualka.cz Pro", layout="centered")

# --- SVĚTLÝ DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap');
    body, .stApp { font-family: 'Sora', sans-serif !important; background-color: white !important; color: #1a1c22 !important; }
    div[data-testid="stSidebar"] { background-color: #f1f3f6 !important; }
    div.stButton > button { 
        width: 100% !important; height: 3.5em; background-color: #00c853 !important; 
        color: white !important; font-weight: 700 !important; border-radius: 12px !important; border: none !important;
    }
    .stFileUploader { border: 2px dashed #ccc !important; border-radius: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏠 Vizualka.cz Pro")

# --- TOKEN (Hledáme v Secrets nebo v UI) ---
# Tady zkoušíme, jestli už jsi ho schoval do nastavení (Secrets)
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Replicate Token:", type="password")

with st.sidebar:
    st.markdown("### 🎨 VZOR PRO FASÁDU")
    texture_file = st.file_uploader("Nahraj vzor (omítka/dřevo):", type=["jpg", "png", "jpeg"])
    watermark_text = st.text_input("Vodoznak:", "Vizualka.cz")

# --- HLAVNÍ PLOCHA ---
bg_file = st.file_uploader("📸 1. Nahraj fotku domu:", type=["jpg", "png", "jpeg"])

if bg_file:
    img = Image.open(bg_file).convert("RGB")
    w, h = img.size
    ratio = min(800/w, 800/h)
    new_size = (int(w*ratio), int(h*ratio))
    img_res = img.resize(new_size)

    st.markdown("### 🖍️ 2. Zamaluj plochu pro změnu:")
    
    # OPRAVA: Předáváme obrázek tak, aby to neházelo AttributeError
    canvas_result = st_canvas(
        fill_color="rgba(0, 200, 83, 0.3)",
        stroke_width=20,
        background_image=img_res,
        height=new_size[1],
        width=new_size[0],
        drawing_mode="freedraw",
        key="canvas_vizualka",
    )

    if st.button("🚀 3. VIZUALIZOVAT"):
        if not api_token:
            st.error("❌ Chybí Token! Vlož ho do menu nebo do Secrets.")
        elif not texture_file:
            st.error("❌ Musíš nejdřív nahrát vzor (texturu) vlevo v menu!")
        else:
            with st.spinner("🤖 AI pracuje..."):
                try:
                    # Příprava obrázků pro AI
                    img_buf = io.BytesIO()
                    img_res.save(img_buf, format="PNG")
                    
                    mask_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    mask_buf = io.BytesIO()
                    mask_img.save(mask_buf, format="PNG")
                    
                    text_img = Image.open(texture_file)
                    text_buf = io.BytesIO()
                    text_img.save(text_buf, format="PNG")

                    client = replicate.Client(api_token=api_token)
                    # Použití stabilního modelu pro inpainting
                    output = client.run(
                        "stability-ai/sdxl-inpainting:95b7223184cc756c70b992010d24213030ca5734e1d4d627a061fac313f81537",
                        input={
                            "image": img_buf,
                            "mask": mask_buf,
                            "prompt": f"facade with texture of this reference image, architectural lighting, hyperrealistic",
                            "image_reference": text_buf # Experimentální parametr
                        }
                    )
                    
                    if output:
                        st.subheader("✨ Výsledek:")
                        res = Image.open(requests.get(output[0], stream=True).raw)
                        st.image(res, use_container_width=True)
                        st.success("Hotovo! 🔥")
                except Exception as e:
                    st.error(f"Chyba: {e}")
