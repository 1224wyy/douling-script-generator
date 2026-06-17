"""抖音视频链接解析工具 - 通过API提取视频信息"""
import re
import json
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def extract_video_id(url):
    """从各种抖音链接格式中提取视频ID"""
    # https://www.douyin.com/video/7602853343500700991
    m = re.search(r'/video/(\d+)', url)
    if m:
        return m.group(1)

    # https://www.douyin.com/user/xxx?modal_id=7602853343500700991
    m = re.search(r'modal_id=(\d+)', url)
    if m:
        return m.group(1)

    return None


def _api_fetch_aweme(video_id):
    """通过抖音官方API获取视频详情"""
    url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}"
    headers = {
        **HEADERS,
        "Referer": f"https://www.douyin.com/video/{video_id}",
    }

    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        return {}

    data = resp.json()
    aweme = data.get('aweme_detail', {})

    if not aweme:
        return {}

    # 提取信息
    author = aweme.get('author', {})
    stats = aweme.get('statistics', {})
    music = aweme.get('music', {})
    video_info = aweme.get('video', {})
    duration_ms = aweme.get('duration', 0)

    # 格式化时长
    if duration_ms and duration_ms > 1000:
        seconds = duration_ms // 1000
        duration_str = f"{seconds // 60:02d}:{seconds % 60:02d}"
    else:
        duration_str = ""

    # 标签
    tags = []
    for item in aweme.get('text_extra', []):
        tag = item.get('hashtag_name', '')
        if tag:
            tags.append(tag)

    # 封面
    cover_url = ""
    covers = video_info.get('cover', {}).get('url_list', [])
    if covers:
        cover_url = covers[0]
    if not cover_url:
        covers = video_info.get('origin_cover', {}).get('url_list', [])
        if covers:
            cover_url = covers[0]

    return {
        "title": aweme.get('desc', ''),
        "author": author.get('nickname', ''),
        "author_uid": author.get('uid', ''),
        "author_signature": author.get('signature', ''),
        "description": aweme.get('desc', ''),
        "tags": tags,
        "music": music.get('title', music.get('author', '')),
        "duration": duration_str,
        "cover_url": cover_url,
        "transcript": aweme.get('desc', ''),
        "likes": str(stats.get('digg_count', '')),
        "comments": str(stats.get('comment_count', '')),
        "shares": str(stats.get('share_count', '')),
        "collects": str(stats.get('collect_count', '')),
    }


def parse_video_url(url):
    """
    解析抖音视频链接

    支持:
    - v.douyin.com 短链接 (自动跟随重定向)
    - www.douyin.com/video/xxx 直接链接
    """
    if not url or not url.strip():
        raise ValueError("请输入视频链接")

    url = url.strip()

    session = requests.Session()
    session.headers.update(HEADERS)

    # 第一步：如果是短链接，跟随重定向获取真实URL和视频ID
    real_url = url
    video_id = extract_video_id(url)

    try:
        resp = session.get(url, allow_redirects=True, timeout=15)
        real_url = resp.url
        if not video_id:
            video_id = extract_video_id(real_url)
    except requests.RequestException:
        # 无法访问，尝试直接从URL提取ID
        if not video_id:
            return _empty_result(url, "无法访问该链接，请检查链接是否正确")

    # 从重定向历史中提取ID
    if not video_id:
        try:
            for hist in resp.history:
                loc = hist.headers.get('Location', '')
                video_id = extract_video_id(loc)
                if video_id:
                    break
        except Exception:
            pass

    # 第二步：通过API获取视频详情
    if video_id:
        try:
            api_data = _api_fetch_aweme(video_id)
            if api_data and api_data.get("title"):
                api_data["raw_url"] = url
                api_data["real_url"] = real_url
                api_data["video_id"] = video_id
                api_data["parse_status"] = "success"
                return api_data
        except Exception:
            pass

    # 第三步：降级方案 - 从页面HTML提取基础信息
    try:
        resp = session.get(real_url, timeout=15)
        html = resp.text

        info = _empty_result(url, "未能提取到视频详情")
        info["real_url"] = real_url
        info["video_id"] = video_id

        # 尝试从页面meta标签提取
        title_m = re.search(r'<title>([^<]+)</title>', html)
        if title_m:
            title = title_m.group(1).replace(' - 抖音', '').strip()
            if title and len(title) > 1:
                info["title"] = title
                info["description"] = title

        desc_m = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html)
        if desc_m:
            info["description"] = desc_m.group(1)
            if not info["title"]:
                info["title"] = info["description"][:100]

        if info.get("title"):
            info["parse_status"] = "partial"
        else:
            info["parse_status"] = "needs_manual"
            info["description"] = (
                "无法自动提取视频详情。\n"
                "建议点击「手动输入」粘贴视频标题和文案。"
            )

        return info

    except requests.RequestException:
        return _empty_result(url, "无法访问视频页面")


def _empty_result(url, msg=""):
    """返回空的解析结果"""
    return {
        "title": "",
        "author": "",
        "description": msg,
        "tags": [],
        "music": "",
        "duration": "",
        "cover_url": "",
        "transcript": "",
        "raw_url": url,
        "real_url": url,
        "video_id": extract_video_id(url),
        "parse_status": "failed",
    }


def parse_video_deep(url, api_key=None):
    """深度解析（保留接口兼容）"""
    return parse_video_url(url)
