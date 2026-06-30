import cv2
import os

video_path = "/Users/vijayakumarjermansraj/Desktop/google_antigravity/yt_simple_tips/scratch/study_secret.mp4"
output_dir = "/Users/vijayakumarjermansraj/.gemini/antigravity-ide/brain/abd58446-2477-4b00-adca-56798e8def07"
os.makedirs(output_dir, exist_ok=True)

cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
print(f"FPS: {fps}, Duration: {duration}s")

# Extract frame at 0.5s, 2s, 5s, 10s, 15s, 20s, 25s, 30s, 35s, 40s
times = [0.5, 2.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0]
for t in times:
    frame_no = int(t * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
    ret, frame = cap.read()
    if ret:
        out_name = f"frame_{t:.1f}s.png"
        cv2.imwrite(os.path.join(output_dir, out_name), frame)
        print(f"Saved {out_name}")
cap.release()
