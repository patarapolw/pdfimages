import os

from pdfimages.app import PdfImages


if __name__ == '__main__':
    with PdfImages(os.path.join('/Users/patarapolw/Desktop',
                                "Rosai and Ackerman's Surgical Pathology 10th.pdf")) as pdf:
        pdf.extract_images_poppler()
