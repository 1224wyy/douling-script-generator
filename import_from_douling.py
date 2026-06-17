import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Plan, KnowledgeDoc, KnowledgeCard, Video, Script, Ranking

app = create_app()

with app.app_context():
    # Clear existing demo data
    KnowledgeCard.query.delete()
    KnowledgeDoc.query.delete()
    Plan.query.delete()
    Video.query.delete()
    Script.query.delete()
    db.session.commit()

    # Load douling data
    with open('douling_full_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Group knowledge cards by doc_id
    cards_by_doc = {}
    for card in data.get('knowledge_cards', []):
        doc_id = card.get('doc_id', 'unknown')
        if doc_id not in cards_by_doc:
            cards_by_doc[doc_id] = []
        cards_by_doc[doc_id].append(card)

    # Group cards by group_id
    group_names = {}
    for g in data.get('knowledge_groups', []):
        group_names[g['id']] = g.get('name', '未分组')

    # Create knowledge docs from card groups
    doc_map = {}
    for doc_id, cards in cards_by_doc.items():
        # Find first card's group
        group_id = cards[0].get('group_id', '')
        group_name = group_names.get(group_id, '未分组')

        # Get document info from first card's document field
        doc_info = cards[0].get('document', {})
        doc_title = doc_info.get('title', '') if isinstance(doc_info, dict) else ''
        if not doc_title:
            doc_title = cards[0].get('title', '知识文档')[:50]

        # Collect all card content as doc content
        doc_content = '\n\n'.join([
            f"## {c.get('title', '')}\n{c.get('raw_content', c.get('principle', ''))}"
            for c in cards[:50]
        ])

        doc = KnowledgeDoc(
            title=doc_title[:200] if doc_title else f"知识文档 {len(doc_map)+1}",
            file_name=f"{doc_title[:50]}.md" if doc_title else "document.md",
            content=doc_content[:10000],
            card_count=len(cards),
            group_name=group_name,
        )
        db.session.add(doc)
        db.session.flush()
        doc_map[doc_id] = doc

    # Create knowledge cards
    for card in data.get('knowledge_cards', []):
        doc_id = card.get('doc_id', '')
        parent_doc = doc_map.get(doc_id)
        if not parent_doc:
            continue

        kc = KnowledgeCard(
            doc_id=parent_doc.id,
            title=card.get('title', '')[:200] or '知识卡片',
            content=card.get('raw_content', card.get('principle', ''))[:2000],
            tags=', '.join(card.get('tags', [])) if isinstance(card.get('tags'), list) else card.get('tags', ''),
        )
        db.session.add(kc)

    # Import plans
    for p in data.get('plans', []):
        plan = Plan(
            title=p.get('title', '策划')[:200],
            content=p.get('content', '')[:10000],
            source_type='ai',
        )
        db.session.add(plan)

    # Import videos (the most important part)
    video_count = 0
    for v in data.get('videos', []):
        title = v.get('video_title', '')[:300]
        author = v.get('author_name', '')[:100]
        url = v.get('video_url', '')
        analysis = v.get('analysis_content', '')
        cover = v.get('cover_url', '')
        is_analyzed = v.get('analysis_status') == 'analyzed'

        # Build parsed_content from available fields
        parsed_parts = [f"【视频标题】{title}"]
        if author:
            parsed_parts.append(f"【作者/账号】{author}")
        if cover:
            parsed_parts.append(f"【封面】{cover}")
        if url:
            parsed_parts.append(f"【链接】{url}")
        parsed_parts.append(f"【分析状态】{'已深度分析' if is_analyzed else '未分析'}")

        video = Video(
            url=url or f"https://v.douyin.com/{v.get('id', '')[:12]}/",
            title=title,
            author=author or '未知创作者',
            parsed_content='\n'.join(parsed_parts),
            analysis=analysis[:20000] if analysis else '',
            is_analyzed=is_analyzed,
            group_name='全部视频',
        )
        db.session.add(video)
        video_count += 1

    def safe_str(val, default=''):
        """Ensure value is a string, not a list"""
        if isinstance(val, list):
            return ', '.join(str(v) for v in val if v)
        if val is None:
            return default
        return str(val)

    # Import scripts
    for s in data.get('scripts', []):
        script = Script(
            title=s.get('title', '脚本')[:200],
            content=s.get('content', '')[:20000],
            requirement=safe_str(s.get('requirements', ''))[:2000],
            keywords=safe_str(s.get('search_keywords', '')),
        )
        db.session.add(script)

    db.session.commit()

    # Print summary
    print("=" * 60)
    print("  原站数据导入完成！")
    print(f"  Plan: {Plan.query.count()}")
    print(f"  KnowledgeDoc: {KnowledgeDoc.query.count()}")
    print(f"  KnowledgeCard: {KnowledgeCard.query.count()}")
    print(f"  Video: {Video.query.count()} (analyzed: {Video.query.filter_by(is_analyzed=True).count()})")
    print(f"  Script: {Script.query.count()}")
    print(f"  Ranking: {Ranking.query.count()}")
    print("=" * 60)

    # Sample a video
    v = Video.query.filter_by(is_analyzed=True).first()
    if v:
        print(f"\n  示例视频:")
        print(f"    Title: {v.title[:80]}")
        print(f"    Author: {v.author}")
        print(f"    Analysis length: {len(v.analysis)} chars")
        print(f"    Analysis preview: {v.analysis[:200]}...")
