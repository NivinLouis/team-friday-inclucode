import io
from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse, Response
from spoken_to_signed.bin import _text_to_gloss, _gloss_to_pose

app = FastAPI(title="Spoken Text to Signed Pose API")

@app.get("/spoken_text_to_signed_pose")
def spoken_text_to_signed_pose(
    text: str = Query(..., description="The English word or phrase to translate (e.g. 'hello')"),
    spoken: str = Query("en", description="The spoken language code (use 'en' for English)"),
    signed: str = Query("ins", description="The sign language code (use 'ins' for Indian Sign Language or 'ase' for American Sign Language)")
):
    try:
        # Validate query parameters
        if not text.strip():
            raise ValueError("Empty text")
        if spoken != "en":
            raise ValueError("Unsupported spoken language")
        if signed not in ("ins", "ase"):
            raise ValueError("Unsupported signed language")

        # 1. Translate spoken text to glosses
        sentences = _text_to_gloss(
            text=text,
            language=spoken,
            signed_language=signed
        )
        
        # 2. Build pose using local dummy lexicon
        lexicon_dir = "assets/dummy_lexicon_en"
        result = _gloss_to_pose(
            sentences=sentences,
            lexicon=lexicon_dir,
            spoken_language=spoken,
            signed_language=signed,
            disable_fingerspelling=False
        )
        
        # 3. Serialize pose to in-memory bytes
        pose_io = io.BytesIO()
        result.pose.write(pose_io)
        pose_bytes = pose_io.getvalue()
        
        return Response(content=pose_bytes, media_type="application/octet-stream")
    except Exception:
        # All errors/failures return 400 and the specified text
        return PlainTextResponse("The sign is unavailable.", status_code=400)
