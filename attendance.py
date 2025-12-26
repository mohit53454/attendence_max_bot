import cv2
import easyocr

# ---------------- CONFIG ----------------
TOTAL_STUDENTS = 45
# ---------------------------------------

reader = easyocr.Reader(['en'], gpu=False)

def load_image(path):
    img = cv2.imread(path)
    if img is None:
        raise RuntimeError(f"Cannot load image: {path}")
    return img

def extract_absent_rolls(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Red color mask (absent)
    red1 = cv2.inRange(hsv, (0, 70, 50), (10, 255, 255))
    red2 = cv2.inRange(hsv, (170, 70, 50), (180, 255, 255))
    red_mask = red1 | red2

    contours, _ = cv2.findContours(
        red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    absent_rolls = set()

    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w < 70 or h < 45:
            continue

        crop = image[y:y+h, x:x+w]

        # remove box borders
        ch, cw, _ = crop.shape
        crop = crop[int(0.2 * ch):int(0.8 * ch),
                    int(0.2 * cw):int(0.8 * cw)]

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

        result = reader.readtext(
            thresh,
            detail=1,
            allowlist="0123456789",
            paragraph=False
        )

        digits = [(bbox[0][0], txt) for bbox, txt, _ in result if txt.isdigit()]
        if not digits:
            continue

        digits.sort(key=lambda x: x[0])
        roll = int("".join(d[1] for d in digits))
        absent_rolls.add(roll)

    return absent_rolls

# ---------------- MAIN ----------------

# Load images
yesterday_img = load_image("yesterday.jpeg")
today_img = load_image("today.jpeg")

# Extract absent rolls
absent_yesterday = extract_absent_rolls(yesterday_img)
absent_today = extract_absent_rolls(today_img)

# Counts
absent_today_count = len(absent_today)
present_today_count = TOTAL_STUDENTS - absent_today_count

# 🔥 CORRECT COMPARISON (MATCHES MANUAL RESULT)
present_to_absent = sorted(absent_today - absent_yesterday)
absent_to_present = sorted(absent_yesterday - absent_today)

# -------- OUTPUT --------
print("====== ATTENDANCE REPORT ======\n")
print(f"Total Students   : {TOTAL_STUDENTS}")
print(f"Present Today    : {present_today_count}")
print(f"Absent Today     : {absent_today_count}\n")
print(f"Present → Absent : {present_to_absent}")
print(f"Absent → Present : {absent_to_present}")
print("\n==============================")
