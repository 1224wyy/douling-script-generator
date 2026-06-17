"""文档解析工具 - 支持 PDF/Word/TXT/MD 格式"""
import os
import re

def parse_text_file(filepath):
    """解析纯文本文件（TXT/MD）"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def parse_docx_file(filepath):
    """解析 Word 文档"""
    try:
        from docx import Document
        doc = Document(filepath)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return '\n\n'.join(paragraphs)
    except ImportError:
        return "[错误] 未安装 python-docx 库"


def parse_pdf_file(filepath):
    """解析 PDF 文档"""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(filepath)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return '\n\n'.join(pages)
    except ImportError:
        return "[错误] 未安装 PyPDF2 库"


def parse_document(filepath):
    """根据文件扩展名自动选择解析器"""
    ext = os.path.splitext(filepath)[1].lower()

    parsers = {
        '.txt': parse_text_file,
        '.md': parse_text_file,
        '.doc': parse_docx_file,
        '.docx': parse_docx_file,
        '.pdf': parse_pdf_file,
    }

    parser = parsers.get(ext)
    if not parser:
        raise ValueError(f"不支持的文件格式: {ext}")

    return parser(filepath)


def split_into_cards(content, max_cards=20):
    """
    将文档内容自动拆解为知识卡片

    策略：按段落/标题/空行分割，每段生成一个卡片
    """
    # 按空行或标题行分割
    sections = re.split(r'\n(?=#{1,3}\s|\d+[\.、]|【|［)', content)

    if len(sections) <= 1:
        # 如果没有明显分段，按双空行分割
        sections = re.split(r'\n\s*\n', content)

    # 过滤太短的片段
    cards = []
    for i, section in enumerate(sections):
        text = section.strip()
        if len(text) < 20:
            continue

        # 提取标题（第一行）
        lines = text.split('\n')
        title = lines[0].lstrip('#').strip()[:80]
        if not title:
            title = f"知识卡片 {i+1}"

        # 提取关键词标签
        tags = extract_tags(text)

        cards.append({
            'title': title,
            'content': text[:2000],
            'tags': ', '.join(tags[:5]),
        })

        if len(cards) >= max_cards:
            break

    return cards


def extract_tags(text):
    """从文本中提取关键词标签"""
    common_tags = [
        '抖音', '短视频', '直播', '带货', '运营', '涨粉', '流量',
        '脚本', '策划', '拍摄', '剪辑', '配乐', '文案', '选题',
        '美妆', '美食', '搞笑', '知识', '育儿', '情感', '干货',
        '品牌', '营销', '算法', '内容', '创意', '热门',
    ]

    found = []
    for tag in common_tags:
        if tag in text:
            found.append(tag)

    return found if found else ['通用']
