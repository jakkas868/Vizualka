import streamlit as st
import replicate
from PIL import Image, ImageDraw
from streamlit_drawable_canvas import st_canvas
import io
import requests

# --- NASTAVENÍ STRÁNKY ---
st.set_page_config(page_title="Vizualka.cz Pro", layout="centered")

# --- CSS TUNING (Světlý, čistý, vysoký kontrast) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&display=swap');
    
    /* Světlé pozadí a tmavý text */
    body, .stApp { font-family: 'Sora', sans-serif !important; background-color: #ffffff !important; color: #1a1c22 !important; }
    
    /* Sidebar - světle šedý pro oddělení */
    div[data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 1px solid #eeeeee !important; }
    div[data-testid="stSidebar"] .stMarkdown, div[data-testid="stSidebar"] label { color: #1a1c22 !important; font-weight: 600; }

    /* Karty pro nahrávání - bílé se stínem */
    .stFileUploader { background-color: #ffffff !important; border: 2px dashed #dddddd !important; border-radius: 15px !important; padding: 20px; }
    
    /* Hlavní zelené tlačítko - musí zářit */
    div.stButton > button { 
        width: 100% !important; 
        height: 3.8em; 
        font-size: 1.2rem !important; 
        background-color: #00c853 !important; 
        color: white !important; 
        font-weight: 700 !important; 
        border: none !important; 
        border-radius: 12px !important; 
        box-shadow: 0 4px 15px rgba(0, 200, 83, 0.3);
        text-transform: uppercase;
    }
    div.stButton > button:hover { background-color: #00b44a !important; box-shadow: 0 6px 20px rgba(0, 200, 83, 0.4); }

    /* Nadpisy */
    h1 { font-weight: 800 !important; color: #000000 !important; letter-spacing: -1px; }
    h2, h3 { color: #1a1c22 !important; }
    
    /* Vstupy (Token, Prompt) */
    input { background-color: #ffffff !important; border: 1px solid #cccccc !important; border-radius: 8px !important; color: #000000 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- HLAVNÍ HLAVIČKA ---
st.title("🏠 Vizualka.cz Pro")
st.markdown("<p style='font-size: 1.2rem; color: #555;'>Prémiový nástroj pro řemeslníky a architekty.</p>", unsafe_allow_html=True)

# --- SIDEBAR (Světlý) ---
with st.sidebar:
    st.markdown("### ⚙️ NASTAVENÍ")
    api_token = st.text_input("Vlož Replicate Token:", type="password", help="Tvůj klíč z replicate.com")
    
    st.markdown("---")
    st.markdown("### 🎨 VZOR / TEXTURA")
    texture_file = st.file_uploader("Nahraj vzor (omítka, dřevo...)", type=["jpg", "jpeg", "png"])
    if texture_file:
        st.image(texture_file, caption="Tvůj vybraný vzor", use_container_width=True)

    st.markdown("---")
    watermark_text = st.text_input("Text vodoznaku:", "Vizualka.cz")

# --- HLAVNÍ PLOCHA ---
uploaded_file = st.file_uploader("📸 1. KROK: Nahraj fotku domu nebo místnosti", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    w, h = img.size
    ratio = min(1024/w, 1024/h)
    new_size = (int(w*ratio), int(h*ratio))
    img_res = img.resize(new_size)

    st.markdown("### 🖍️ 2. KROK: Zamaluj plochu pro změnu")
    canvas_result = st_canvas(
        fill_color="rgba(0, 200, 83, 0.3)", # Světle zelená maska, lépe vidět na světlém
        stroke_width=20,
        background_image=img_res,
        height=new_size[1],
        width=new_size[0],
        drawing_mode="freedraw",
        key="canvas",
    )

    if st.button("🚀 3. KROK: VIZUALIZOVAT"):
        if not api_token:
            st.error("❌ Chybí API Token v levém menu!")
        elif not texture_file:
            st.error("❌ Musíš nejdřív nahrát vzor (texturu) v levém menu!")
        elif canvas_result.image_data is not None:
            with st.spinner("🤖 AI nanáší tvůj vzor..."):
                # Příprava dat
                img_byte = io.BytesIO()
                img_res.save(img_byte, format='PNG')
                
                mask_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                mask_byte = io.BytesIO()
                mask_img.save(mask_byte, format='PNG')
                
                texture_img = Image.open(texture_file)
                texture_byte = io.BytesIO()
                texture_img.save(texture_byte, format='PNG')

                try:
                    client = replicate.Client(api_token=api_token)
                    output = client.run(
                        "cjwbw/inpainting-high-resolution:f00c7a88481458e08d666b6c0e5a9c0c889f0a400c9e6d03d494f6f4f1d4b684",
                        input={
                            "image": img_byte,
                            "mask": mask_byte,
                            "texture_image": texture_byte,
                            "prompt": "Professional architectural visualization, apply texture to facade, realistic daylight, 8k",
                            "negative_prompt": "blurry, distorted, low quality, bad shadows",
                        }
                    )
                    
                    if output:
                        st.markdown("### ✨ VÝSLEDEK")
                        final_res = Image.open(requests.get(output[0], stream=True).raw)
                        
                        # Vodoznak
                        draw = ImageDraw.Draw(final_res)
                        draw.text((30, 30), watermark_text, fill=(255, 255, 255, 150))
                        
                        st.image(final_res, use_container_width=True)
                        st.success("Hotovo! Teď to ukaž zákazníkovi. 🎯")
                except Exception as e:
                    st.error(f"Chyba: {e}")

st.markdown("<br><hr><center>© 2026 Vizualka.cz Pro</center>", unsafe_allow_html=True)
