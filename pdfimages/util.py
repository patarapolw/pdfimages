import PIL.ImageOps


def remove_alpha(img):
    return img.convert('RGB')


def do_invert(img):
    return PIL.ImageOps.invert(img)
