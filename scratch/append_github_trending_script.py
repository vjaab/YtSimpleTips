# -*- coding: utf-8 -*-
import json
import os

fallback_path = "/Users/vijayakumarjermansraj/Desktop/google_antigravity/yt_simple_tips/fallback_scripts.json"

new_script = {
    "title": "GitHub-ல ஒரு Trending AI Hack! PentAGI Security! 🛡️",
    "description": "GitHub Trending page-la innaikku top trending list-la irukku PentAGI. How this autonomous AI hacking agent works explained in Tanglish by VJ. #AITamil #GitHubTrending #SimpleTipsByVJ",
    "use_case_evidence_url": "https://github.com/trending",
    "script": "Chrome matrum WhatsApp-ai vida 10 madangu powerful AI Hack... GitHub-la innaikku enna trending theriyuma? Athu thaan PentAGI. GitHub-la top trending-la irukku intha tool. Ithu oru fully autonomous AI hacking team mathiri work pannum! Metasploit, Nmap, sqlmap mathiri 20 plus top security tools-a ithu automatic-a chain panni absolute security testing pannidum. PostgreSQL knowledge graphs vachu unga code safety pattern-a analyze pannum. Professional security researchers kooda bug find panna intha tool-a thaan top-la use panranga. Intha advanced tech news ungalukku useful-a irundha like pannittu, 'Simple Tips by VJ' channel-a subscribe pannunga!",
    "relevant_links": [
        "https://github.com/trending"
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
        "block": "blok",
        "PentAGI": "pent-ay-jee",
        "Nmap": "en-map",
        "PostgreSQL": "post-gres-cue-el",
        "Metasploit": "meta-sploit",
        "sqlmap": "sequel-map"
    },
    "hook": "GitHub-la innaikku enna trending theriyuma? 🛡️",
    "summary": "How PentAGI autonomous AI hacking agent works and why it is trending on GitHub.",
    "sub_category": "ai_safety_and_scams",
    "breaking_news_level": 9,
    "keywords": [
        "GitHub Trending",
        "PentAGI",
        "AI Hacking Agent",
        "Simple Tips by VJ",
        "Tamil Tech Tips"
    ],
    "hashtags": [
        "#AITamil",
        "#TechTamil",
        "#GitHub",
        "#PentAGI",
        "#SimpleTipsByVJ"
    ],
    "comment_bait_question": "Neenga autonomous AI security tools use panni irukingala? Comment-la sollunga!",
    "subtitle_chunks": [
        {
            "chunk_id": 1,
            "text": "Chrome matrum WhatsApp-ai vida",
            "english_caption": "POWERFUL APPS",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A glowing grid of modern app icons including WhatsApp and Chrome, digital interfaces, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 2,
            "text": "10 madangu powerful AI Hack...",
            "english_caption": "10X POWER HACK",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A glowing battery icon with green electrical lightning sparks showing 10X power boost, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 3,
            "text": "GitHub-la innaikku enna trending",
            "english_caption": "GITHUB TRENDING",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A close-up of a glowing digital smartphone showing the GitHub logo and trending stars graph, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 4,
            "text": "theriyuma? Athu thaan PentAGI.",
            "english_caption": "PENTAGI REVEALED",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A sleek glowing computer setup displaying cybersecurity agents and matrix code, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 5,
            "text": "GitHub-la top trending-la",
            "english_caption": "NUMBER ONE TREND",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Glowing golden trophy floating above data flow graphs, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 6,
            "text": "irukku intha tool.",
            "english_caption": "POPULAR TOOL",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Digital terminal dashboard with stats and stars rising, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 7,
            "text": "Ithu oru fully autonomous AI",
            "english_caption": "AUTONOMOUS AGENT",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A friendly cute robotic agent typing code on a holographic laptop, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 8,
            "text": "hacking team mathiri work pannum!",
            "english_caption": "HACKING TEAM",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A team of small cute helper robots wearing hacker hoodies working together, glowing screens, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 9,
            "text": "Metasploit, Nmap, sqlmap mathiri",
            "english_caption": "SECURITY TOOLS",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A security toolbox filled with glowing digital tools and lock symbols, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 10,
            "text": "20 plus top security tools-a",
            "english_caption": "20+ POWERFUL TOOLS",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A grid of 20 glowing metallic lock and shield symbols, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 11,
            "text": "ithu automatic-a chain panni",
            "english_caption": "AUTOMATED CHAINING",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Glowing golden digital chains linking together cyber processes, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 12,
            "text": "absolute security testing pannidum.",
            "english_caption": "SECURED SYSTEM",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A giant glowing green digital lock appearing over a secure server room, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 13,
            "text": "PostgreSQL knowledge graphs vachu",
            "english_caption": "KNOWLEDGE GRAPH",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A glowing network of databases connected by light pathways, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 14,
            "text": "unga code safety pattern-a",
            "english_caption": "CODE PATTERNS",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Glowing green lines of source code scanned by a searchlight, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 15,
            "text": "analyze pannum. Professional security",
            "english_caption": "AI ANALYSIS",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A cute robot analyst pointing at security charts on a screen, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 16,
            "text": "researchers kooda bug find panna",
            "english_caption": "BUG HUNTING",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A magnifying glass highlighting a small glowing bug on a digital leaf made of chips, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 17,
            "text": "intha tool-a thaan top-la use panranga.",
            "english_caption": "TOP CHOICE",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A shiny crown placed on top of a holographic server rack, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 18,
            "text": "Intha advanced tech news ungalukku",
            "english_caption": "USEFUL TECH HACKS",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Sparkling news article screen popping out of a phone, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 19,
            "text": "useful-a irundha like pannittu,",
            "english_caption": "LIKE THE VIDEO",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A glowing 'Like' thumbs-up button floating in a warm volumetric background, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 20,
            "text": "'Simple Tips by VJ' channel-a",
            "english_caption": "VJ VIDEOS",
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Channel profile banner with glowing letters, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 21,
            "text": "subscribe pannunga!",
            "english_caption": "SUBSCRIBE",
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

print("✅ Successfully added GitHub Trending PentAGI script to fallback_scripts.json!")
