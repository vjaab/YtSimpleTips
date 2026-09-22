import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from config import get_gemini_client, GEMINI_FLASH_LITE_MODEL
from gemini_script import PIPELINE_PROMPTS, sanitize_script_against_ai_cliches

client = get_gemini_client()
topic = "மனித மூளையின் Doorway Effect: ரூமுக்குள்ள போனதும் ஏன் மறந்து போகுது?"

prompt = PIPELINE_PROMPTS["script_writer"].format(
    topic=topic,
    hook_question="ஒரு ரூம்க்குள்ள நுழைஞ்ச உடனே எதுக்கு வந்தோம்னு உங்க மூளைக்கு டக்குனு மறந்து போகுதா?",
    core_concept="இதற்கு Doorway Effect அல்லது Event Boundary என்று பெயர். மூளை புதிய இடத்திற்கு மாறும்போது பழைய நினைவுகளை ஒரு File போல மூடி வைக்கிறது",
    real_world_example="ஹாலில் இருந்து கிச்சனுக்கு தண்ணி குடிக்க போகும்போது கதவை தாண்டியதும் யோசிப்பது",
    surprising_fact="Doorway Effect மூளையின் குறைபாடு அல்ல, அது மூளையின் மெமரியை Refresh செய்யும் ஒரு சூப்பர் பவர்",
    target_segment="all"
)

response = client.models.generate_content(
    model=GEMINI_FLASH_LITE_MODEL,
    contents=prompt
)
raw_script = response.text.strip()
cleaned_script = sanitize_script_against_ai_cliches(raw_script)

print("=== GENERATED SCRIPT TEST ===")
print("Prompt Topic:", topic)
print("\n--- RAW SCRIPT ---")
print(raw_script)
print("\n--- CLEANED CONVERSATIONAL SCRIPT ---")
print(cleaned_script)
print("\nWord Count:", len(cleaned_script.split()))
