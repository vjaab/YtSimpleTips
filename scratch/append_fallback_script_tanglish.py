# -*- coding: utf-8 -*-
import json
import os

fallback_path = "/Users/vijayakumarjermansraj/Desktop/google_antigravity/yt_simple_tips/fallback_scripts.json"

new_script = {
    "title": "உங்க GPay பணத்தை திருட முடியாது! AI Security Hack! 🛡️",
    "description": "Ungalukke theriyaama, unga GPay matrum PhonePe panathai 24 mani neramum oru 'Invisible Guard' paadhugaathuttu irukkunnu theriyuma? How AI is protecting your UPI money explained in Tanglish by VJ. #AITamil #GPayTamil #SimpleTipsByVJ",
    "use_case_evidence_url": "https://github.com/vjaab/YtSimpleTips",
    "script": "Ungalukke theriyaama, unga GPay matrum PhonePe panathai 24 mani neramum oru 'Invisible Guard' paadhugaathuttu irukkunnu theriyuma? Adhuthaan Artificial Intelligence (AI). Neenga dhinamum panra transactions vachu intha AI unga spending habits-a padichutte irukkum. Udhaaranathukku, dhinamum tea kadaila 20 roobai anuppura neenga, dhideernu night 2 manikki yaaro oru unknown person-ukku 50000 roobai anuppa try pannaa, AI udane alert aagi andha transaction-a block pannidum! Unga bank manager-a vida intha AI-ku ungala nalla theriyum! Intha information pudhusa irundha like pannittu, 'Simple Tips by VJ' channel-a subscribe pannunga!",
    "relevant_links": [
        "https://github.com/vjaab/YtSimpleTips"
    ],
    "phonetic_pronunciation_map": {
        "GPay": "jee-pay",
        "PhonePe": "phone-pay",
        "Invisible": "in-vis-i-bl",
        "Guard": "gard",
        "Artificial": "ar-ti-fi-shal",
        "Intelligence": "in-tel-i-gens",
        "AI": "ay-eye",
        "transactions": "tran-sac-shuns",
        "spending": "spen-ding",
        "habits": "ha-bits",
        "alert": "a-lert",
        "block": "blok"
    },
    "hook": "உங்க GPay பணத்தை திருட முடியாது! Why? 🛡️",
    "summary": "How AI protects GPay and PhonePe 24/7 with invisible security and habit learning.",
    "sub_category": "ai_safety_and_scams",
    "breaking_news_level": 9,
    "keywords": [
        "GPay AI",
        "PhonePe Security",
        "UPI Fraud AI",
        "Simple Tips by VJ",
        "Tamil Tech Tips"
    ],
    "hashtags": [
        "#AITamil",
        "#TechTamil",
        "#GPay",
        "#PhonePe",
        "#SimpleTipsByVJ"
    ],
    "comment_bait_question": "Unga GPay/PhonePe-la ennikkaavadhu unknown transaction block aagi irukka? Comment-la sollunga!",
    "subtitle_chunks": [
        {
            "chunk_id": 1,
            "text": "Ungalukke theriyaama, unga GPay",
            "english_caption": "INVISIBLE SHIELD",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A close-up of a glowing digital smartphone showing GPay and PhonePe app icons, surrounded by a semi-transparent glowing golden security shield, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 2,
            "text": "matrum PhonePe panathai",
            "english_caption": "UPI SECURITY",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Digital data streams forming a secure barrier, glowing holographic lock symbol, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 3,
            "text": "24 mani neramum oru 'Invisible Guard'",
            "english_caption": "24/7 GUARD",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A friendly cute robotic security guard holding a small glowing shield, smiling, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 4,
            "text": "paadhugaathuttu irukkunnu theriyuma?",
            "english_caption": "DID YOU KNOW?",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A South Indian young man scrolling phone looking surprised, phone screen glowing on face, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 5,
            "text": "Adhuthaan Artificial Intelligence (AI).",
            "english_caption": "ARTIFICIAL INTELLIGENCE",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A cute cartoon representation of a glowing digital brain, pulsing with warm soft blue and purple lighting, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 6,
            "text": "Neenga dhinamum panra",
            "english_caption": "DAILY BASIS",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A smartphone interface displaying glowing digital icons of shopping, food, and bills, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 7,
            "text": "transactions vachu intha AI",
            "english_caption": "TRANSACTIONS MONITOR",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A cute 3D cartoon style smartphone screen showing small transaction history logs popping up, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 8,
            "text": "unga spending habits-a",
            "english_caption": "SPENDING HABITS",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A digital chart/graph highlighting regular payment blocks, warm volumetric lighting, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 9,
            "text": "padichutte irukkum.",
            "english_caption": "AI LEARNING",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A robotic brain studying a chart/graph of daily habits with a magnifying glass, looking focused, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 10,
            "text": "Udhaaranathukku, dhinamum",
            "english_caption": "FOR EXAMPLE",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A friendly South Indian cartoon tea stall owner pouring hot milk tea, warm sun rays, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 11,
            "text": "tea kadaila 20 roobai",
            "english_caption": "TEA SHOP ₹20",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A charming traditional South Indian tea shop with steam rising from hot tea glass, bright warm volumetric light, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 12,
            "text": "anuppura neenga,",
            "english_caption": "REGULAR PAYMENT",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Hand holding phone scanning a QR code at a street stall, glowing energy line, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 13,
            "text": "dhideernu night 2 manikki",
            "english_caption": "NIGHT 2:00 AM",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A phone displaying a clock face reading 2:00 AM in a dark room, glowing blue light, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 14,
            "text": "yaaro oru unknown person-ukku",
            "english_caption": "UNKNOWN PERSON",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A mysterious dark hacker silhouette with a hood, looking at a glowing matrix code screen, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 15,
            "text": "50000 roobai anuppa try pannaa,",
            "english_caption": "SENDING ₹50,000",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A phone in the dark displaying an outgoing transfer screen of ₹50,000 at 2:00 AM, glowing text, dark dramatic lighting, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 16,
            "text": "AI udane alert aagi",
            "english_caption": "AI ALERTS",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A bright red warning alert sign flashing on a mobile screen, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 17,
            "text": "andha transaction-a block pannidum!",
            "english_caption": "TRANSACTION BLOCKED!",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A digital shield blocking a red hacking attempt, secure lock icon, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 18,
            "text": "Unga bank manager-a vida",
            "english_caption": "BANK MANAGER",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A funny scene of a shocked bank manager wearing glasses behind a desk, looking surprised, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 19,
            "text": "intha AI-ku ungala nalla theriyum!",
            "english_caption": "AI KNOWS YOU BETTER",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A glowing smart assistant avatar smiling from a phone screen, warm volumetric background, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 20,
            "text": "Intha information pudhusa irundha like pannittu,",
            "english_caption": "LIKE THE VIDEO",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A glowing 'Like' thumbs-up button floating in a warm volumetric background, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 21,
            "text": "'Simple Tips by VJ' channel-a subscribe pannunga!",
            "english_caption": "SUBSCRIBE TO VJ",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A large shining red 'Subscribe' button floating with sparkles, 3D Pixar style, vertical 9:16."
        }
    ]
}

if os.path.exists(fallback_path):
    with open(fallback_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception:
            data = []
else:
    data = []

# Filter out old entry with same title to prevent duplication
data = [s for s in data if s.get("title") != new_script["title"]]

# Insert as the first element
data.insert(0, new_script)

with open(fallback_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✅ Successfully updated fallback_scripts.json with Tanglish script!")
