from datetime import datetime
import barcode, subprocess, os
from barcode.writer import ImageWriter

from PIL import Image, ImageDraw, ImageFont

# Get the directory of the current script and parent
script_directory = os.path.dirname(os.path.abspath(__file__))
parent_directory = os.path.dirname(os.path.dirname(script_directory))

dpi = 360

def format_hardware_version(hardware_version):
    # Split the version number into major and minor parts
    major, _, minor = hardware_version.partition('.')

    # Add a zero to the minor part if it has only one digit
    minor = minor.ljust(2, '0')

    # Combine major and minor parts, remove the decimal point, and convert to an integer
    formatted_version = int(major + minor)

    return formatted_version

def generate_barcode(barcode_text):
    barcode_type = barcode.get_barcode_class('code128')  # Using Code 39 format
    bc = barcode_type(barcode_text, writer=ImageWriter())
    options = {"module_height": 10, "font_size": 10, "text_distance": 4, "quiet_zone": 0.9, "module_width": 0.2}

    label = bc.render(options)


    width, height = label.size

    left, top, right, bottom = 0, 10, width, height - 29
    label = label.crop((left, top, right, bottom))

    label.save(os.path.join(parent_directory, 'images', 'barcode_raw.png'))

    # Convert mm to pixels

    width_px = int((34 / 25.4) * dpi)
    height_px = int((12 / 25.4) * dpi)

    # Create blank image
    img = Image.new("RGB", (width_px, height_px), "white")

    # Assuming cropped_img is already defined and has size
    label_width, label_height = label.size

    # Calculate position to center
    x_offset = (width_px - label_width) // 2
    y_offset = (height_px - label_height) // 2

    # Paste cropped_img centered in img
    img.paste(label, (x_offset, y_offset))

    img.save(os.path.join(parent_directory, 'images', 'barcode.png'))


def generate_label(lines):

    width_mm, height_mm = 50, 12
    width_px = int((width_mm * dpi) / 25.4)
    height_px = int((height_mm * dpi) / 25.4)

    # Create a new white image
    img = Image.new('RGB', (width_px, height_px), 'white')
    draw = ImageDraw.Draw(img)

    # Load the image you want to add
    barcode = Image.open(os.path.join(parent_directory, 'images', 'barcode.png'))
    position = (0, 0)
    img.paste(barcode, position)

    # Define text and position
    number_of_lines = len(lines)
    size = height_px / (number_of_lines )

    font = ImageFont.truetype('DejaVuSansMono', int(size-10))
    font_size = size

    line_height = font_size  # Use font size as line height

    for i, line in enumerate(lines):
        x = 470
        y = i * line_height -2

        # Draw text
        draw.text((x, y), line, (0, 0, 0), font=font)  # Black text

        img.save(os.path.join(parent_directory, 'images', 'product_label.png'))

def main(barcode_text, make, model, variant, hardware_version, software_version, batch_id, print_flag):
    formated_hw = format_hardware_version(str(hardware_version))
    today_date = datetime.today().strftime('%Y/%m/%d')
    lines = [f"MN:{make}-{model}-{variant}", f"SW:{software_version}", f"BA:0{formated_hw}{batch_id}", today_date]

    generate_barcode(barcode_text)
    generate_label(lines)

    if(print_flag != '--no-print'):
        cmd = f"lpr -P PT-P900W -o PageSize=Custom.12x50mm -o Resolution=360dpi -o CutLabel=0 -o ExtraMargin=0mm -o number-up=1 -o orientation-requested=4 -#2 f{os.path.join(parent_directory, 'images', 'product_label.png')}"
        subprocess.check_output(cmd, shell=True, text=True)

if __name__ == '__main__':
    main()