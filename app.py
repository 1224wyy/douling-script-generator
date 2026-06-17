"""抖音脚本生成器 - Flask 主应用"""
import os
import json
from flask import Flask, render_template, request, jsonify, send_from_directory
from config import Config
from models import db, Plan, KnowledgeDoc, KnowledgeCard, Video, Script
from utils.deepseek import generate_script, generate_plan, analyze_video_content
from utils.document_parser import parse_document, split_into_cards
from utils.video_parser import parse_video_url
from datetime import datetime, timezone

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ==================== 页面路由 ====================

    @app.route('/')
    @app.route('/home')
    def home():
        return render_template('home.html')

    @app.route('/planning')
    def planning():
        return render_template('planning.html')

    @app.route('/knowledge')
    def knowledge():
        return render_template('knowledge.html')

    @app.route('/accounts')
    def accounts():
        return render_template('accounts.html')

    @app.route('/history')
    def history():
        return render_template('history.html')

    # ==================== API: 脚本生成 ====================

    @app.route('/api/generate', methods=['POST'])
    def api_generate():
        data = request.get_json()
        api_key = data.get('api_key', '')
        title = data.get('title', '')
        requirement = data.get('requirement', '')
        creative_ratio = data.get('creative_ratio', 50)
        plan_ids = data.get('plan_ids', [])
        knowledge_ids = data.get('knowledge_ids', [])
        video_ids = data.get('video_ids', [])

        if not title or not requirement:
            return jsonify({"error": "请填写脚本标题和创作需求"}), 400

        if not api_key:
            return jsonify({"error": "请先设置 DeepSeek API Key"}), 400

        # 获取参考内容
        plan_refs = [Plan.query.get(pid).to_dict() for pid in plan_ids if Plan.query.get(pid)]
        knowledge_refs = [KnowledgeCard.query.get(kid).to_dict() for kid in knowledge_ids if KnowledgeCard.query.get(kid)]
        video_refs = [Video.query.get(vid).to_dict() for vid in video_ids if Video.query.get(vid)]
        fast_mode = data.get('fast_mode', False)

        try:
            result = generate_script(api_key, title, requirement, creative_ratio,
                                     plan_refs, knowledge_refs, video_refs,
                                     fast_mode=fast_mode)

            # 提取关键词（简单的标签提取）
            keywords = extract_keywords(requirement)

            # 保存脚本
            script = Script(
                title=title,
                content=result,
                requirement=requirement,
                creative_ratio=creative_ratio,
                plan_refs=json.dumps(plan_ids),
                knowledge_refs=json.dumps(knowledge_ids),
                video_refs=json.dumps(video_ids),
                keywords=keywords,
            )
            db.session.add(script)
            db.session.commit()

            return jsonify({"success": True, "script": script.to_dict()})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/scripts', methods=['GET', 'POST'])
    def api_scripts():
        if request.method == 'POST':
            data = request.get_json()
            script = Script(
                title=data.get('title', ''),
                content=data.get('content', ''),
                requirement=data.get('requirement', ''),
                keywords=extract_keywords(data.get('content', '')[:200]),
            )
            db.session.add(script)
            db.session.commit()
            return jsonify({"success": True, "script": script.to_dict()})

        scripts = Script.query.order_by(Script.created_at.desc()).all()
        return jsonify([s.to_dict() for s in scripts])

    @app.route('/api/scripts/<int:script_id>', methods=['GET', 'DELETE'])
    def api_script(script_id):
        script = Script.query.get_or_404(script_id)
        if request.method == 'DELETE':
            db.session.delete(script)
            db.session.commit()
            return jsonify({"success": True})
        return jsonify(script.to_dict())

    # ==================== API: 前期策划 ====================

    @app.route('/api/plans', methods=['GET', 'POST'])
    def api_plans():
        if request.method == 'POST':
            data = request.get_json()
            plan = Plan(
                title=data.get('title', ''),
                content=data.get('content', ''),
                source_type=data.get('source_type', 'manual'),
            )
            db.session.add(plan)
            db.session.commit()
            return jsonify({"success": True, "plan": plan.to_dict()})

        plans = Plan.query.order_by(Plan.updated_at.desc()).all()
        return jsonify([p.to_dict() for p in plans])

    @app.route('/api/plans/<int:plan_id>', methods=['GET', 'PUT', 'DELETE'])
    def api_plan(plan_id):
        plan = Plan.query.get_or_404(plan_id)
        if request.method == 'DELETE':
            db.session.delete(plan)
            db.session.commit()
            return jsonify({"success": True})
        elif request.method == 'PUT':
            data = request.get_json()
            plan.title = data.get('title', plan.title)
            plan.content = data.get('content', plan.content)
            db.session.commit()
            return jsonify({"success": True, "plan": plan.to_dict()})
        return jsonify(plan.to_dict())

    @app.route('/api/planning/chat', methods=['POST'])
    def api_planning_chat():
        """AI 聊天式策划"""
        data = request.get_json()
        api_key = data.get('api_key', '')
        history = data.get('history', [])

        if not api_key:
            return jsonify({"error": "请先设置 DeepSeek API Key"}), 400

        try:
            from utils.deepseek import chat_planning
            result = chat_planning(api_key, history)
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/plans/ai-create', methods=['POST'])
    def api_plan_ai():
        data = request.get_json()
        api_key = data.get('api_key', '')
        topic = data.get('topic', '')
        requirements = data.get('requirements', '')

        if not topic:
            return jsonify({"error": "请输入策划主题"}), 400
        if not api_key:
            return jsonify({"error": "请先设置 DeepSeek API Key"}), 400

        try:
            result = generate_plan(api_key, topic, requirements)
            plan = Plan(
                title=topic,
                content=result,
                source_type='ai',
            )
            db.session.add(plan)
            db.session.commit()
            return jsonify({"success": True, "plan": plan.to_dict()})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/plans/upload', methods=['POST'])
    def api_plan_upload():
        file = request.files.get('file')
        if not file:
            return jsonify({"error": "请选择文件"}), 400

        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext not in {'.pdf', '.doc', '.docx', '.txt', '.md'}:
            return jsonify({"error": "不支持的文件格式，请上传 PDF/Word/TXT/MD"}), 400

        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            content = parse_document(filepath)
            plan = Plan(
                title=os.path.splitext(filename)[0],
                content=content,
                source_type='upload',
                file_path=filepath,
            )
            db.session.add(plan)
            db.session.commit()
            return jsonify({"success": True, "plan": plan.to_dict()})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ==================== API: 知识库 ====================

    @app.route('/api/knowledge/upload', methods=['POST'])
    def api_knowledge_upload():
        file = request.files.get('file')
        if not file:
            return jsonify({"error": "请选择文件"}), 400

        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext not in {'.pdf', '.doc', '.docx', '.txt', '.md'}:
            return jsonify({"error": "不支持的文件格式"}), 400

        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            content = parse_document(filepath)

            # 创建知识文档
            doc = KnowledgeDoc(
                title=os.path.splitext(filename)[0],
                file_name=filename,
                file_path=filepath,
                content=content,
            )
            db.session.add(doc)
            db.session.flush()

            # 自动拆解为知识卡片
            cards_data = split_into_cards(content)
            for card_data in cards_data:
                card = KnowledgeCard(
                    doc_id=doc.id,
                    title=card_data['title'],
                    content=card_data['content'],
                    tags=card_data['tags'],
                )
                db.session.add(card)

            doc.card_count = len(cards_data)
            db.session.commit()

            cards = KnowledgeCard.query.filter_by(doc_id=doc.id).all()
            return jsonify({
                "success": True,
                "doc": doc.to_dict(),
                "cards": [c.to_dict() for c in cards],
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/knowledge/docs', methods=['GET', 'DELETE'])
    def api_knowledge_docs():
        if request.method == 'DELETE':
            doc_id = request.args.get('id')
            if doc_id:
                doc = KnowledgeDoc.query.get_or_404(doc_id)
                KnowledgeCard.query.filter_by(doc_id=doc.id).delete()
                db.session.delete(doc)
                db.session.commit()
                return jsonify({"success": True})
            return jsonify({"error": "缺少文档ID"}), 400

        docs = KnowledgeDoc.query.order_by(KnowledgeDoc.created_at.desc()).all()
        return jsonify([d.to_dict() for d in docs])

    @app.route('/api/knowledge/cards', methods=['GET'])
    def api_knowledge_cards():
        doc_id = request.args.get('doc_id')
        if doc_id:
            cards = KnowledgeCard.query.filter_by(doc_id=doc_id).all()
        else:
            cards = KnowledgeCard.query.order_by(KnowledgeCard.created_at.desc()).all()
        return jsonify([c.to_dict() for c in cards])

    @app.route('/api/knowledge/docs/<int:doc_id>', methods=['PUT'])
    def api_knowledge_doc_update(doc_id):
        doc = KnowledgeDoc.query.get_or_404(doc_id)
        data = request.get_json()
        if 'group_name' in data:
            doc.group_name = data['group_name']
        if 'title' in data:
            doc.title = data['title']
        db.session.commit()
        return jsonify({"success": True, "doc": doc.to_dict()})

    # ==================== API: 对标视频 ====================

    @app.route('/api/videos', methods=['GET'])
    def api_videos():
        videos = Video.query.order_by(Video.created_at.desc()).all()
        return jsonify([v.to_dict() for v in videos])

    @app.route('/api/videos/<int:video_id>', methods=['GET', 'DELETE'])
    def api_video(video_id):
        video = Video.query.get_or_404(video_id)
        if request.method == 'DELETE':
            db.session.delete(video)
            db.session.commit()
            return jsonify({"success": True})
        return jsonify(video.to_dict())

    @app.route('/api/videos/parse', methods=['POST'])
    def api_video_parse():
        data = request.get_json()
        url = data.get('url', '')
        if not url:
            return jsonify({"error": "请输入视频链接"}), 400

        try:
            # 调用真实解析器
            parsed = parse_video_url(url)
        except Exception as e:
            return jsonify({"error": f"视频解析失败: {str(e)}"}), 400

        # 构建解析内容摘要（用于AI分析的素材）
        parsed_content_parts = []
        parsed_content_parts.append(f"【视频标题】{parsed.get('title', '未知')}")
        if parsed.get('author'):
            parsed_content_parts.append(f"【作者/账号】{parsed['author']}")
            if parsed.get('author_signature'):
                parsed_content_parts.append(f"【作者简介】{parsed['author_signature'][:200]}")
        if parsed.get('description'):
            parsed_content_parts.append(f"【视频简介】{parsed['description']}")
        if parsed.get('duration'):
            parsed_content_parts.append(f"【时长】{parsed['duration']}")
        if parsed.get('music'):
            parsed_content_parts.append(f"【BGM】{parsed['music']}")
        if parsed.get('tags'):
            parsed_content_parts.append(f"【标签】{', '.join(parsed['tags'])}")

        stats_parts = []
        if parsed.get('likes'):
            stats_parts.append(f"点赞 {parsed['likes']}")
        if parsed.get('comments'):
            stats_parts.append(f"评论 {parsed['comments']}")
        if parsed.get('shares'):
            stats_parts.append(f"分享 {parsed['shares']}")
        if parsed.get('collects'):
            stats_parts.append(f"收藏 {parsed['collects']}")
        if stats_parts:
            parsed_content_parts.append(f"【数据表现】{' · '.join(stats_parts)}")

        if parsed.get('video_id'):
            parsed_content_parts.append(f"【视频ID】{parsed['video_id']}")
        if parsed.get('real_url'):
            parsed_content_parts.append(f"【真实链接】{parsed['real_url']}")

        if not parsed.get('title') and not parsed.get('description'):
            parsed_content_parts.append("（未能提取到详细内容，可尝试手动输入后再分析）")

        video = Video(
            url=url,
            title=parsed.get('title') or f"视频 {url[-12:]}",
            author=parsed.get('author') or '未知创作者',
            parsed_content='\n'.join(parsed_content_parts),
        )
        db.session.add(video)
        db.session.commit()

        return jsonify({
            "success": True,
            "video": video.to_dict(),
            "parsed_detail": {
                "title": parsed.get('title', ''),
                "author": parsed.get('author', ''),
                "description": parsed.get('description', ''),
                "tags": parsed.get('tags', []),
                "music": parsed.get('music', ''),
                "duration": parsed.get('duration', ''),
                "cover_url": parsed.get('cover_url', ''),
                "likes": parsed.get('likes', ''),
                "comments": parsed.get('comments', ''),
                "shares": parsed.get('shares', ''),
                "collects": parsed.get('collects', ''),
                "video_id": parsed.get('video_id', ''),
                "parse_status": parsed.get('parse_status', 'success'),
            }
        })

    @app.route('/api/videos/analyze', methods=['POST'])
    def api_video_analyze():
        data = request.get_json()
        api_key = data.get('api_key', '')
        video_id = data.get('video_id')

        video = Video.query.get_or_404(video_id)
        if not api_key:
            return jsonify({"error": "请先设置 DeepSeek API Key"}), 400

        try:
            analysis = analyze_video_content(api_key, video.title, video.parsed_content)
            video.analysis = analysis
            video.is_analyzed = True
            db.session.commit()
            return jsonify({"success": True, "video": video.to_dict()})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route('/api/videos/<int:video_id>', methods=['PUT'])
    def api_video_update(video_id):
        video = Video.query.get_or_404(video_id)
        data = request.get_json()
        if 'group_name' in data:
            video.group_name = data['group_name']
        if 'title' in data:
            video.title = data['title']
        if 'author' in data:
            video.author = data['author']
        if 'parsed_content' in data:
            video.parsed_content = data['parsed_content']
        db.session.commit()
        return jsonify({"success": True, "video": video.to_dict()})

    @app.route('/api/videos/manual', methods=['POST'])
    def api_video_manual():
        """手动创建视频条目"""
        data = request.get_json()
        title = data.get('title', '').strip()
        if not title:
            return jsonify({"error": "请输入视频标题"}), 400

        video = Video(
            url=data.get('url', '手动输入'),
            title=title,
            author=data.get('author', ''),
            parsed_content=data.get('parsed_content', ''),
        )
        db.session.add(video)
        db.session.commit()
        return jsonify({"success": True, "video": video.to_dict()})

    # ==================== API: 统计 ====================

    @app.route('/api/stats', methods=['GET'])
    def api_stats():
        return jsonify({
            "script_count": Script.query.count(),
            "script_limit": 500,
            "keyword_count": count_keywords(),
            "video_count": Video.query.count(),
        })

    return app


def extract_keywords(text):
    """从文本中提取关键词"""
    common = ['抖音', '短视频', '直播', '带货', '运营', '涨粉', '流量',
              '脚本', '策划', '拍摄', '剪辑', '配乐', '文案', '选题',
              '美妆', '美食', '搞笑', '知识', '育儿', '情感', '干货']
    found = [t for t in common if t in text]
    return ', '.join(found[:5]) if found else '通用'


def count_keywords():
    """统计所有脚本使用过的关键词"""
    scripts = Script.query.all()
    all_keywords = set()
    for s in scripts:
        if s.keywords:
            for k in s.keywords.split(', '):
                all_keywords.add(k)
    return len(all_keywords)


if __name__ == '__main__':
    app = create_app()
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'), exist_ok=True)
    print("\n" + "=" * 50)
    print("  抖音脚本生成器 V1.0")
    print("  访问地址: http://localhost:5000")
    print("  局域网共享: http://0.0.0.0:5000")
    print("=" * 50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)
