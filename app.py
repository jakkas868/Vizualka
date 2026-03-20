import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import io
import requests
import base64
import time

# --- DESIGN (Světlý profi styl) ---
st.set_page_config(page_title="Vizualka.cz Pro", layout="centered")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;700&display=swap');
    body, .stApp { background-color: white !important; color: #1a1c22 !important; font-family: 'Sora', sans-serif !important; }
    div[data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 1px solid #eee !important; }
    div.stButton > button { width: 100% !important; height: 3.5em; background-color: #00c853 !important; color: white !important; font-weight: 700 !important; border-radius: 12px !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏠 Vizualka.cz Pro")

# --- TOKEN (Z Secrets nebo pole) ---
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token (r8_...):", type="password")

# --- SIDEBAR PRO VZOR ---
with st.sidebar:
    st.header("🎨 Váš vzor")
    texture_file = st.file_uploader("Nahrajte vzor (omítka/dřevo):", type=["jpg", "png", "jpeg"])
    if texture_file:
        st.image(texture_file, caption="Vybraný vzor", use_container_width=True)
    st.markdown("---")
    watermark_text = st.text_input("Vodoznak:", "Vizualka.cz")

# --- HLAVNÍ NAHRÁVÁNÍ DOMU ---
bg_file = st.file_uploader("📸 1. Nahrajte fotku domu:", type=["jpg", "png", "jpeg"])

if bg_file:
    img = Image.open(bg_file).convert("RGB")
    w, h = img.size
    ratio = min(800/w, 800/h)
    new_size = (int(w*ratio), int(h*ratio))
    img_res = img.resize(new_size)

    st.write("🖍️ 2. Zamalujte plochu pro změnu:")
    canvas_result = st_canvas(
        fill_color="rgba(0, 200, 83, 0.3)",
        stroke_width=20,
        background_image=img_res,
        height=new_size[1],
        width=new_size[0],
        drawing_mode="freedraw",
        key="vizualka_vFinal_vzor",
    )

    if st.button("🚀 3. VIZUALIZOVAT"):
        if not api_token:
            st.error("⚠️ Chybí Token v nastavení!")
        elif not texture_file:
            st.error("⚠️ Nejdřív nahrajte vzor v levém menu!")
        elif canvas_result.image_data is not None:
            with st.spinner("🤖 AI nanáší váš vzor na dům..."):
                try:
                    # Funkce pro převod na Base64
                    def pil_to_b64(pil_img):
                        buf = io.BytesIO()
                        pil_img.save(buf, format="PNG")
                        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

                    mask_img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    text_img = Image.open(texture_file).convert("RGB")
                    
                    # API volání Replicate
                    headers = {"Authorization": f"Token {api_token}", "Content-Type": "application/json"}
                    payload = {
                        "version": "95b7223184cc756c70b992010d24213030ca5734e1d4d627a061fac313f81537",
                        "input": {
                            "image": pil_to_b64(img_res),
                            "mask": pil_to_b64(mask_img),
                            # Do promptu napíšeme, aby AI použila texturu
                            "prompt": "Apply the style and texture from the reference image to the masked area, architectural photorealistic facade",
                            "image_reference": pil_to_b64(text_img), # Tady posíláme ten tvůj vzor
                            "num_outputs": 1
                        }
                    }

                    resp = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload)
                    prediction = resp.json()
                    
                    # Čekání na výsledek
                    poll_url = prediction["urls"]["get"]
                    while prediction["status"] not in ["succeeded", "failed"]:
                        time.sleep(2)
                        prediction = requests.get(poll_url, headers=headers).json()

                    if prediction["status"] == "succeeded":
                        st.subheader("✨ Výsledek:")
                        st.image(prediction["output"][0], use_container_width=True)
                        st.success("Hotovo! 🔥")
                    else:
                        st.error("AI se nepodařilo obrázek vytvořit.")

                except Exception as e:
                    st.error(f"Něco se pokazilo: {e}")
