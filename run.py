import os

from pdfimages.app import PdfImages


if __name__ == '__main__':
    with PdfImages(os.path.join('/Users/patarapolw/Desktop',
                                "Differential Diagnosis in Surgical Pathology, 3rd Edition.pdf")) as pdf:
        pdf.extract_images_poppler()
