from PIL import Image, ImageColor, ImageFilter
from math import sqrt
import os


INPUT = 'Input'
OUTPUT = 'Output'


def get_filenames():
    contents = os.listdir(path="Input")
    filenames = []
    for item in contents:
        if os.path.isfile(f'{INPUT}/{item}'):
            filenames.append(item)
    return filenames


def load_palette():
    with open('Palette.txt', 'r') as palette_file:
        lines = palette_file.readlines()
        colors = []
        for line in lines:
            hex_color = line[:7]
            color = ImageColor.getcolor(hex_color, "RGB")
            colors.append(color)
        return colors


def get_color(src_color, colors):
    src_color = src_color[:3]
    sr, sg, sb = src_color
    colors_diffs = []
    for dst_color in colors:
        dr, dg, db = dst_color
        dist = sqrt(abs(sr - dr) ** 2 + abs(sg - dg) ** 2 + abs(sb - db) ** 2)
        colors_diffs.append((dist, dst_color))
    fit_color = min(colors_diffs)[1]
    return fit_color


def get_brightness(color):
    r, g, b = color
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def tweak_pixel_brightness(src_color, fit_color):
    src_color = src_color[:3]
    sr, sg, sb = src_color
    rr, rg, rb = fit_color
    src_luminance = get_brightness((sr, sg, sb))
    res_luminance = get_brightness((rr, rg, rb))
    max_factor = 255 / max(rr, rg, rb)
    factor = min(src_luminance / res_luminance, max_factor)
    rr = round(rr * factor)
    rg = round(rg * factor)
    rb = round(rb * factor)
    rr = min(255, (max(0, rr)))
    rg = min(255, (max(0, rg)))
    rb = min(255, (max(0, rb)))
    return rr, rg, rb


def tweak_image_brightness(img, result_img, pixels, res_pixels, filename='current image'):
    last_msg_val = 0
    for i in range(img.size[0]):
        progress_val = round((i + 1) / img.size[0] * 100)
        if progress_val != last_msg_val and progress_val % 5 == 0:
            last_msg_val = progress_val
            print(f'Brightness tweaking for {filename} is {progress_val}% done')
        for j in range(img.size[1]):
            src_color = pixels[i, j]
            fit_color = res_pixels[i, j]
            res_pixels[i, j] = tweak_pixel_brightness(src_color, fit_color)
    return result_img


def create_blur_map(img, pixels, blur_radius, blur_offset, filename='current image'):
    blur_map = Image.new('L', img.size, 0)
    blur_pixels = blur_map.load()

    conv_filter = [
        [-1, -1, -1],
        [-1, 8, -1],
        [-1, -1, -1],
    ]

    last_msg_val = 0
    for i in range(blur_radius, img.size[0] - blur_radius):
        progress_val = round((i + 1) / img.size[0] * 100)
        if progress_val != last_msg_val and progress_val % 5 == 0:
            last_msg_val = progress_val
            print(f'Blur map for {filename} is {progress_val}% done')
        for j in range(blur_radius, img.size[1] - blur_radius):
            blur_val = 0
            blur_val += get_brightness(pixels[i - 1, j - 1]) * conv_filter[0][0]
            blur_val += get_brightness(pixels[i - 1, j]) * conv_filter[0][1]
            blur_val += get_brightness(pixels[i - 1, j + 1]) * conv_filter[0][2]
            blur_val += get_brightness(pixels[i, j - 1]) * conv_filter[1][0]
            blur_val += get_brightness(pixels[i, j]) * conv_filter[1][1]
            blur_val += get_brightness(pixels[i, j + 1]) * conv_filter[1][2]
            blur_val += get_brightness(pixels[i + 1, j - 1]) * conv_filter[2][0]
            blur_val += get_brightness(pixels[i + 1, j]) * conv_filter[2][1]
            blur_val += get_brightness(pixels[i + 1, j + 1]) * conv_filter[2][2]

            if blur_val > blur_offset:
                for oi in range(-blur_radius, blur_radius + 1):
                    for oj in range(-blur_radius, blur_radius + 1):
                        blur_pixels[i + oi, j + oj] = 255
    return blur_map


def apply_blur(img, blur_map, blur_radius):
    blur = img.filter(ImageFilter.GaussianBlur(blur_radius))
    img.paste(blur, mask=blur_map)
    return img


def match_colors(img, pixels, colors, filename='current image'):
    result_img = Image.new('RGB', img.size)
    res_pixels = result_img.load()
    last_msg_val = 0
    for i in range(img.size[0]):
        progress_val = round((i + 1) / img.size[0] * 100)
        if progress_val != last_msg_val and progress_val % 5 == 0:
            last_msg_val = progress_val
            print(f'Color matching for {filename} is {progress_val}% done')
        for j in range(img.size[1]):
            src_color = pixels[i, j]
            res_pixels[i, j] = get_color(src_color, colors)
    return result_img, res_pixels


def process_image(filename, colors, blur=False, blur_radius=3, blur_offset=10):
    img_file = Image.open(f'{INPUT}/{filename}')
    img = Image.new("RGB", img_file.size, (255, 255, 255))
    img.paste(img_file)  # 3 is the alpha channel
    pixels = img.load()

    result_img, res_pixels = match_colors(img, pixels, colors, filename=filename)
    # result_img.save(f'{OUTPUT}/1.png')
    if blur:
        blur_map = create_blur_map(result_img, res_pixels, blur_radius=blur_radius,
                                   blur_offset=blur_offset, filename=filename)
        # blur_map.save(f'{OUTPUT}/2.png')
        result_img = apply_blur(result_img, blur_map, blur_radius=blur_radius)
        # result_img.save(f'{OUTPUT}/3.png')
    result_img = tweak_image_brightness(img, result_img, pixels, res_pixels, filename=filename)
    return result_img


def main():
    filenames = get_filenames()
    colors = load_palette()
    for filename in filenames:
        img = process_image(filename, colors)
        print(f'{filename} processing complete!')
        img.save(f'{OUTPUT}/{filename}')


if __name__ == '__main__':
    main()
