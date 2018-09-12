import os
# from PIL import Image

from pdfimages.app import PdfImages
# from pdfimages.util import do_invert, remove_alpha


if __name__ == '__main__':
    with PdfImages(os.path.join('/Users/patarapolw/Desktop',
                                'Robbins and Cotran Pathologic Basis of Disease 9e - Kumar, Abbas, Aster (Elsevier 2015).pdf')) as pdf:
        pdf.extract_images_poppler()

    # img = Image.open(os.path.join('/Users/patarapolw/Desktop/Differential Diagnosis in Surgical Pathology, 3rd Edition/Chapter 9/b\'Adrenal Gland\'/Differential Diagnos', '447-Im728.jpg'))
    # img = do_invert(remove_alpha(img))
    # img.save('test.jpg')
