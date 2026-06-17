"""抖音视频解析 + 下载工具 - 双API策略"""
import re
import json
import os
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── UA 配置 ──
MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
PC_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
APP_UA = "com.ss.android.ugc.aweme/110801 (iPhone; iOS 16_6; Scale/3.00) Resolution/1170_2532 Version/11.8.1 Build/110801"

HEADERS_MOBILE = {"User-Agent": MOBILE_UA, "Referer": "https://www.douyin.com/"}
HEADERS_PC = {"User-Agent": PC_UA, "Referer": "https://www.douyin.com/", "Cookie": "msToken=abc123"}
HEADERS_APP = {"User-Agent": APP_UA}
HEADERS_DOWNLOAD = {"User-Agent": APP_UA, "Referer": "https://www.douyin.com/"}


def extract_video_id(url: str) -> str | None:
    for p in [r'/video/(\d+)', r'modal_id=(\d+)', r'/note/(\d+)']:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


def resolve_video_id(share_url: str) -> str:
    """跟随短链重定向，提取 video_id"""
    resp = requests.get(share_url, headers=HEADERS_MOBILE, allow_redirects=True, timeout=15)
    real_url = resp.url
    vid = extract_video_id(real_url)
    if vid:
        return vid
    m = re.search(r'"aweme_id"\s*:\s*"(\d+)"', resp.text)
    if m:
        return m.group(1)
    raise ValueError(f"无法提取 video_id: {real_url}")


def fetch_via_snssdk(video_id: str) -> dict | None:
    """方法A: snssdk App API（模拟抖音App）"""
    try:
        r = requests.get(f"https://aweme.snssdk.com/aweme/v1/aweme/detail/?aweme_id={video_id}",
                         headers=HEADERS_APP, timeout=15)
        if r.status_code == 200 and r.text.strip():
            data = r.json()
            if data.get("aweme_detail"):
                return data["aweme_detail"]
    except Exception:
        pass
    return None


def fetch_via_web_api(video_id: str) -> dict | None:
    """方法B: douyin.com Web API"""
    try:
        r = requests.get(f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}",
                         headers=HEADERS_PC, timeout=15)
        if r.status_code == 200 and r.text.strip():
            data = r.json()
            if data.get("aweme_detail"):
                return data["aweme_detail"]
    except Exception:
        pass
    return None


def get_aweme_detail(share_url: str, video_id: str) -> dict:
    """双API策略获取视频详情"""
    # 方法A优先（更稳定）
    data = fetch_via_snssdk(video_id)
    if data:
        return data, "snssdk"
    # 方法B备用
    data = fetch_via_web_api(video_id)
    if data:
        return data, "web_api"
    raise RuntimeError("无法获取视频数据，视频可能已被删除或需要登录")


def extract_video_info(aweme: dict, raw_url: str = "", source: str = "") -> dict:
    """从 aweme_detail 提取所有信息"""
    author = aweme.get("author", {})
    stats = aweme.get("statistics", {})
    music = aweme.get("music", {})
    video_info = aweme.get("video", {})
    duration_ms = aweme.get("duration", 0)

    # 时长
    if duration_ms and duration_ms > 1000:
        sec = duration_ms // 1000
        duration_str = f"{sec//60:02d}:{sec%60:02d}"
    else:
        duration_str = ""

    # 标签
    tags = [t.get("hashtag_name", "") for t in aweme.get("text_extra", []) if t.get("hashtag_name")]

    # 封面
    cover = ""
    for k in ["cover", "origin_cover"]:
        urls = video_info.get(k, {}).get("url_list", [])
        if urls:
            cover = urls[0]
            break

    # 播放地址（无水印）
    play_urls = []
    for k in ["play_addr_h264", "play_addr_265", "play_addr"]:
        for u in video_info.get(k, {}).get("url_list", []):
            if u and "http" in u and u not in play_urls:
                play_urls.append(u)
    # bit_rate 列表
    for br in (video_info.get("bit_rate") or []):
        for u in br.get("play_addr", {}).get("url_list", []):
            if u and "http" in u and u not in play_urls:
                play_urls.append(u)

    return {
        "title": aweme.get("desc", ""),
        "author": author.get("nickname", ""),
        "author_uid": author.get("uid", ""),
        "author_signature": author.get("signature", ""),
        "description": aweme.get("desc", ""),
        "tags": tags,
        "music": music.get("title", music.get("author", "")),
        "duration": duration_str,
        "cover_url": cover,
        "transcript": aweme.get("desc", ""),
        "likes": str(stats.get("digg_count", stats.get("like_count", ""))),
        "comments": str(stats.get("comment_count", "")),
        "shares": str(stats.get("share_count", "")),
        "collects": str(stats.get("collect_count", "")),
        "play_count": str(stats.get("play_count", "")),
        "raw_url": raw_url,
        "video_id": aweme.get("aweme_id", ""),
        "parse_status": "success",
        "play_urls": play_urls,
        "source": source,
    }


