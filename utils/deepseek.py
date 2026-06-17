"""DeepSeek API 调用封装"""
import json
import requests

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

DEFAULT_SYSTEM_PROMPT = """你是一个专业的抖音短视频脚本策划师和分镜导演。你精通各赛道的爆款脚本创作，输出必须是可直接指导拍摄的详细分镜脚本。

请严格按照以下格式输出：

## 🎬 视频概述
- **视频标题**：（吸引眼球的爆款标题，2-3个备选）
- **视频类型**：口播/剧情/Vlog/教程/产品种草
- **目标受众**：精准用户画像
- **核心卖点/核心信息**：一句话总结
- **预计时长**：XX秒
- **内容风格**：温暖治愈/快节奏/悬疑/幽默/专业

---

## 📋 分镜脚本（逐镜头）

| 镜头编号 | 时间码 | 景别 | 画面内容 | 台词/口播 | 字幕 | 拍摄手法/运镜 | 道具/场景 | 备注 |
|----------|--------|------|----------|-----------|------|---------------|------------|------|
| 1 | 0:00-0:03 | 特写/近景/中景/全景 | 具体的画面描述 | 演员要说的话 | 屏幕字幕文字 | 推/拉/摇/移/固定 | 所需道具 | 情绪/音效 |

（每个镜头一行，覆盖整个视频所有镜头）

---

## 🎥 拍摄执行清单
- **场景需求**：具体场地描述
- **道具清单**：逐项列出
- **人员需求**：演员/摄影师/灯光
- **灯光方案**：自然光/环形灯/侧光
- **服装建议**：着装风格

---

## 🎵 音频方案
- **BGM**：具体曲目或风格
- **音效**：关键节点音效（如"叮"提示音、转场音效）
- **旁白/配音要求**：语速、语调、情绪

---

## 💬 字幕与文案策略
- **标题字幕**：视频开头大字
- **强调字幕**：关键信息高亮
- **结尾引导字幕**：互动引导
- **话题标签**：#标签1 #标签2

---

## 📊 预期效果与优化
- **完播率预估**：XX%
- **互动率预估**：XX%
- **能否投流**：适合/不适合 Dou+ 投放
- **AB测试建议**：可替换的开头/结尾方案

---

请确保：每个镜头都具体、可执行、有画面感。台词口语化接地气，符合抖音调性。"""


def call_deepseek(api_key, user_message, system_prompt=None, references=None, max_tokens=4096):
    """
    调用 DeepSeek API

    Args:
        api_key: 用户的 API Key
        user_message: 用户的需求描述
        system_prompt: 系统提示词（可选）
        references: 参考内容列表 [{"type": "plan/knowledge/video", "title": "...", "content": "..."}]
        max_tokens: 最大输出token数

    Returns:
        str: AI 生成的脚本内容
    """
    if not api_key:
        raise ValueError("请先设置 DeepSeek API Key")

    system = system_prompt or DEFAULT_SYSTEM_PROMPT

    # 拼接参考内容
    ref_text = ""
    if references:
        ref_text = "\n\n## 参考内容：\n"
        for i, ref in enumerate(references):
            ref_text += f"\n### {ref['type']} - {ref['title']}\n{ref['content']}\n"

    full_message = user_message + ref_text if ref_text else user_message

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": full_message}
        ],
        "temperature": 0.8,
        "max_tokens": max_tokens,
    }

    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=120)

    if response.status_code != 200:
        error_msg = response.json().get('error', {}).get('message', response.text)
        raise Exception(f"API 调用失败: {error_msg}")

    result = response.json()
    return result['choices'][0]['message']['content']


FAST_MODE_PROMPT = """你是一个抖音脚本策划师。输出精简但可直接拍摄的分镜脚本：

## 🎬 视频概述
- 标题 / 类型 / 时长 / 风格

## 📋 分镜脚本
| 镜号 | 时间 | 景别 | 画面 | 台词 | 字幕 | 拍摄 |
（每个镜头一行，覆盖全片）

## 🎵 BGM与音效

## 💬 话题标签

精简输出，每项一句话即可，不要展开论述。"""


