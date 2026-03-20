import streamlit as st
import io
import requests
import base64
import time
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- OPRAVA CHYBY KRESLENÍ (PATCH PRO STARŠÍ STREAMLIT) ---
try:
    import streamlit.elements.image as st_image
    if not hasattr(st_image, 'image_to_url'):
        from streamlit.runtime.media_file_storage import get_instance
        def image_to_url(data, width, height, clamp, channels, output_format, image_id):
            return get_instance().add(data, output_format, image_id)
        st_image.image_to_url = image_to_url
except Exception:
    pass
# --------------------------------------------------------

# --- NASTAVENÍ STRÁNKY ---
st.set_page_config(page_title="Vizualka.cz Pro", layout="wide")
st.title("🏠 Vizualka.cz Pro")
st.write("Profesionální vizualizace fasády")

# --- TOKEN (Z Secrets nebo pole) ---
api_token = st.secrets.get("REPLICATE_API_TOKEN") or st.sidebar.text_input("Vlož Token:", type="password")

# --- KROK 1: NAHRÁVÁNÍ FOTEK (Uprostřed stránky) ---
st.markdown("---")
col_upload1, col_upload2 = st.columns(2)

with col_upload1:
    bg_file = st.file_uploader("📸 1. Nahrajte fotku DOMU (Hlavní fotka)", type=["jpg", "png", "jpeg"])

with col_upload2:
    texture_file = st.file_uploader("🎨 2. Nahrajte fotku VZORU (Textury, omítky, obkladu)", type=["jpg", "png", "jpeg"])

if bg_file and texture_file:
    # --- PŘÍPRAVA FOTKY DOMU ---
    img = Image.open(bg_file).convert("RGB")
    w, h = img.size
    # Optimalizace velikosti pro kreslení (max 800px)
    max_dim = 800
    if w > h:
        new_w, new_h = max_dim, int(h * (max_dim / w))
    else:
        new_w, new_h = int(w * (max_dim / h)), max_dim
    img_res = img.resize((new_w, new_h))

    # 🔥 KLÍČOVÝ FIX PRO MOBILE: Převedeme fotku na Base64 string 🔥
    buffered = io.BytesIO()
    img_res.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()
    background_data_url = f"data:image/png;base64,{img_b64}"

    # --- KROK 2: KRESLENÍ ---
    st.markdown("---")
    st.markdown("### 🖍️ 3. Zamalujte na fotce plochu, kterou chcete změnit:")
    
    # Používáme Base64 string jako background_image
    canvas_result = st_canvas(
        fill_color="rgba(0, 200, 83, 0.3)",
        stroke_width=25,
        background_image=background_data_url, # Tady používáme ten zakódovaný string
        height=new_h,
        width=new_w,
        drawing_mode="freedraw",
        key="final_mobile_fix_canvas",
    )

    # --- VOD_ZNAK ---
    with st.sidebar:
        watermark_text = st.text_input("Zadejte vodoznak na výsledek:", "Vizualka.cz")
        st.caption("Verze: 1.0 Pro")

    # --- TLAČÍTKO VIZUALIZOVAT ---
    if st.button("🚀 4. VIZUALIZOVAT"):
        if not api_token:
            st.error("⚠️ Chybí API Token! Vložte ho v levém menu.")
        elif canvas_result.image_data is not None:
            with st.spinner("🤖 AI nanáší vzor na označenou plochu... Může to trvat až 30 sekund."):
                try:
                    # Funkce pro převod PIL na Base64
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
                            # Lepší prompt pro přesné nanášení textury
                            "prompt": f"change the facade of the house to the texture from the reference image, high quality architectural photography, realistic facade with prompt strength, {watermark_text}",
                            "image_reference": pil_to_b64(text_img),
                            "negative_prompt": "cartoon, painting, abstract, blurry",
                            "num_outputs": 1
                        }
                    }

                    resp = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload)
                    data = resp.json()
                    
                    if "urls" in data:
                        poll_url = data["urls"]["get"]
                        # Čekání na výsledek
                        while data["status"] not in ["succeeded", "failed"]:
                            time.sleep(3) # Zvýšené čekání
                            data = requests.get(poll_url, headers=headers).json()
                        
                        if data["status"] == "succeeded":
                            st.markdown("---")
                            st.subheader("✨ Výsledek:")
                            # Výsledek roztáhneme na celou šířku
                            st.image(data["output"][0], use_container_width=True)
                            st.success("Hotovo! Vizualizace je hotova. 🔥")
                        else:
                            st.error("AI se nepodařilo obrázek vygenerovat, zkuste to znovu.")
                    else:
                        st.error(f"AI selhala: {data.get('detail', 'Neznámý problém')}")

                except Exception as e:
                    st.error(f"Něco se pokazilo: {e}")
else:
    st.info("Nahrajte obě fotky (dům i vzor) a automaticky se zobrazí kreslicí plocha.")