def download_video_file(play_urls: list[str], output_dir: str, title: str) -> str | None:
    """下载无水印视频，返回文件路径"""
    if not play_urls:
        return None

    safe = title[:60].replace("/", "_").replace("\\", "_").replace(" ", "_") or "douyin_video"
    filepath = os.path.join(output_dir, f"{safe}-no-watermark.mp4")

    for idx, url in enumerate(play_urls):
        for verify in (True, False):
            try:
                with requests.get(url, headers=HEADERS_DOWNLOAD, stream=True, timeout=120, verify=verify) as r:
                    r.raise_for_status()
                    with open(filepath + ".part", "wb") as f:
                        for chunk in r.iter_content(8192):
                            if chunk:
                                f.write(chunk)
                    os.replace(filepath + ".part", filepath)
                    # 校验
                    with open(filepath, "rb") as f:
                        if f.read(12)[4:8] == b"ftyp":
                            return filepath
                    os.remove(filepath)
            except Exception:
                if os.path.exists(filepath + ".part"):
                    os.remove(filepath + ".part")
                continue

    return None


def parse_video_url(url: str, download: bool = False, download_dir: str = "") -> dict:
    """
    解析抖音视频链接

    Args:
        url: 抖音视频链接
        download: 是否同时下载视频文件
        download_dir: 下载目录

    Returns:
        包含视频信息的字典，如果 download=True 还会包含 downloaded_file 字段
    """
    if not url or not url.strip():
        raise ValueError("请输入视频链接")
    url = url.strip()

    # Step 1: 解析 video_id
    session = requests.Session()
    session.headers.update(HEADERS_MOBILE)

    video_id = extract_video_id(url)
    real_url = url
    try:
        resp = session.get(url, allow_redirects=True, timeout=15)
        real_url = resp.url
        if not video_id:
            video_id = extract_video_id(real_url)
    except Exception:
        if not video_id:
            return _fail_result(url, "无法访问链接")

    if not video_id:
        try:
            for hist in resp.history:
                vid = extract_video_id(hist.headers.get("Location", ""))
                if vid:
                    video_id = vid
                    break
        except Exception:
            pass

    if not video_id:
        return _fail_result(url, "无法提取视频ID")

    # Step 2: 双API获取详情
    try:
        aweme, source = get_aweme_detail(url, video_id)
    except Exception as e:
        return _fail_result(url, f"获取视频失败: {e}")

    info = extract_video_info(aweme, url, source)
    info["real_url"] = real_url
    info["parse_status"] = "success"

    # Step 3: 下载视频（可选）
    if download and info["play_urls"]:
        dl_dir = download_dir or os.path.join(os.getcwd(), "downloads")
        os.makedirs(dl_dir, exist_ok=True)
        filepath = download_video_file(info["play_urls"], dl_dir, info["title"] or video_id)
        if filepath:
            info["downloaded_file"] = filepath
            info["file_size"] = os.path.getsize(filepath)
        else:
            info["download_error"] = "下载失败：所有CDN地址不可用"

    return info


def _fail_result(url: str, msg: str) -> dict:
    return {
        "title": "", "author": "", "description": msg,
        "tags": [], "music": "", "duration": "", "cover_url": "",
        "likes": "", "comments": "", "shares": "", "collects": "",
        "raw_url": url, "video_id": "", "parse_status": "failed",
    }


def parse_video_deep(url: str, api_key=None):
    return parse_video_url(url)
