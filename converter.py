from PIL import Image, ImageColor, ImageFilter
from math import sqrt
import os
import json


INPUT, OUTPUT = None, None


def load_settings():
    global INPUT, OUTPUT
    with open('Config.json', 'r') as config:
        data = json.load(config)
        INPUT = data["settings"]["input_dir"]
        OUTPUT = data["settings"]["output_dir"]
        colors = []
        for hex_color in data["palettes"][data["settings"]["palette"]]:
            color = ImageColor.getcolor(hex_color, "RGB")
            colors.append(color)
        return data["settings"], colors


def get_filenames():
    contents = os.listdir(path="Input")
    filenames = []
    for item in contents:
        if os.path.isfile(f'{INPUT}/{item}'):
            filenames.append(item)
    return filenames


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


def process_image(filename, colors, palette=None, blur=True, blur_radius=3, blur_offset=10, debug=True):
    print(f'Image {filename} processing started!')
    if blur:
        print(f'(palette: {palette}, blur: {blur}, blur_radius: {blur_radius}, blur_offset: {blur_offset}, '
              f'output: /{OUTPUT}, debug: {debug})')
    else:
        print(f'(palette: {palette}, blur: {blur}, output: /{OUTPUT}, debug: {debug})')

    img_file = Image.open(f'{INPUT}/{filename}')
    img = Image.new("RGB", img_file.size, (255, 255, 255))
    img.paste(img_file)  # 3 is the alpha channel
    pixels = img.load()

    result_img, res_pixels = match_colors(img, pixels, colors, filename=filename)
    if debug:
        result_img.save(f'{OUTPUT}/{filename}-color_match-(1).png')
    if blur:
        blur_map = create_blur_map(result_img, res_pixels, blur_radius=blur_radius,
                                   blur_offset=blur_offset, filename=filename)
        if debug:
            blur_map.save(f'{OUTPUT}/{filename}-blur_map-(2).png')
        result_img = apply_blur(result_img, blur_map, blur_radius=blur_radius)
        if debug:
            result_img.save(f'{OUTPUT}/{filename}-blurred_colors-(3).png')
    result_img = tweak_image_brightness(img, result_img, pixels, res_pixels, filename=filename)
    return result_img


def main():
    settings, colors = load_settings()
    filenames = get_filenames()
    for filename in filenames:
        img = process_image(
            filename,
            colors,
            palette=settings["palette"],
            blur=settings["blur"],
            blur_radius=settings["blur_radius"],
            blur_offset=settings["blur_offset"],
            debug=settings["debug"],
        )
        print(f'{filename} processing complete!')
        print(f'Image {settings["palette"]}-{filename} will be saved in /{OUTPUT}')
        img.save(f'{OUTPUT}/{settings["palette"]}-{filename}', format='PNG')


if __name__ == '__main__':
    main()
