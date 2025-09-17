from PIL import Image, ImageDraw, ImageFont


def generate_end_of_day_image(summary: dict, output_path="summary.png"):

    width, height = 600, 400
    img = Image.new("RGB", (width, height), (30, 30, 60))
    draw = ImageDraw.Draw(img)

    title_font = ImageFont.load_default()
    text_font = ImageFont.load_default()

    draw.text(
        (20, 20),
        f"[Day summary] {summary['date']}",
        font=title_font,
        fill=(255, 255, 0),
    )

    y = 70
    draw.text(
        (20, y),
        f"[All habits]]: {summary['total_habits']}",
        font=text_font,
        fill=(255, 255, 255),
    )
    y += 25
    draw.text(
        (20, y), f"[Done]: {summary['completed']}", font=text_font, fill=(100, 255, 100)
    )
    y += 25
    draw.text(
        (20, y),
        f"[Not done]: {summary['not_completed']}",
        font=text_font,
        fill=(255, 100, 100),
    )
    y += 25
    draw.text(
        (20, y),
        f"[Progress]: {summary['percent']}%",
        font=text_font,
        fill=(200, 200, 255),
    )
    y += 40

    draw.text((20, y), "Done]:", font=text_font, fill=(150, 255, 150))
    y += 20
    for habit in summary["done_habits"]:
        draw.text((40, y), f"- {habit}", font=text_font, fill=(200, 255, 200))
        y += 20

    draw.text((20, y), "[Left]:", font=text_font, fill=(255, 180, 180))
    y += 20
    for habit in summary["habits"]:
        if habit not in summary["done_habits"]:
            draw.text((40, y), f"- {habit}", font=text_font, fill=(255, 150, 150))
            y += 20

    img.save(output_path)
    return output_path
