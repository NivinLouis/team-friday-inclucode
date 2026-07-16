import argparse
import os
import tempfile

from pose_format import Pose

from spoken_to_signed.gloss_to_pose import (
    CSVPoseLookup,
    PoseResult,
    concatenate_poses,
    gloss_to_pose,
)
from spoken_to_signed.gloss_to_pose.lookup.fingerspelling_lookup import (
    FingerspellingPoseLookup,
)
from spoken_to_signed.text_to_gloss import rules
from spoken_to_signed.text_to_gloss.types import Gloss


def _text_to_gloss(text: str, language: str = "en", **kwargs) -> list[Gloss]:
    return rules.text_to_gloss(text=text, language=language, **kwargs)


def _gloss_to_pose(
    sentences: list[Gloss],
    lexicon: str,
    spoken_language: str,
    signed_language: str,
    disable_fingerspelling: bool = False,
) -> PoseResult:
    backup = None if disable_fingerspelling else FingerspellingPoseLookup()
    pose_lookup = CSVPoseLookup(lexicon, backup=backup)
    results = [gloss_to_pose(gloss, pose_lookup, spoken_language, signed_language) for gloss in sentences]
    if len(results) == 1:
        return results[0]
    return PoseResult(pose=concatenate_poses([r.pose for r in results], trim=False))


def _get_models_dir():
    home_dir = os.path.expanduser("~")
    sign_dir = os.path.join(home_dir, ".sign")
    os.makedirs(sign_dir, exist_ok=True)
    models_dir = os.path.join(sign_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    return models_dir


def _pose_to_video(pose: Pose, video_path: str):
    models_dir = _get_models_dir()
    pix2pix_path = os.path.join(models_dir, "pix2pix.h5")
    if not os.path.exists(pix2pix_path):
        print("Downloading pix2pix model...")
        import urllib.request

        urllib.request.urlretrieve(
            "https://firebasestorage.googleapis.com/v0/b/sign-mt-assets/o/models%2Fgenerator%2Fmodel.h5?alt=media",
            pix2pix_path,
        )

    import shutil
    import subprocess

    if shutil.which("pose_to_video") is None:
        raise RuntimeError(
            "The command 'pose_to_video' does not exist. Please install the `pose-to-video` package using "
            "`pip install 'pose-to-video[pix2pix,simple_upscaler] @ git+https://github.com/sign-language-processing/pose-to-video'`"
        )

    pose_path = tempfile.mktemp(suffix=".pose")
    with open(pose_path, "wb") as f:
        pose.write(f)

    args = [
        "pose_to_video",
        "--type=pix2pix",
        "--model",
        pix2pix_path,
        "--pose",
        pose_path,
        "--video",
        video_path,
        "--processors",
        "simple_upscaler",
    ]
    print(" ".join(args))
    subprocess.run(args, check=True)


def _lexicon_input_arguments(parser: argparse.ArgumentParser):
    parser.add_argument("--lexicon", type=str, required=True)
    parser.add_argument("--disable-fingerspelling", action="store_true", help="Disable fingerspelling fallback")


def _text_input_arguments(parser: argparse.ArgumentParser):
    parser.add_argument("--text", type=str, required=True)


def text_to_gloss():
    args_parser = argparse.ArgumentParser()
    _text_input_arguments(args_parser)
    args = args_parser.parse_args()

    print("Text to gloss")
    print("Input text:", args.text)
    sentences = _text_to_gloss(args.text)
    print("Output gloss:", sentences)


def pose_to_video():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument("--pose", type=str, required=True)
    args_parser.add_argument("--video", type=str, required=True)
    args = args_parser.parse_args()

    with open(args.pose, "rb") as f:
        pose = Pose.read(f.read())

    _pose_to_video(pose, args.video)

    print("Pose to video")
    print("Input pose:", args.pose)
    print("Output video:", args.video)


def text_to_gloss_to_pose():
    args_parser = argparse.ArgumentParser()
    _text_input_arguments(args_parser)
    _lexicon_input_arguments(args_parser)
    args_parser.add_argument("--pose", type=str, required=True)
    args = args_parser.parse_args()

    sentences = _text_to_gloss(args.text)
    result = _gloss_to_pose(
        sentences, args.lexicon, "en", "ase", args.disable_fingerspelling
    )

    with open(args.pose, "wb") as f:
        result.pose.write(f)

    print("Text to gloss to pose")
    print("Input text:", args.text)
    print("Output pose:", args.pose)


def text_to_gloss_to_pose_to_video():
    args_parser = argparse.ArgumentParser()
    _text_input_arguments(args_parser)
    _lexicon_input_arguments(args_parser)
    args_parser.add_argument("--video", type=str, required=True)
    args = args_parser.parse_args()

    sentences = _text_to_gloss(args.text)
    result = _gloss_to_pose(
        sentences, args.lexicon, "en", "ase", args.disable_fingerspelling
    )
    _pose_to_video(result.pose, args.video)

    print("Text to gloss to pose to video")
    print("Input text:", args.text)
    print("Output video:", args.video)


if __name__ == "__main__":
    text_to_gloss_to_pose()