def generate_script(api_key, title, requirement, creative_ratio=50,
                    plan_refs=None, knowledge_refs=None, video_refs=None,
                    fast_mode=False):
    """生成抖音脚本"""
    system_prompt = FAST_MODE_PROMPT if fast_mode else DEFAULT_SYSTEM_PROMPT

    # 构建参考比例描述
    plan_ratio = int((100 - creative_ratio) * 0.35)
    knowledge_ratio = int((100 - creative_ratio) * 0.35)
    video_ratio = int((100 - creative_ratio) * 0.30)

    user_message = f"""请根据以下信息生成抖音短视频脚本：

## 脚本标题
{title}

## 创作需求
{requirement}

## 参考权重分配
- 创意发挥：{creative_ratio}%
- 前期策划参考：{plan_ratio}%
- 知识库参考：{knowledge_ratio}%
- 对标视频参考：{video_ratio}%

请按照权重平衡创意与参考内容，生成一份完整的拍摄脚本。"""

    # 拼接所有参考
    references = []
    for p in (plan_refs or []):
        references.append({"type": "前期策划", "title": p.get('title', ''), "content": p.get('content', '')})
    for k in (knowledge_refs or []):
        references.append({"type": "知识库", "title": k.get('title', ''), "content": k.get('content', '')})
    for v in (video_refs or []):
        references.append({"type": "对标视频", "title": v.get('title', ''), "content": v.get('analysis', v.get('parsed_content', ''))})

    max_tokens = 2048 if fast_mode else 4096
    return call_deepseek(api_key, user_message, system_prompt, references, max_tokens=max_tokens)


def generate_plan(api_key, topic, requirements=""):
    """AI 智能生成策划方案"""
    system_prompt = """你是一个专业的短视频内容策划师。请根据用户提供的主题，生成一份详细的前期策划方案。

策划方案应包含：
1. **账号定位**：目标受众、内容方向、人设风格
2. **内容规划**：选题方向、内容系列、更新频率
3. **拍摄方案**：需要的设备、场景、道具
4. **运营策略**：发布时间、话题标签、互动策略
5. **变现路径**：可能的变现方式

请输出结构清晰、可执行的策划方案。"""

    user_message = f"策划主题：{topic}\n\n额外要求：{requirements}" if requirements else f"策划主题：{topic}"

    return call_deepseek(api_key, user_message, system_prompt)


