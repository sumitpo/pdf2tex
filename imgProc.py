import fitz  # PyMuPDF
import os
from typing import List
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt


def extract_number(img_path: str) -> int:
    return int(img_path.split("_")[1])


def plot(img: np.ndarray, debug: bool = False):
    if debug:
        plt.imshow(img, cmap="gray")
        plt.axis("off")
        plt.show()


def skip_white(img: np.ndarray, idx: int, oper: str, thres: int) -> int:
    origal_idx = idx
    try:
        while sum(img[idx]) <= thres:
            # print(sum(img[idx]))
            if oper == "add":
                idx += 1
            else:
                idx -= 1
    except IndexError:
        plot(img, True)
        import pdb

        pdb.set_trace()
        return origal_idx
    return idx


def get_crop(img: np.ndarray) -> (int, int, int, int):
    top, bottom = 0, img.shape[0] - 1
    left, right = 0, img.shape[1] - 1

    sum1 = np.sum(img)
    print(sum1 / (bottom * right))
    if sum1 / (bottom * right) < 0.001:
        return left, top, right, bottom

    t_thres = 40
    b_thres = 800
    l_thres = 200
    r_thres = 200
    plot(img)
    # print("top")
    top = skip_white(img, top, "add", t_thres) - 30
    # print("bottom")
    bottom = skip_white(img, bottom, "minus", b_thres) + 10

    img = img[top:bottom]
    plot(img)
    img = np.transpose(img)

    # print("left")
    left = skip_white(img, left, "add", l_thres) - 20
    # print("right")
    right = skip_white(img, right, "minus", r_thres) + 20
    img = img[left:right]
    img = np.transpose(img)
    plot(img)
    return left, top, right, bottom


def cut_img(img_path: str, out_img_path: str = None) -> None:
    img = Image.open(img_path)

    gray = 255 - np.array(img.convert("L"))
    gray = (gray == 255).astype(int)

    """
    if img_path == "./tmp/page_71_img_1.png":
        plot(gray, True)
        import pdb

        pdb.set_trace()
    """
    crop_box = get_crop(gray)

    cropped_img = img.crop(crop_box)
    if out_img_path is None:
        out_img_path = img_path
    cropped_img.save(out_img_path)


def extract_images_from_pdf(pdf_path: str, output_folder: str) -> List[str]:
    """extract images from pdf and save to png

    Args:
        pdf_path (str): pdf file path
        output_folder (str): folder to save extracted images

    Returns:
        List[str]: extracted images paths
    """
    imgs = []

    # Open the PDF file
    pdf_document = fitz.open(pdf_path)

    # Create the output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Iterate through each page
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)

        # Get the images on the page
        image_list = page.get_images(full=True)

        # Iterate through the images on the page
        for image_index, img in enumerate(image_list):
            xref = img[0]  # The XREF of the image
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # Save the image
            image_filename = f"page_{page_number + 1}_img_{image_index + 1}.{image_ext}"
            image_path = os.path.join(output_folder, image_filename)
            imgs.append(image_path)
            with open(image_path, "wb") as image_file:
                image_file.write(image_bytes)
            cut_img(image_path)
            print(f"Saved {image_path}")

    # Close the PDF document
    pdf_document.close()

    return imgs


def load_imgs(pdf_path: str, output_folder: str) -> List[str]:
    """load extracted images path from output_folder if not empty,
    else extract images from pdf and save to output_folder

    Args:
        pdf_path (str): pdf file path
        output_folder (str): folder to save extracted images

    Returns:
        List[str]: extracted images paths
    """
    if not os.path.exists(output_folder):
        return extract_images_from_pdf(pdf_path, output_folder)
    png_files = []
    for root, dirs, files in os.walk(output_folder):
        for file in files:
            if file.endswith(".png"):
                png_files.append(os.path.join(root, file))
    return sorted(png_files, key=extract_number)


def test():
    cut_img("./sample.png", "./sample_cut.png")


def main():
    load_imgs("./hpMysql.pdf", "./tmp")


if __name__ == "__main__":
    test()
