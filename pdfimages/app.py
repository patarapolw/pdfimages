import PyPDF2
import os
import re
from PIL import Image
from pathlib import Path
from io import BytesIO
import subprocess
from tempfile import TemporaryDirectory
import shutil

from .util import remove_alpha, do_invert


class PdfImages:
    def __init__(self, pdf_filename):
        self.filename = pdf_filename
        self.f = open(pdf_filename, 'rb')
        self.reader = PyPDF2.PdfFileReader(self.f)

        self._toc = dict()
        self._title = list()
        self.toc = dict()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.f.close()

    def get_toc(self):
        toc2 = self._get_toc_page()

        used_img = set()
        for i in range(len(toc2)-1):
            images_dict = self.get_images(toc2[i][1], toc2[i+1][1])
            self.toc[toc2[i][0]] = [v for k, v in images_dict.items() if k not in used_img]
            used_img.update(self.get_images(toc2[i][1], toc2[i+1][1]).keys())

        return self.toc

    def _get_toc_page(self):
        for outline in self.reader.getOutlines():
            self._read_outlines(outline)

        return sorted(self._toc.items(), key=lambda x: x[1])

    def _read_outlines(self, outlines, recursion=0):
        if isinstance(outlines, list):
            for outline in outlines:
                self._read_outlines(outline, recursion=recursion + 1)
        else:
            title = str(outlines.title.strip()).strip()[:20]

            try:
                self._title[recursion] = title
            except IndexError:
                self._title.append(title)

            self._toc[tuple(self._title[:recursion+1])] = self.reader.getDestinationPageNumber(outlines)

        self._toc[('numPages',)] = self.reader.getNumPages()

    def get_images(self, start, end):
        images = dict()
        for j in range(start, end+1):
            page = self.reader.getPage(j)

            try:
                xObject = page['/Resources']['/XObject'].getObject()
                for obj in xObject:
                    if xObject[obj]['/Subtype'] == '/Image':
                        images[obj] = f'{j}-{obj[1:]}'
            except KeyError:
                pass

        return images

    def extract_images_pypdf2(self, output_folder=None, invert=False, no_alpha=False):
        """
        From https://stackoverflow.com/a/34116472/9023855
        Requires https://github.com/mstamy2/PyPDF2.git
        Note that `pip install PyPDF2` doesn't work
        :param output_folder:
        :param invert:
        :param no_alpha:
        :return:
        """
        if output_folder is None:
            output_folder = os.path.splitext(self.filename)[0]

        page_number = None
        page = None
        for dir_names, images in self.get_toc().items():
            print(dir_names)

            for image in images:
                match_obj = re.fullmatch(r'(\d+)-(\S+\d+)', image)
                if match_obj is None:
                    print(image)
                else:
                    page_str, obj_str = match_obj.groups()

                    if page_number != page_str:
                        page = self.reader.getPage(int(page_str))
                        page_number = page_str

                    xObject = page['/Resources']['/XObject'].getObject()
                    obj = '/' + obj_str
                    file_root = os.path.join(output_folder, *dir_names)
                    file_stem = os.path.join(file_root, image)

                    Path(file_root).mkdir(parents=True, exist_ok=True)

                    try:
                        size = (xObject[obj]['/Width'], xObject[obj]['/Height'])
                        data = xObject[obj].getData()
                        if xObject[obj]['/ColorSpace'] == '/DeviceRGB':
                            mode = "RGB"
                        else:
                            mode = "P"

                        if no_alpha:
                            if xObject[obj]['/Filter'] == '/FlateDecode':
                                img = Image.frombytes(mode, size, data)
                            else:
                                img = Image.open(BytesIO(data))

                            img = remove_alpha(img)
                            if invert:
                                img = do_invert(img)
                            img.save(file_stem + ".jpg")
                        else:
                            if xObject[obj]['/Filter'] == '/FlateDecode':
                                img = Image.frombytes(mode, size, data)
                                img.save(file_stem + ".png")
                            elif xObject[obj]['/Filter'] == '/DCTDecode':
                                img = open(file_stem + ".jpg", "wb")
                                img.write(data)
                                img.close()
                            elif xObject[obj]['/Filter'] == '/JPXDecode':
                                img = open(file_stem + ".jp2", "wb")
                                img.write(data)
                                img.close()

                    except AssertionError:
                        pass

    def extract_images_poppler(self, output_folder=None, output_format=None, min_file_size=50000):
        if output_folder is None:
            output_folder = os.path.splitext(self.filename)[0]

        toc2 = self._get_toc_page()
        with TemporaryDirectory() as tempdir:
            command = [
                'pdfimages',
                '-p',
                self.filename,
                os.path.join(tempdir, 'img')
            ]

            if output_format:
                command[2:2] = '-' + output_format

            subprocess.call(command)

            for i in range(len(toc2)-1):
                dir_names = toc2[i][0]
                print(dir_names)

                for filename in os.listdir(tempdir):
                    src = os.path.join(tempdir, filename)
                    if os.path.getsize(src) < min_file_size:
                        os.unlink(src)
                        continue

                    page_number = re.search(r'(\d+)-\d+', filename).group(1)
                    if int(page_number) in range(toc2[i][1], toc2[i+1][1]):
                        file_root = os.path.join(output_folder, *dir_names)
                        Path(file_root).mkdir(parents=True, exist_ok=True)

                        shutil.move(src=src,
                                    dst=os.path.join(file_root, filename))
