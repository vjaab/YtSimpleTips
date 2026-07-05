import os
import json
import time
import subprocess
import shutil

def _notify_kaggle_failure(message):
    """Send a Telegram alert when Kaggle GPU encounters issues."""
    try:
        from telegram_selector import notify_telegram
        notify_telegram(message, "🔴")
    except Exception as e:
        print(f"⚠️ Telegram notification failed: {e}")

def trigger_kaggle_gpu_job(script_data, custom_map):
    """
    Saves job data, pushes to Kaggle, waits for completion, and downloads results.
    
    Returns:
        dict with results on success, or dict with "error" key on failure.
    """
    print("🚀 [kaggle_handover] Initiating Kaggle GPU Handover for IndicF5 Tamil Voice Cloning...")
    
    # Configure environment variables for both legacy and new Kaggle CLI versions
    from config import KAGGLE_USERNAME, KAGGLE_KEY
    if KAGGLE_KEY:
        os.environ["KAGGLE_KEY"] = KAGGLE_KEY
        os.environ["KAGGLE_API_TOKEN"] = KAGGLE_KEY
    if KAGGLE_USERNAME:
        os.environ["KAGGLE_USERNAME"] = KAGGLE_USERNAME
        
    # Dynamically write ~/.kaggle/kaggle.json and ~/.kaggle/access_token to ensure auth works
    try:
        kaggle_dir = os.path.expanduser("~/.kaggle")
        os.makedirs(kaggle_dir, exist_ok=True)
        
        # Legacy/standard API config file
        kaggle_json_path = os.path.join(kaggle_dir, "kaggle.json")
        with open(kaggle_json_path, "w", encoding="utf-8") as f:
            json.dump({"username": KAGGLE_USERNAME, "key": KAGGLE_KEY}, f)
        os.chmod(kaggle_json_path, 0o600)
        
        # New CLI version access token file
        if KAGGLE_KEY:
            access_token_path = os.path.join(kaggle_dir, "access_token")
            with open(access_token_path, "w", encoding="utf-8") as f:
                f.write(KAGGLE_KEY)
            os.chmod(access_token_path, 0o600)
            
        print("🔒 Successfully updated Kaggle API configuration files.")
    except Exception as e:
        print(f"⚠️ Warning: Could not write Kaggle credential files: {e}")
        
    scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    
    # Copy audio_gen.py to scripts/audio_gen.py so it gets uploaded to Kaggle
    try:
        shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_gen.py"), os.path.join(scripts_dir, "audio_gen.py"))
        print("📦 Staged local audio_gen.py for Kaggle upload.")
    except Exception as copy_err:
        print(f"⚠️ Warning: Could not stage audio_gen.py for Kaggle upload: {copy_err}")
        
    # 1. Inject Job Data directly into the script
    from config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID
    job_payload = {
        "script": script_data.get("script"),
        "custom_map": custom_map or {},
        "elevenlabs_api_key": ELEVENLABS_API_KEY,
        "elevenlabs_voice_id": ELEVENLABS_VOICE_ID,
        "face_path": script_data.get("lipsync_face_path", "assets/video/Firefly_video_final.mp4")
    }
    
    worker_script_path = os.path.join(scripts_dir, "kaggle_worker.py")
    if not os.path.exists(worker_script_path):
        print(f"❌ Worker script missing: {worker_script_path}")
        return {"error": "worker_missing"}
        
    with open(worker_script_path, "r", encoding='utf-8') as f:
        worker_code = f.read()
    
    # Inject payload at the top
    injection = f"\nJOB_PAYLOAD = {json.dumps(job_payload)}\n"
    
    # Write temporary execution file that Kaggle will upload
    temp_script_path = os.path.join(scripts_dir, "ytsimpletips_gpu_worker.py")
    with open(temp_script_path, "w", encoding='utf-8') as f:
        f.write(injection + worker_code)
        
    # Update Metadata to point to the temp script
    meta_path = os.path.join(scripts_dir, "kernel-metadata.json")
    if not os.path.exists(meta_path):
        meta = {
            "id": "vijayakumarj/ytsimpletips-gpu-worker",
            "title": "ytsimpletips-gpu-worker",
            "code_file": "ytsimpletips_gpu_worker.py",
            "language": "python",
            "kernel_type": "script",
            "is_private": "true",
            "enable_gpu": "true",
            "enable_internet": "true",
            "dataset_sources": [],
            "kernel_sources": [],
            "competition_sources": []
        }
        with open(meta_path, "w", encoding='utf-8') as f:
            json.dump(meta, f, indent=4)
    else:
        with open(meta_path, "r", encoding='utf-8') as f:
            meta = json.load(f)
        meta["code_file"] = "ytsimpletips_gpu_worker.py"
        with open(meta_path, "w", encoding='utf-8') as f:
            json.dump(meta, f, indent=4)
            
    # Copy vj.wav to the scripts directory if it exists, so Kaggle can upload it as part of the kernel files
    vj_wav_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "vj.wav")
    if os.path.exists(vj_wav_src):
        shutil.copy(vj_wav_src, os.path.join(scripts_dir, "vj.wav"))
        print("📁 Copied vj.wav to scripts/ for Kaggle kernel upload.")
        
    # 2. Push Kernel
    print("📤 Pushing kernel to Kaggle...")
    try:
        kaggle_cmd = "kaggle"
        if os.path.exists("venv/bin/kaggle"):
            kaggle_cmd = "venv/bin/kaggle"
        elif os.path.exists("venv/Scripts/kaggle"):
            kaggle_cmd = "venv/Scripts/kaggle"
            
        # Force NvidiaTeslaT4 accelerator to avoid incompatible Tesla P100 (which has compute capability 6.0, unsupported by PyTorch/CUDA wheels in the Kaggle environment)
        push_res = subprocess.run(
            [kaggle_cmd, "kernels", "push", "-p", scripts_dir, "--accelerator", "NvidiaTeslaT4"],
            capture_output=True,
            text=True,
            timeout=90
        )
        if push_res.returncode != 0:
            raise subprocess.CalledProcessError(
                push_res.returncode,
                push_res.args,
                output=push_res.stdout,
                stderr=push_res.stderr
            )
        kernel_id = meta.get("id", "vijayakumarj/ytsimpletips-gpu-worker")
        print(f"✅ Kernel pushed successfully!")
        print(f"🔗 Kaggle URL: https://www.kaggle.com/code/{kernel_id}")
    except subprocess.CalledProcessError as cpe:
        parts = []
        if cpe.output:
            parts.append(f"STDOUT: {cpe.output.strip()}")
        if cpe.stderr:
            parts.append(f"STDERR: {cpe.stderr.strip()}")
        err_detail = " | ".join(parts) if parts else str(cpe)
        msg = f"Failed to push Kaggle kernel: {err_detail}"
        print(f"❌ {msg}")
        _notify_kaggle_failure(f"🚨 Kaggle Push Failed\n\n{msg}\n\nPipeline will attempt ElevenLabs fallback.")
        return {"error": "push_failed", "message": msg}
    except Exception as e:
        msg = f"Failed to push Kaggle kernel: {e}"
        print(f"❌ {msg}")
        _notify_kaggle_failure(f"🚨 Kaggle Push Failed\n\n{msg}\n\nPipeline will attempt ElevenLabs fallback.")
        return {"error": "push_failed", "message": msg}

    # 3. Poll for Completion (with an absolute safety limit)
    kernel_id = "vijayakumarj/ytsimpletips-gpu-worker"
    print(f"🔗 Kaggle URL: https://www.kaggle.com/code/{kernel_id}")
    print(f"⌛ Waiting for Kaggle job ({kernel_id}) to finish...")
    
    max_queued_mins = 10
    max_running_mins = 30
    poll_interval_s = 20
    absolute_timeout_s = (max_queued_mins + max_running_mins + 5) * 60
    
    start_time = time.time()
    job_started_running = False
    running_start_time = None
    
    while True:
        elapsed_s = time.time() - start_time
        elapsed_mins = elapsed_s / 60
        
        # Absolute safety timeout to prevent infinite hangs
        if elapsed_s > absolute_timeout_s:
            msg = f"Kaggle job exceeded absolute safety timeout of {absolute_timeout_s/60:.0f} minutes."
            print(f"❌ {msg}")
            _notify_kaggle_failure(
                f"⏰ Kaggle GPU Absolute Timeout\n\n{msg}\n\n"
                f"Pipeline will attempt ElevenLabs fallback."
            )
            return {"error": "absolute_timeout", "message": msg}
        
        try:
            status_output = subprocess.check_output(
                [kaggle_cmd, "kernels", "status", kernel_id], text=True
            )
            status_lower = status_output.strip().lower()
            print(f"   Status: {status_output.strip()}")
            
            if "complete" in status_lower:
                print("✅ Kaggle job finished successfully!")
                break
            
            if "error" in status_lower:
                msg = f"Kaggle job '{kernel_id}' reported an error after {elapsed_mins:.1f} min."
                print(f"❌ {msg}")
                _notify_kaggle_failure(f"🚨 Kaggle GPU Job Error\n\n{msg}\n\nFallback to ElevenLabs will trigger.")
                return {"error": "job_error", "message": msg}
            
            is_queued = "queued" in status_lower
            is_running = "running" in status_lower
            
            if is_running and not job_started_running:
                job_started_running = True
                running_start_time = time.time()
                print(f"   🟢 Job started running after {elapsed_mins:.1f} min in queue.")
            
            if is_queued and not job_started_running and elapsed_s > (max_queued_mins * 60):
                msg = f"Kaggle job stuck in QUEUED for {elapsed_mins:.0f} min. GPU likely unavailable."
                print(f"❌ {msg}")
                _notify_kaggle_failure(f"⏰ Kaggle GPU Queue Timeout\n\n{msg}\n\nFallback to ElevenLabs will trigger.")
                return {"error": "queued_timeout", "message": msg}
            
            if job_started_running and running_start_time:
                running_elapsed_s = time.time() - running_start_time
                if running_elapsed_s > (max_running_mins * 60):
                    msg = f"Kaggle job running for {running_elapsed_s/60:.0f} min (limit: {max_running_mins} min)."
                    print(f"❌ {msg}")
                    _notify_kaggle_failure(f"⏰ Kaggle GPU Run Timeout\n\n{msg}\n\nFallback to ElevenLabs will trigger.")
                    return {"error": "run_timeout", "message": msg}
                    
        except Exception as e:
            print(f"⚠️ Error checking status: {e}")
            
        time.sleep(poll_interval_s)

    # 4. Download Results
    print("📥 Downloading results from Kaggle...")
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    try:
        subprocess.run([kaggle_cmd, "kernels", "output", kernel_id, "-p", output_dir], check=True, timeout=120)
        
        results_file = os.path.join(output_dir, "results.json")
        if os.path.exists(results_file):
            with open(results_file, "r") as f:
                results = json.load(f)
            
            if results.get("audio_path"):
                results["audio_path"] = os.path.abspath(os.path.join(output_dir, results["audio_path"]))
            if results.get("lipsync_path"):
                results["lipsync_path"] = os.path.abspath(os.path.join(output_dir, results["lipsync_path"]))
                
            # Copy temp files out of scripts folder to clean up git workspace
            try:
                if os.path.exists(temp_script_path):
                    os.remove(temp_script_path)
                if os.path.exists(os.path.join(scripts_dir, "vj.wav")):
                    os.remove(os.path.join(scripts_dir, "vj.wav"))
            except Exception:
                pass
                
            return results
        else:
            msg = "Kaggle job completed but results.json not found in output."
            print(f"❌ {msg}")
            _notify_kaggle_failure(f"🚨 Kaggle Results Missing\n\n{msg}")
            return {"error": "download_failed", "message": msg}
    except Exception as e:
        msg = f"Failed to download/process Kaggle results: {e}"
        print(f"❌ {msg}")
        _notify_kaggle_failure(f"🚨 Kaggle Download Failed\n\n{msg}")
        return {"error": "download_failed", "message": msg}
