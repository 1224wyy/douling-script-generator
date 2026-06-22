"""讯飞语音听写 - 视频语音转文字"""
import json
import base64
import hashlib
import hmac
import time
import os
import subprocess
import requests
import tempfile
import urllib3

urllib3.disable_warnings()

XF_APPID = os.environ.get("XF_APPID", "")
XF_APIKEY = os.environ.get("XF_APIKEY", "")
XF_APISECRET = os.environ.get("XF_APISECRET", "")
XF_IAT_URL = "https://iat-api.xfyun.cn/v2/iat"


def _build_auth_url():
    """构建鉴权URL"""
    host = "iat-api.xfyun.cn"
    path = "/v2/iat"
    now = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    sign_str = f"host: {host}\ndate: {now}\nGET {path} HTTP/1.1"
    sig = base64.b64encode(
        hmac.new(XF_APISECRET.encode(), sign_str.encode(), hashlib.sha256).digest()
    ).decode()
    auth = f'api_key="{XF_APIKEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{sig}"'
    return f"https://{host}{path}?authorization={base64.b64encode(auth.encode()).decode()}&date={now.replace(' ', '%20')}&host={host}"


def _extract_audio(video_path):
    """从视频中提取16kHz/16bit/mono WAV音频"""
    wav_path = video_path.rsplit(".", 1)[0] + "_audio.wav"
    # 用ffprobe检查时长
    result = subprocess.run([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "csv=p=0", video_path
    ], capture_output=True, text=True)
    try:
        duration = float(result.stdout.strip())
    except Exception:
        duration = 60

    subprocess.run([
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        "-t", str(min(duration, 120)),
        wav_path
    ], capture_output=True, check=True)
    return wav_path, min(duration, 120)


def _call_xunfei_asr(audio_file, duration):
    """调用讯飞语音听写API"""
    try:
        with open(audio_file, "rb") as f:
            audio_data = f.read()
    except Exception:
        return ""

    # 如果音频小于10KB，跳过
    if len(audio_data) < 10000:
        return ""

    # 构建请求
    param = {
        "common": {"app_id": XF_APPID},
        "business": {
            "language": "zh_cn",
            "domain": "iat",
            "accent": "mandarin",
            "dwa": "wpgs",        # 动态修正
            "vad_eos": 3000,       # 后端点检测
        },
        "data": {
            "status": 2,           # 最后一帧
            "format": "audio/L16;rate=16000",
            "encoding": "raw",
            "audio": base64.b64encode(audio_data).decode(),
        }
    }

    url = _build_auth_url()
    headers = {"Content-Type": "application/json"}

    try:
        resp = requests.post(url, json=param, headers=headers, timeout=60)
        if resp.status_code == 200:
            result = resp.json()
            if result.get("code") == 0 and result.get("data", {}).get("result"):
                text = result["data"]["result"].get("text", "")
                # 清理标点
                return text
        else:
            # 切片模式重试
            return _call_xunfei_sliced(audio_file)
    except Exception:
        pass
    return ""


def _call_xunfei_sliced(audio_file):
    """切片模式：大文件分段发送"""
    try:
        with open(audio_file, "rb") as f:
            audio_data = f.read()
    except Exception:
        return ""

    chunk_size = 32000  # 约2秒
    chunks = [audio_data[i:i+chunk_size] for i in range(0, len(audio_data), chunk_size)]
    if len(chunks) < 2:
        return ""

    results = []
    for idx, chunk in enumerate(chunks):
        status = 2 if idx == len(chunks) - 1 else 1
        param = {
            "common": {"app_id": XF_APPID},
            "business": {
                "language": "zh_cn",
                "domain": "iat",
                "accent": "mandarin",
            },
            "data": {
                "status": status,
                "format": "audio/L16;rate=16000",
                "encoding": "raw",
                "audio": base64.b64encode(chunk).decode(),
            }
        }

        url = _build_auth_url()
        headers = {"Content-Type": "application/json"}

        try:
            resp = requests.post(url, json=param, headers=headers, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("code") == 0 and result.get("data", {}).get("result"):
                    text = result["data"]["result"].get("text", "")
                    if text:
                        results.append(text)
        except Exception:
            continue
        time.sleep(0.1)

    return "".join(results)


def transcribe_video(video_url: str) -> dict:
    """
    下载视频 → 提取音频 → ASR转文字

    Returns: {"text": "识别出的文字", "success": True/False, "error": ""}
    """
    # 检查ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except Exception:
        return {"text": "", "success": False,
                "error": "服务器未安装ffmpeg，无法提取音频。请手动输入视频文案。"}

    # 下载视频
    print("[ASR] 下载视频...")
    tmpdir = tempfile.mkdtemp()
    video_path = os.path.join(tmpdir, "video.mp4")

    # 用我们的解析器获取播放地址
    from utils.video_parser import parse_video_url as pvu
    info = pvu(video_url)
    play_urls = info.get("play_urls", [])

    if not play_urls:
        return {"text": "", "success": False, "error": "无法获取视频播放地址"}

    # 下载
    downloaded = False
    for pu in play_urls[:3]:
        try:
            resp = requests.get(pu, headers={
                "User-Agent": "com.ss.android.ugc.aweme/110801",
                "Referer": "https://www.douyin.com/",
            }, stream=True, timeout=60, verify=False)
            if resp.status_code == 200:
                with open(video_path, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        if chunk:
                            f.write(chunk)
                file_size = os.path.getsize(video_path)
                if file_size > 100000:  # >100KB
                    downloaded = True
                    break
                os.remove(video_path)
        except Exception:
            continue

    if not downloaded:
        return {"text": "", "success": False, "error": "视频下载失败"}

    # 提取音频
    print("[ASR] 提取音频...")
    try:
        wav_path, duration = _extract_audio(video_path)
    except Exception as e:
        os.remove(video_path)
        return {"text": "", "success": False, "error": f"音频提取失败: {str(e)}"}

    # ASR识别
    print(f"[ASR] 语音识别 (时长{duration:.0f}秒)...")
    text = _call_xunfei_asr(wav_path, duration)

    # 清理
    try:
        os.remove(video_path)
        os.remove(wav_path)
        os.rmdir(tmpdir)
    except Exception:
        pass

    if text:
        return {"text": text, "success": True, "error": ""}
    return {"text": "", "success": False, "error": "语音识别无结果，可能是纯音乐/无声视频"}
