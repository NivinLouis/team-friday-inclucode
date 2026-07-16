# English-to-ASL Gloss-Based Pipeline

An `English -> ASL gloss -> pose -> video` pipeline for spoken-to-signed translation.

- This fork is focused on English input and American Sign Language (`ase`) output.

- Paper available on [arxiv](https://arxiv.org/abs/2305.17714), presented
  at [AT4SSL 2023](https://sites.google.com/tilburguniversity.edu/at4ssl2023/).

![Visualization of our pipeline](assets/pipeline.jpg)

## Install

```bash
pip install -e .
```

## Usage

The project now exposes a single path: English text in, ASL gloss and pose out.
To demo it locally with the bundled dummy lexicon:

```bash
git clone https://github.com/ZurichNLP/spoken-to-signed-translation
cd spoken-to-signed-translation

pip install .

text_to_gloss_to_pose \
  --text "Children eat pizza." \
  --lexicon "assets/dummy_lexicon_en" \
  --pose "quick_test.pose"
```

#### Text-to-Gloss Translation

This script translates input text into gloss notation.

```bash
text_to_gloss \
  --text <input_text>
```

#### Text-to-Gloss-to-Pose Translation

This script translates input text into gloss notation, then converts the glosses into a pose file.

```bash
text_to_gloss_to_pose \
  --text <input_text> \
  --lexicon <path_to_directory> \
  --pose <output_pose_file_path>.pose
```

#### Text-to-Gloss-to-Pose-to-Video Translation

This script translates input text into gloss notation, converts the glosses into a pose file, and then transforms the pose file into a video.

> **Note:** Video generation requires the `pose-to-video` package with pix2pix and upscaler:
> ```bash
> pip install 'pose-to-video[pix2pix,simple_upscaler] @ git+https://github.com/sign-language-processing/pose-to-video'
> ```

```bash
text_to_gloss_to_pose_to_video \
  --text <input_text> \
  --lexicon <path_to_directory> \
  --video <output_video_file_path>.mp4
```

## Methodology

The pipeline consists of three main components:

1. **Text-to-Gloss Translation**

   Transforms English input text into an ASL-oriented gloss sequence using the
   rule-based pipeline in [spoken_to_signed/text_to_gloss/rules.py](spoken_to_signed/text_to_gloss/rules.py).

2. **Gloss-to-Pose Conversion**

  - [Lookup](spoken_to_signed/gloss_to_pose/lookup/lookup.py): Uses a lexicon of signed languages to convert the sequence of glosses into a
      sequence of poses.
  - [Pose Concatenation](spoken_to_signed/gloss_to_pose/concatenate.py): The poses are then cropped, concatenated, and smoothed,
      creating a pose representation for the input sentence.

3. **Pose-to-Video Generation**

    Transforms the processed pose video back into a synthesized video using an image translation model.

## Supported Language Pair

| Spoken Language | Sign Language | Codes |
|----------------|---------------|-------|
| English        | American Sign Language | `en -> ase` |

## Online Playgrounds

We have two available:

- [sign.mt](https://sign.mt) is a web interface of a translation system.
- [research.sign.mt](https://research.sign.mt) is an overview of sign language processing literature.

## Citation

If you find this work useful, please cite our paper:

```bib
@inproceedings{moryossef2023baseline,
  title={An Open-Source Gloss-Based Baseline for Spoken to Signed Language Translation},
  author={Moryossef, Amit and M{\"u}ller, Mathias and G{\"o}hring, Anne and Jiang, Zifan and Goldberg, Yoav and Ebling, Sarah},
  booktitle={2nd International Workshop on Automatic Translation for Signed and Spoken Languages (AT4SSL)},
  year={2023},
  month={June},
  url={https://github.com/ZurichNLP/spoken-to-signed-translation},
  note={Available at: \url{https://arxiv.org/abs/2305.17714}}
}
```
