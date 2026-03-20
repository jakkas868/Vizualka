import streamlit as st
import replicate
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import io

st.set_page_config(page_title="Vizualka.cz Pro")

st.title("🏠 Vizualka.cz Pro")

# Token ze Secrets (nastavuje se v Dashboardu Streamlitu)
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token:", type="password")

bg_file = st.file_uploader("📸 Nahraj fotku domu:", type=["jpg", "png", "jpeg"])

if bg_file:
    img = Image.open(bg_file).convert("RGB")
    w, h = img.size
    ratio = min(700/w, 700/h)
    new_size = (int(w*ratio), int(h*ratio))
    img_res = img.resize(new_size)

    st.write("🖍️ Zamaluj plochu:")
    canvas_result = st_canvas(
        fill_color="rgba(0, 200, 83, 0.3)",
        stroke_width=20,
        background_image=img_res,
        height=new_size[1],
        width=new_size[0],
        drawing_mode="freedraw",
        key="canvas_final",
    )

    if st.button("🚀 VIZUALIZOVAT"):
        if not api_token:
            st.error("Chybí Token!")
        else:
            st.info("AI startuje...")
