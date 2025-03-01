import argparse
from ocrmac import ocrmac
from typing import List

from imgProc import load_imgs
import os
import json
import re
from tqdm import tqdm


def ocr2text(img_path: str):
    """recongize text from image

    Args:
        img_path (str): image path

    Returns:
        _type_: _description_
    """
    annotations = ocrmac.OCR(
        img_path, language_preference=["zh-Hans", "en-US"]
    ).recognize()
    return annotations


def split2chap(annotations):
    chapTitles = ["前言"]
    for i in range(1, 17):
        chapTitles.append("第{}章".format(i))

    chaps = []
    lines = []

    chapter_num = 0
    for ann in tqdm(annotations):
        if ann[0] in chapTitles:
            chapter_num += 1
            chaps.append(lines)
            print("get new chapter")
            lines = []
        lines.append(ann)
    """
    import pdb

    pdb.set_trace()
    """
    return chaps


def parse():

    des = "Extract text from a PDF file and save it to a text file."
    try:
        from rich_argparse import RichHelpFormatter

        parser = argparse.ArgumentParser(
            description=des, formatter_class=RichHelpFormatter
        )
    except ImportError:
        parser = argparse.ArgumentParser(description=des)

    # Add arguments with long and short options
    parser.add_argument(
        "-i", "--input", required=True, help="Path to the input PDF file"
    )
    parser.add_argument(
        "-o", "--output", required=False, help="Path to the output text file"
    )

    # Parse the arguments
    args = parser.parse_args()
    return args


def chap2tex(chap, chap_dir: str) -> str:
    tex = ""
    tex += "\\chapter{%s}\n" % (chap[1][0])
    if not re.search(r"第\d+章", chap[0][0]):
        return ""
    chapter_number = int(chap[0][0][1:-1])
    chapter_title = chap[1]
    for line in chap[2:]:
        text_width = line[2][2]
        text_height = line[2][3]
        print("w: {}, h: {}, line: {}".format(text_width, text_height, line[0]))
        if line[0].startswith(str(chapter_number)):
            matches = re.match(
                rf"({chapter_number}(\.\d+)+)\s*(.+)", line[0], re.M | re.I
            )
            if matches:
                print(
                    "sec number: {}, sec title: {}".format(
                        matches.group(1), matches.group(3)
                    )
                )
                dot_num = len(matches.group(1).split("."))
                if 2 == dot_num:
                    tex += "\\section{%s}" % (matches.group(3))
                elif 3 == dot_num:
                    tex += "\\subsection{%s}" % (matches.group(3))
                else:
                    tex += "\\subsubsection{}" % (matches.group(3))
            else:
                tex += "{}\n".format(line[0])
        else:
            tex += "{}\n".format(line[0])
        if text_width < 0.98:
            tex += "\n"
    tex = tex.replace("_", "\\_")

    with open(os.path.join(chap_dir, "{}.tex".format(chapter_number)), "w") as fp:
        print(tex, file=fp)
    return tex


def main():
    args = parse()
    anno_json = "./anno.json"
    if not os.path.exists(anno_json):
        imgs = load_imgs(args.input, "./tmp")
        annotations = []
        for img in imgs:
            annotations.extend(ocr2text(img))
        with open(anno_json, "w", encoding="utf-8") as fp:
            json.dump(annotations, fp, indent=2)
    else:
        with open(anno_json, "r", encoding="utf-8") as fp:
            annotations = json.load(fp)

    chaps = split2chap(annotations)
    chap_dir = "./chapters"
    if not os.path.exists(chap_dir):
        os.mkdir(chap_dir)
    for chap in chaps:
        chap2tex(chap, chap_dir)


if __name__ == "__main__":
    main()
