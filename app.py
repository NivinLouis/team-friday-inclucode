import os
import tempfile

import streamlit as st
from pose_format.pose_visualizer import PoseVisualizer

from spoken_to_signed.bin import _text_to_gloss, _gloss_to_pose

# --- CUSTOM CSS FOR SLEEK MODERN DARK DESIGN ---
st.set_page_config(
    page_title="Spoken-to-Signed Translator",
    page_icon="🖐️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Space+Grotesk:wght@400;600&display=swap');

    /* Global Overrides */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(18, 18, 24) 0%, rgb(8, 8, 12) 90%);
        color: #f1f3f9;
    }

    /* Cards / Containers styling */
    .premium-card {
        background: rgba(30, 30, 42, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(12px);
        transition: all 0.3s ease;
    }
    .premium-card:hover {
        border-color: rgba(144, 97, 249, 0.3);
        box-shadow: 0 8px 40px 0 rgba(144, 97, 249, 0.15);
    }

    /* Titles and text overrides */
    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        background: linear-gradient(135deg, #a78bfa 0%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Gloss pill tags */
    .gloss-pill {
        display: inline-block;
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(236, 72, 153, 0.2) 100%);
        border: 1px solid rgba(139, 92, 246, 0.4);
        color: #ddd6fe;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 14px;
        padding: 6px 14px;
        margin: 6px;
        border-radius: 30px;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.15);
        animation: floatPill 3s ease-in-out infinite alternate;
    }

    @keyframes floatPill {
        0% { transform: translateY(0px); }
        100% { transform: translateY(-2px); }
    }
    
    /* Input areas */
    .stTextArea textarea {
        background-color: rgba(15, 15, 25, 0.8) !important;
        color: #f1f3f9 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
    }
    .stTextArea textarea:focus {
        border-color: #a78bfa !important;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR CONFIGURATION ---
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    st.write("**Spoken Language**: `English (en)`")
    st.write("**Sign Language**: `American Sign Language (ase)`")
    st.write("**Glosser**: `rules`")
    disable_fs = st.checkbox("Disable fingerspelling fallback", value=False)

spoken_code = "en"
signed_code = "ase"
lexicon_dir = "assets/dummy_lexicon_en"

# --- MAIN APP LAYOUT ---
st.title("🖐️ Spoken-to-Signed Translation Pipeline")
st.markdown("Translate spoken text into **Sign Language Glosses** and visual **Skeletal Pose Motions**.")

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Input Text")
    
    default_text = "Children eat pizza."
    input_text = st.text_area("Type your sentence here:", value=default_text, height=120)
    
    translate_btn = st.button("🚀 Translate Sentence", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="premium-card">', unsafe_allow_html=True)
    st.markdown("### 📊 Translation Metadata")
    st.write("**Spoken Language**: `English (en)`")
    st.write("**Sign Language**: `American Sign Language (ase)`")
    st.write("**Glosser Engine**: `rules`")
    st.write(f"**Lexicon Path**: `{lexicon_dir}`")
    st.info(
        "The bundled English demo lexicon is intentionally tiny. Unknown words will fall back to the "
        "bundled fingerspelling poses."
    )
    st.markdown('</div>', unsafe_allow_html=True)

# --- EXECUTION PIPELINE ---
if translate_btn and input_text:
    try:
        with st.spinner("Step 1/3: Converting spoken text to glosses..."):
            sentences = _text_to_gloss(
                text=input_text,
                language=spoken_code,
                signed_language=signed_code
            )
        
        # Display Glosses
        st.markdown('<div class="premium-card">', unsafe_allow_html=True)
        st.markdown("### 🏷️ Generated Gloss Sequence")
        
        all_gloss_items = [item for sent in sentences for item in sent]
        pills_html = "".join([f'<span class="gloss-pill">{item.gloss}</span>' for item in all_gloss_items])
        st.markdown(pills_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.spinner("Step 2/3: Converting glosses to pose skeletal frames..."):
            # Convert gloss to pose
            result = _gloss_to_pose(
                sentences=sentences,
                lexicon=lexicon_dir,
                spoken_language=spoken_code,
                signed_language=signed_code,
                disable_fingerspelling=disable_fs
            )
            
        with st.spinner("Step 3/3: Rendering skeleton animation..."):
            # Render pose frames to GIF
            visualizer = PoseVisualizer(result.pose)
            # Draw frame arrays
            frames = list(visualizer.draw(background_color=(18, 18, 24)))
            
            # Save visualizer gif bytes
            with tempfile.NamedTemporaryFile(delete=False, suffix=".gif") as temp_gif:
                visualizer.save_gif(temp_gif.name, frames)
                with open(temp_gif.name, "rb") as gif_f:
                    gif_bytes = gif_f.read()
                try:
                    os.unlink(temp_gif.name)
                except:
                    pass

        # Display result layout
        col_res1, col_res2 = st.columns([1, 1])
        
        with col_res1:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.markdown("### 🎬 Skeletal Motion Preview")
            st.image(gif_bytes, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_res2:
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.markdown("### 📥 Download Results")
            
            # Pose file bytes
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pose") as temp_pose:
                result.pose.write(temp_pose)
                with open(temp_pose.name, "rb") as pose_f:
                    pose_bytes = pose_f.read()
                try:
                    os.unlink(temp_pose.name)
                except:
                    pass
                    
            st.download_button(
                label="📥 Download Skeleton (.pose) File",
                data=pose_bytes,
                file_name="sign_language.pose",
                mime="application/octet-stream",
                use_container_width=True
            )
            
            st.download_button(
                label="📥 Download Skeletal GIF Preview",
                data=gif_bytes,
                file_name="sign_language.gif",
                mime="image/gif",
                use_container_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"⚠️ Error running pipeline: {str(e)}")
        st.info("Ensure the English spaCy model is available and that the ASL demo lexicon assets are present.")
