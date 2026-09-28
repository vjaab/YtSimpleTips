import json
from topic_tracker import check_story_uniqueness

test_cases = [
    ("3000 வருஷம் பழமையான தேன் கெட்டுப்போகாதா? Honey Science! 🍯", "3000 Year Old Honey", "https://en.wikipedia.org/wiki/Honey#Preservation", False),
    ("Turritopsis dohrnii - The Immortal Jellyfish Secret", "Immortal Jellyfish", "https://en.wikipedia.org/wiki/Turritopsis_dohrnii", False),
    ("Banana Hack: Why Bananas are Berries", "Banana Berry Fact", "https://en.wikipedia.org/wiki/Banana", False),
    ("Why Airplane Windows Are Round - De Havilland Comet Secret", "Airplane Windows Round", "https://en.wikipedia.org/wiki/De_Havilland_Comet", True),
    ("Sharks Are Older Than Trees - 400 Million Years Wonder", "Sharks Predate Trees", "https://en.wikipedia.org/wiki/Shark", True),
    ("Underwater Waterfall in Mauritius - Sand Illusion", "Mauritius Underwater Waterfall", "https://en.wikipedia.org/wiki/Mauritius", True),
    ("Venus Rotates Backwards - Sun Rises in West", "Venus Retrograde Rotation", "https://en.wikipedia.org/wiki/Venus", True),
    ("Oru vishayam theriyuma? 1945 Chocolate Melt Microwave", "Microwave accidental discovery", "https://en.wikipedia.org", False),
    ("2 Oceans Don't Mix in Alaska", "Two Oceans Mixing Density", "https://en.wikipedia.org", False),
    ("📱 உங்க போனை இப்படி Charge பண்ணாதீங்க! Smartphone Battery Hack", "Battery 80-20 rule", "https://en.wikipedia.org/wiki/Lithium-ion_battery", False),
    ("காகம் உங்க முகத்தை வாழ்நாள் முழுக்க மறக்காது! Crow Face Recognition", "Crows Recognize Human Faces", "https://en.wikipedia.org/wiki/Crow", True),
    ("ரூம்குள்ள போனதும் ஏன் விஷயம் மறந்து போகுது? Doorway Effect!", "Why You Forget When Entering A Room", "https://en.wikipedia.org/wiki/Doorway_effect", False),
    ("ஆக்டோபஸுக்கு 3 இதயம் & நீல நிற ரத்தம்! Octopus Anatomy", "Octopus Three Hearts Hemocyanin", "https://en.wikipedia.org/wiki/Octopus", False),
    ("தண்ணீரில் உப்பு போட்டா சீக்கிரம் கொதிக்குமா? Boiling Secret! 🧂", "Boiling Point Elevation Salt", "https://en.wikipedia.org/wiki/Boiling-point_elevation", False),
    ("Mantis Shrimp Sees 16 Color Receptors - Super Vision", "Mantis Shrimp Optical System", "https://en.wikipedia.org/wiki/Mantis_shrimp", True),
    ("Hummingbirds Can Fly Backwards and Upside Down", "Hummingbird Flight Mechanics", "https://en.wikipedia.org/wiki/Hummingbird", True),
]

passed_all = True
for title, headline, url, expected in test_cases:
    unique, reason = check_story_uniqueness(new_title=title, new_headline=headline, new_url=url)
    status = "PASS" if unique == expected else "FAIL"
    if status == "FAIL":
        passed_all = False
    print(f"[{status}] expected={expected}, got={unique}. '{title[:35]}...' -> {reason}")

print("\nAll tests passed:", passed_all)
assert passed_all, "Test suite failed!"