def analyze_video_content(api_key, video_title, video_content=""):
    """深度分析视频内容 - 输出详细的结构化分析报告"""
    system_prompt = """你是一个专业的抖音短视频分析师和脚本策划师。你的任务是对给定的视频进行深度拆解分析，输出一份详细、具体、可直接用于脚本创作参考的分析报告。

请严格按照以下结构输出分析报告：

## 📊 视频基本信息摘要
- 视频主题、核心卖点、目标受众的简要判断

## 🎬 内容结构深度拆解

### 开头（前3秒）
- 用了什么钩子手法（悬念/痛点/反常识/情感共鸣/数据冲击？）
- 具体话术/画面是什么
- 为什么这个开头能留住用户

### 中段（核心内容）
- 信息结构：总分总？并列递进？问题-解决方案？
- 节奏控制：每几秒切换一个信息点
- 画面/声音配合技巧
- 核心信息传递的方式（演示/口播/字幕/对比）

### 结尾（最后5秒）
- 如何引导互动（点赞/评论/关注/转发）
- 转化引导方式（挂车/留资/私域）
- 是否埋了"再看一遍"或"关注看后续"的钩子

## 🔥 爆款因素分析
- 这条视频能爆/能跑量的核心原因（至少3点）
- 情绪价值：激发了什么情绪（焦虑/好奇/感动/愤怒/认同）
- 信息价值：提供了什么有用的东西（知识/技巧/观点/优惠）
- 社交货币：用户为什么会转发/艾特好友

## 🎯 目标受众与赛道定位
- 精准用户画像
- 所属赛道及细分领域
- 平台推荐算法会推给什么样的人群

## 📝 口播文案逐段解析
- 逐段拆分文案，标注每段的作用和技巧
- 标注"金句"和可复用的表达方式

## 🛠️ 制作手法与技术分析
- 拍摄手法（运镜/构图/光线）
- 剪辑节奏（快切/慢镜/Jump Cut）
- BGM运用（卡点/情绪配合）
- 字幕风格和特效

## 💡 可复用的创作方法论
- 提炼出3-5条可以套用的创作公式/模板
- 这个视频背后的"底层逻辑"是什么

## 🔄 改进与创新空间
- 如果重新制作同主题视频，可以在哪些方面优化
- 有什么角度是原视频没覆盖但值得尝试的
- 如何与自己的产品/内容结合

## 🏷️ 关键词与标签建议
- 推荐使用的热门话题标签（5-10个）
- SEO关键词

请确保分析具体、落地、可直接指导脚本创作。避免空泛的评价，每一点都要有具体的例子或话术参考。"""

    user_message = f"""请对以下抖音视频进行深度分析：

## 视频标题
{video_title}

## 视频内容/文案
{video_content}

请输出完整的分析报告。"""

    return call_deepseek(api_key, user_message, system_prompt, max_tokens=8192)


CHAT_PLANNING_SYSTEM = """你是一个专业的抖音短视频策划顾问。你的任务是通过多轮对话，帮助用户逐步细化策划方案。

对话规则：
1. 每次回复要简短、聚焦，不要一次性输出完整策划方案
2. 通过提问引导用户思考：赛道、受众、人设、内容方向、变现模式等
3. 每轮只问 1-2 个关键问题
4. 根据用户的回答动态调整后续问题
5. 当信息足够充分时（通常 3-5 轮对话后），输出结构化的策划方案摘要

策划方案应包含：账号定位、内容规划、拍摄方案、运营策略、变现路径

在你的每条回复末尾，将当前策划进度以JSON格式附上（方便前端解析）：
<!--PLAN_JSON
{
  "plan_title": "策划主题",
  "plan_summary": "当前积累的策划内容摘要"
}
-->

如果没有足够信息还无法生成摘要，plan_summary 留空字符串。"""


def chat_planning(api_key, history):
    """
    多轮对话策划

    Args:
        api_key: DeepSeek API Key
        history: [{"role": "user/assistant", "content": "..."}]

    Returns:
        {"reply": "AI回复", "plan_title": "主题", "plan_summary": "摘要"}
    """
    if not history:
        return {"reply": "请告诉我你想做什么类型的抖音账号？", "plan_title": "", "plan_summary": ""}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    messages = [{"role": "system", "content": CHAT_PLANNING_SYSTEM}]
    messages.extend(history)

    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 2048,
    }

    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=120)

    if response.status_code != 200:
        error_msg = response.json().get('error', {}).get('message', response.text)
        raise Exception(f"API 调用失败: {error_msg}")

    result = response.json()
    reply = result['choices'][0]['message']['content']

    # 提取 JSON 块
    import re
    plan_title = ""
    plan_summary = ""
    json_match = re.search(r'<!--PLAN_JSON\s*({.+?})\s*-->', reply, re.DOTALL)
    if json_match:
        try:
            plan_data = json.loads(json_match.group(1))
            plan_title = plan_data.get('plan_title', '')
            plan_summary = plan_data.get('plan_summary', '')
        except json.JSONDecodeError:
            pass

        # 移除 JSON 标记，让回复更干净
        reply = re.sub(r'<!--PLAN_JSON.+?-->', '', reply, flags=re.DOTALL).strip()

    return {
        "reply": reply,
        "plan_title": plan_title,
        "plan_summary": plan_summary,
    }
