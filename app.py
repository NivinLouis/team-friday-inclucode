import os
import tempfile

import streamlit as st
from pose_format.pose_visualizer import PoseVisualizer

from spoken_to_signed.bin import _text_to_gloss, _gloss_to_pose

st.set_page_config(
    page_title="Friday - Text to Pose Generator Test",
    page_icon="🤟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("**Settings**")
    st.caption("Language: English → ISL")

spoken_code = "en"
signed_code = "ins"  # ISL first; falls back to ASL (ase) via LANGUAGE_BACKUP, then fingerspelling
lexicon_dir = "assets/dummy_lexicon_en"

# --- HEADER ---
st.title("Friday - Text to Pose Generator")
st.divider()

# --- TWO-COLUMN LAYOUT ---
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("Input")
    default_text = "Children eat pizza."
    input_text = st.text_area(
        "Sentence",
        value=default_text,
        height=140,
        label_visibility="collapsed",
        placeholder="Type a sentence…",
    )
    translate_btn = st.button("Translate →", type="primary")
    disable_fs = st.checkbox("Disable fingerspelling fallback", value=False)

    # Gloss sequence — shown after translate, below lookup priority
    if translate_btn and input_text:
        try:
            with st.spinner("Generating glosses…"):
                sentences = _text_to_gloss(
                    text=input_text,
                    language=spoken_code,
                    signed_language=signed_code,
                )
            st.divider()
            st.subheader("Generated Gloss sequence")
            all_gloss_items = [item for sent in sentences for item in sent]
            st.write(" · ".join([item.gloss for item in all_gloss_items]))
        except Exception as e:
            st.error(str(e))
            sentences = None
    else:
        sentences = None

# Right column — pose preview and downloads
with col_right:
    if translate_btn and input_text and sentences is not None:
        try:
            with st.spinner("Building pose…"):
                result = _gloss_to_pose(
                    sentences=sentences,
                    lexicon=lexicon_dir,
                    spoken_language=spoken_code,
                    signed_language=signed_code,
                    disable_fingerspelling=disable_fs,
                )

            with st.spinner("Rendering…"):
                visualizer = PoseVisualizer(result.pose)
                frames = list(visualizer.draw(background_color=(14, 17, 23)))
                with tempfile.NamedTemporaryFile(delete=False, suffix=".gif") as tmp_gif:
                    visualizer.save_gif(tmp_gif.name, frames)
                    with open(tmp_gif.name, "rb") as f:
                        gif_bytes = f.read()
                    try:
                        os.unlink(tmp_gif.name)
                    except Exception:
                        pass

            st.subheader("Preview")
            st.image(gif_bytes, use_container_width=True)

            st.divider()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pose") as tmp_pose:
                result.pose.write(tmp_pose)
                with open(tmp_pose.name, "rb") as f:
                    pose_bytes = f.read()
                try:
                    os.unlink(tmp_pose.name)
                except Exception:
                    pass

            dl_a, dl_b = st.columns(2)
            with dl_a:
                st.download_button(
                    label="Download .pose",
                    data=pose_bytes,
                    file_name="sign_language.pose",
                    mime="application/octet-stream",
                    use_container_width=True,
                )
            with dl_b:
                st.download_button(
                    label="Download GIF",
                    data=gif_bytes,
                    file_name="sign_language.gif",
                    mime="image/gif",
                    use_container_width=True,
                )

        except Exception as e:
            st.error(str(e))
            st.caption("Check spaCy (en) model and assets under `assets/dummy_lexicon_en/`.")
    else:
        st.caption("Translation preview will appear here.")
