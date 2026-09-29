import sys
import os

# Add workspace to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ecosystem_logic import generate_youtube_tags, sanitize_and_fit_tags, calculate_youtube_tags_length, CATEGORY_TAG_POOLS

def test_tags():
    print("=" * 60)
    print("TESTING EXPANDED YOUTUBE TAG GENERATION")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Science Curiosities",
            "title": "மூளையில் இவ்வளவு கரண்ட்டா? 💡 Brain Electricity Facts",
            "keywords": ["Human Brain", "Electricity", "Neurons", "Light Bulb", "Bio Electricity"],
            "hashtags": ["#தெரியுமா", "#VJVideos", "#ScienceFacts", "#BrainPower"],
            "category": "🧠 Mind-Blowing Science Curiosities"
        },
        {
            "name": "Human Body & Psychology",
            "title": "சூரியனைப் பார்த்தால் தும்மல் வருவது ஏன்? ☀️ Photic Sneeze",
            "keywords": ["Photic Sneeze", "Nerve Wiring", "Sunlight Reflex", "Human Body"],
            "hashtags": ["#HumanBody", "#PsychologyFacts", "#VJVideos"],
            "category": "🧬 Human Body & Dark Psychology"
        },
        {
            "name": "Money-Saving & Smart Living",
            "title": "Supermarket-ல இந்த தப்பை பண்ணாதீங்க! 🛒 Psychology Trick",
            "keywords": ["Supermarket Tricks", "Dairy Placement", "Save Money", "Shopping Hack"],
            "hashtags": ["#MoneySavingTips", "#LifeHacks", "#VJVideos"],
            "category": "💰 Money-Saving & Smart Living Tricks"
        },
        {
            "name": "Empty Inputs / Fallback",
            "title": "",
            "keywords": [],
            "hashtags": [],
            "category": ""
        }
    ]
    
    for case in test_cases:
        print(f"\n--- Testing: {case['name']} ---")
        tags = generate_youtube_tags(
            title=case["title"],
            keywords=case["keywords"],
            hashtags=case["hashtags"],
            category=case["category"],
            max_chars=400
        )
        
        yt_chars = calculate_youtube_tags_length(tags)
        
        print(f"Total Tags Generated: {len(tags)}")
        print(f"YouTube True Length (including spaces/quotes/commas): {yt_chars} / 500 max characters")
        print(f"Sample Tags (first 10): {tags[:10]}")
        print(f"Sample Tags (last 5): {tags[-5:]}")
        
        # Assertions
        assert len(tags) >= 20, f"Expected at least 20 tags, got {len(tags)}"
        assert yt_chars <= 400, f"Expected yt_chars <= 400, got {yt_chars}"
        assert all("<" not in t and ">" not in t for t in tags), "Found forbidden angle bracket in tags"
        assert all(not t.startswith("#") for t in tags), "Found leading hashtag in tags"
        
        # Check uniqueness (case-insensitive)
        lower_tags = [t.lower() for t in tags]
        assert len(lower_tags) == len(set(lower_tags)), "Duplicate tags detected!"
        print(f"✅ PASSED for {case['name']}")

    # Stress Test: Over 100 candidate tags
    print("\n--- Stress Testing: Massive Tag List (> 1000 chars) ---")
    huge_tags = [f"VeryLongKeywordNumber{i}AboutSomethingInteresting" for i in range(50)]
    fitted = sanitize_and_fit_tags(huge_tags, max_chars=400)
    yt_huge_len = calculate_youtube_tags_length(fitted)
    print(f"Fitted {len(fitted)} tags out of 50. Total YouTube length: {yt_huge_len}")
    assert yt_huge_len <= 400
    print("✅ Stress test passed safely under 400 characters!")

    print("\n🎉 ALL YOUTUBE TAG GENERATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_tags()
