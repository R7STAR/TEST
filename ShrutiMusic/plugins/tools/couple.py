from datetime import datetime, timedelta
import pytz
import os
import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.enums import ChatType
from telegraph import upload_file
from PIL import Image, ImageDraw, ImageFont
import requests

from PritiMusic.utils import get_image, get_couple, save_couple
from PritiMusic import app


# ---------------- TIME ----------------

def get_today_date():
    tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).strftime("%d/%m/%Y")


def get_tomorrow_date():
    tz = pytz.timezone("Asia/Kolkata")
    return (datetime.now(tz) + timedelta(days=1)).strftime("%d/%m/%Y")


today = get_today_date()
tomorrow = get_tomorrow_date()


# ---------------- DOWNLOAD IMAGE ----------------

def download_image(url, path):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            open(path, "wb").write(r.content)
    except:
        pass
    return path


# ---------------- SAFE PROFILE PHOTO ----------------

async def safe_pfp(user_id, path):
    try:
        chat = await app.get_chat(user_id)
        if chat.photo:
            return await app.download_media(chat.photo.big_file_id, file_name=path)
    except:
        pass

    # default pfp
    return download_image(
        "https://telegra.ph/file/05aa686cf52fc666184bf.jpg",
        path
    )


# ---------------- GENDER DETECTOR ----------------

def detect_gender(user):
    text = f"{(user.first_name or '').lower()} {(user.username or '').lower()} {(user.bio or '').lower()}"

    boy_kw = ["boy", "male", "king", "bro", "mr", "bhai", "gamer", "ladka"]
    girl_kw = ["girl", "female", "queen", "miss", "mrs", "sis", "ladki", "cute"]

    if any(k in text for k in boy_kw):
        return "boy"
    if any(k in text for k in girl_kw):
        return "girl"

    return random.choice(["boy", "girl"])  # fallback


# ---------------- MAKE CIRCLE WITHOUT NAME ----------------

def circle_only(base, profile_img, pos_x, pos_y):
    size = 350

    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((0, 0, size, size), fill=255)

    profile_img = profile_img.resize((size, size))

    circle_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    circle_img.paste(profile_img, (0, 0), mask)

    base.paste(circle_img, (pos_x, pos_y), circle_img)


# ---------------- TITLE TEXT ----------------

def draw_title(img):
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("PritiMusic/assets/GreatVibes-Regular.ttf", 120)
    title = "Couple of the Day"

    w, h = draw.textsize(title, font=font)
    x = 1400 // 2 - w // 2
    y = 40

    draw.text((x, y), title, font=font, fill=(220, 120, 70))


# ---------------- COUPLE COMMAND ----------------

@app.on_message(filters.command(["couple", "couples"]))
async def couple_cmd(_, message):

    if message.chat.type == ChatType.PRIVATE:
        return await message.reply_text("This command works only in groups!")

    cid = message.chat.id

    p1_path = "downloads/p1.png"
    p2_path = "downloads/p2.png"
    output_path = f"downloads/couple_{cid}.png"

    try:
        selected = await get_couple(cid, today)

        # ---------- NEW COUPLE ----------
        if not selected:
            msg = await message.reply_text("❣️")

            boys = []
            girls = []

            async for m in app.get_chat_members(cid, limit=100):
                u = m.user
                if u.is_bot or u.is_deleted:
                    continue

                gender = detect_gender(u)
                if gender == "boy":
                    boys.append(u.id)
                else:
                    girls.append(u.id)

            if not boys or not girls:
                return await message.reply_text("❗ इस ग्रुप में boy या girl की कमी है।")

            c1 = random.choice(boys)
            c2 = random.choice(girls)

            u1 = await app.get_users(c1)
            u2 = await app.get_users(c2)

            N1 = u1.mention
            N2 = u2.mention

            # profile pics
            p1 = await safe_pfp(c1, p1_path)
            p2 = await safe_pfp(c2, p2_path)

            img1 = Image.open(p1).convert("RGBA")
            img2 = Image.open(p2).convert("RGBA")

            # background
            bg = Image.new("RGBA", (1400, 900), (245, 245, 245, 255))

            draw_title(bg)

            # paste circles
            circle_only(bg, img1, 200, 250)
            circle_only(bg, img2, 850, 250)

            bg.save(output_path)

            TXT = f"""
<b>Today's Couple of the Day 🎉:

{N1} + {N2} ❤️

Next Couple will be selected on {tomorrow}!</b>
"""

            await message.reply_photo(
                output_path,
                caption=TXT,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Add me 🌋", url=f"https://t.me/{app.username}?startgroup=true")]]
                ),
            )

            saved = upload_file(output_path)
            img_link = "https://graph.org/" + saved[0]

            couple = {"c1_id": c1, "c2_id": c2}
            await save_couple(cid, today, couple, img_link)

            await msg.delete()

        # ---------- OLD COUPLE ----------
        else:
            msg = await message.reply_text("❣️")

            c1 = int(selected["c1_id"])
            c2 = int(selected["c2_id"])

            u1 = await app.get_users(c1)
            u2 = await app.get_users(c2)

            N1 = u1.mention
            N2 = u2.mention

            b = await get_image(cid)

            TXT = f"""
<b>Today's Couple of the Day 🎉:

{N1} + {N2} ❤️

Next Couple will be selected on {tomorrow}!</b>
"""

            await message.reply_photo(
                b,
                caption=TXT,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Add me 🌋", url=f"https://t.me/{app.username}?startgroup=true")]]
                ),
            )

            await msg.delete()

    except Exception as e:
        print("Error:", e)

    finally:
        try:
            os.remove(p1_path)
            os.remove(p2_path)
            os.remove(output_path)
        except:
            pass