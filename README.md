# 抖灵AI创作引擎 V1.0 — 抖音脚本生成器

复刻自 [douling.vip](https://douling.vip)，一个基于 AI 的抖音短视频脚本创作辅助工具。

## 功能模块

| 模块 | 说明 |
|------|------|
| **脚本生成** | 填写标题和需求，AI 自动生成完整拍摄脚本（支持引用策划/知识库/对标视频） |
| **前期策划** | 管理策划文档，支持 AI 智能策划和文件上传自动解析 |
| **知识库** | 上传 PDF/Word/TXT/MD 文档，自动拆解为知识卡片供创作参考 |
| **对标视频** | 输入抖音链接，解析并深度分析对标视频内容 |
| **榜单** | 查看各赛道头部账号排名数据 |
| **历史记录** | 查看和管理所有已生成的脚本 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动应用

```bash
python app.py
```

### 3. 打开浏览器

访问 http://localhost:5000

### 4. 设置 API Key

在页面右上角输入框填入你的 [DeepSeek API Key](https://platform.deepseek.com/api_keys)，点击保存按钮。

## 局域网共享

启动应用后，局域网内其他设备通过你的电脑 IP 访问：

```
http://你的IP地址:5000
```

例如：`http://192.168.1.100:5000`

> 注意：防火墙需要放行 5000 端口。

## 公网部署

### Railway (推荐)

1. Fork 本项目到 GitHub
2. 在 [Railway](https://railway.app) 中导入仓库
3. 设置启动命令：`python app.py`
4. 自动获得公网链接

### Render

1. 在 [Render](https://render.com) 创建 Web Service
2. 设置 Build Command: `pip install -r requirements.txt`
3. 设置 Start Command: `gunicorn app:create_app()`

## 项目结构

```
douling-clone/
├── app.py              # Flask 主应用
├── models.py           # 数据库模型
├── config.py           # 配置文件
├── requirements.txt    # 依赖列表
├── utils/              # 工具模块
│   ├── deepseek.py     # DeepSeek API 封装
│   ├── video_parser.py # 视频解析器
│   └── document_parser.py # 文档解析器
├── templates/          # HTML 页面模板
├── static/             # CSS/JS 静态资源
├── uploads/            # 上传文件存储
└── data/               # SQLite 数据库
```

## 技术栈

- **后端**: Python Flask + SQLAlchemy + SQLite
- **前端**: 原生 HTML/CSS/JavaScript（无框架依赖）
- **AI**: DeepSeek Chat API
- **样式**: 暗色主题，响应式设计

## 注意事项

- 所有数据存储在 SQLite 中，无需额外数据库配置
- API Key 存储在浏览器 localStorage，不会上传到服务器
- 支持局域网共享，适合团队协作使用
- 非商业用途，仅供学习参考
