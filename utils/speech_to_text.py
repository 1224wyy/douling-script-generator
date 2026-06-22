"""Groq Whisper API - 视频语音转文字"""
import os
import subprocess
import requests
import tempfile

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


def _extract_audio(video_path):
    """从视频提取音频为MP3（Whisper兼容格式）"""
    mp3_path = video_path.rsplit(".", 1)[0] + "_audio.mp3"
    result = subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", video_path
    ], capture_output=True, text=True)
    try:
        duration = float(result.stdout.strip())
    except Exception:
        duration = 60
    duration = min(duration, 120)

    subprocess.run([
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "libmp3lame", "-ar", "16000", "-ac", "1",
        "-t", str(duration), mp3_path
    ], capture_output=True, check=True)
    return mp3_path, duration


def transcribe_video(video_url: str) -> dict:
    """
    下载视频 → 提取音频 → Groq Whisper 转文字

    Returns: {"text": "识别文字", "success": True/False, "error": ""}
    """
    if not GROQ_API_KEY:
        return {"text": "", "success": False, "error": "未配置 Groq API Key"}

    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except Exception:
        return {"text": "", "success": False, "error": "服务器未安装ffmpeg"}

    from utils.video_parser import parse_video_url as pvu
    info = pvu(video_url)
    play_urls = info.get("play_urls", [])

    if not play_urls:
        return {"text": "", "success": False, "error": "无法获取视频播放地址"}

    # 下载视频
    tmpdir = tempfile.mkdtemp()
    video_path = os.path.join(tmpdir, "video.mp4")
    downloaded = False
    for pu in play_urls[:3]:
        try:
            r = requests.get(pu, headers={
                "User-Agent": "com.ss.android.ugc.aweme/110801",
                "Referer": "https://www.douyin.com/",
            }, stream=True, timeout=60, verify=False)
            if r.status_code == 200:
                with open(video_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        if chunk: f.write(chunk)
                if os.path.getsize(video_path) > 100000:
                    downloaded = True
                    break
                os.remove(video_path)
        except Exception:
            continue

    if not downloaded:
        return {"text": "", "success": False, "error": "视频下载失败"}

    # 提取音频
    try:
        mp3_path, duration = _extract_audio(video_path)
    except Exception as e:
        return {"text": "", "success": False, "error": f"音频提取失败: {str(e)}"}

    # 调用 Groq Whisper
    try:
        with open(mp3_path, "rb") as f:
            resp = requests.post(
                GROQ_API_URL,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                files={"file": ("audio.mp3", f, "audio/mpeg")},
                data={"model": "whisper-large-v3", "language": "zh", "response_format": "json"},
                timeout=120,
            )
        if resp.status_code == 200:
            text = resp.json().get("text", "")
            if text:
                # 清理临时文件
                try:
                    os.remove(video_path)
                    os.remove(mp3_path)
                    os.rmdir(tmpdir)
                except Exception:
                    pass
                return {"text": text, "success": True, "error": ""}
        error = resp.text[:200]
    except Exception as e:
        error = str(e)

    try:
        os.remove(video_path)
        os.remove(mp3_path)
        os.rmdir(tmpdir)
    except Exception:
        pass

    return {"text": "", "success": False, "error": f"语音识别失败: {error}"}
