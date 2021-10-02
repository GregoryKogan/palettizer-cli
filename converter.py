from PIL import Image, ImageColor, ImageFilter
from math import sqrt
import os
import json
from tqdm import trange


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


def get_color(src_color, colors, quadratic_color_distance=False):
    alpha = src_color[3]
    src_color = src_color[:3]
    sr, sg, sb = src_color
    colors_diffs = []
    for dst_color in colors:
        dr, dg, db = dst_color
        if quadratic_color_distance:
            dist = sqrt(abs(sr - dr) ** 2 + abs(sg - dg) ** 2 + abs(sb - db) ** 2)
        else:
            dist = abs(sr - dr) + abs(sg - dg) + abs(sb - db)
        colors_diffs.append((dist, dst_color))
    fit_color = list(min(colors_diffs)[1])
    fit_color.append(alpha)
    return tuple(fit_color)


def get_brightness(color):
    alpha = 1
    if len(color) > 3:
        alpha = color[3] / 255
    color = color[:3]
    r, g, b = color
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) * alpha


def tweak_pixel_brightness(src_color, fit_color, brightness_steps=False):
    src_luminance = get_brightness((src_color))
    res_luminance = get_brightness((fit_color))
    res_luminance = max(0.0001, res_luminance)
    factor = src_luminance / res_luminance
    if brightness_steps:
        factor = round(factor, 1)

    alpha = None
    if len(fit_color) > 3:
        alpha = fit_color[3]
        fit_color = fit_color[:3]
    rr, rg, rb = fit_color

    rr = round(rr * factor)
    rg = round(rg * factor)
    rb = round(rb * factor)
    rr = min(255, (max(0, rr)))
    rg = min(255, (max(0, rg)))
    rb = min(255, (max(0, rb)))
    if alpha is not None:
        return rr, rg, rb, alpha
    return rr, rg, rb


def tweak_image_brightness(img, result_img, pixels, filename='current image', brightness_steps=False):
    res_pixels = result_img.load()
    for i in trange(img.size[0], desc=f'Brightness tweaking for {filename}', colour='green'):
        for j in range(img.size[1]):
            src_color = pixels[i, j]
            fit_color = res_pixels[i, j]
            res_pixels[i, j] = tweak_pixel_brightness(src_color, fit_color, brightness_steps=brightness_steps)
    return result_img


def match_colors(img, pixels, colors, filename='current image', quadratic_color_distance=False):
    result_img = Image.new('RGBA', img.size)
    res_pixels = result_img.load()
    for i in trange(img.size[0], desc=f'Color matching for {filename}', colour='green'):
        for j in range(img.size[1]):
            src_color = pixels[i, j]
            res_pixels[i, j] = get_color(src_color, colors, quadratic_color_distance=quadratic_color_distance)
    return result_img


def process_image(filename,
                  colors,
                  palette=None,
                  brightness_tweak=True,
                  quadratic_color_distance=False,
                  blur=True,
                  blur_radius=3,
                  brightness_steps=False,
                  debug=True):
    print('=' * 20)
    print(f'Image {filename} processing started!')
    print(f'palette: {palette}')
    print(f'brightness tweak: {brightness_tweak}')
    print(f'quadratic color distance: {quadratic_color_distance}')
    print(f'blur: {blur}')
    if blur:
        print(f'blur radius: {blur_radius}')
    print(f'brightness steps: {brightness_steps}')
    print(f'input: /{INPUT}')
    print(f'output: /{OUTPUT}')
    print(f'debug: {debug}')
    print('=' * 20)

    img_file = Image.open(f'{INPUT}/{filename}')
    img = Image.new("RGBA", img_file.size, (255, 255, 255, 0))
    img.paste(img_file)
    pixels = img.load()

    result_img = match_colors(img, pixels, colors, filename=filename,
                                          quadratic_color_distance=quadratic_color_distance)
    if debug:
        result_img.save(f'{OUTPUT}/{filename}-color_match-(1).png')
    if blur:
        result_img = result_img.filter(ImageFilter.GaussianBlur(blur_radius))
        if debug:
            result_img.save(f'{OUTPUT}/{filename}-blurred_colors-(2).png')


    if brightness_tweak:
        result_img = tweak_image_brightness(img, result_img, pixels,
                                            filename=filename, brightness_steps=brightness_steps)
    return result_img


def main():
    settings, colors = load_settings()
    filenames = get_filenames()
    for filename in filenames:
        img = process_image(
            filename,
            colors,
            palette=settings["palette"],
            brightness_tweak=settings["brightness_tweak"],
            quadratic_color_distance=settings["quadratic_color_distance"],
            blur=settings["blur"],
            blur_radius=settings["blur_radius"],
            brightness_steps=settings["brightness_steps"],
            debug=settings["debug"],
        )
        print(f'{filename} processing complete!')
        print(f'Image {settings["palette"]}-{filename} will be saved in /{OUTPUT}')
        img.save(f'{OUTPUT}/{settings["palette"]}-{filename}', format='PNG')


if __name__ == '__main__':
    main()
