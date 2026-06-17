/**
 * 知识库 - 卡片网格
 */
let allCards = [];
let currentTag = 'all';

async function loadCards() {
    try {
        allCards = await apiGet('/api/knowledge/cards');
        document.getElementById('cardCountText').textContent = `${allCards.length} 个知识卡片`;
        buildTagFilter();
        renderCards();
    } catch (e) {
        showToast('加载失败: ' + e.message, 'error');
    }
}

function buildTagFilter() {
    const tags = new Set();
    allCards.forEach(c => {
        if (c.tags) c.tags.split(', ').forEach(t => { if (t) tags.add(t); });
    });
    const container = document.getElementById('tagFilter');
    container.innerHTML = `<span class="tab ${currentTag==='all'?'active':''}" onclick="filterByTag('all')">全部</span>`;
    [...tags].sort().forEach(t => {
        container.innerHTML += `<span class="tab ${currentTag===t?'active':''}" onclick="filterByTag('${escapeHtml(t)}')">${escapeHtml(t)}</span>`;
    });
}

function filterByTag(tag) {
    currentTag = tag;
    buildTagFilter();
    renderCards();
}

function renderCards() {
    const cards = currentTag === 'all' ? allCards : allCards.filter(c => (c.tags || '').includes(currentTag));
    const container = document.getElementById('cardsGrid');

    if (cards.length === 0) {
        container.innerHTML = '<div class="empty-state"><p class="empty-state-text">该分类下暂无知识卡片</p></div>';
        return;
    }

    // 卡片色系
    const colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#84cc16'];
    container.innerHTML = cards.map((c, i) => {
        const color = colors[i % colors.length];
        const tagHtml = c.tags ? c.tags.split(', ').slice(0, 3).map(t => `<span class="tag" style="background:${color}20;color:${color};">${escapeHtml(t)}</span>`).join('') : '';
        const preview = (c.content || '').substring(0, 150);
        return `
        <div class="card knowledge-card" onclick="viewCardDetail('${escapeHtml(c.title)}', '${escapeHtml(c.content)}', '${escapeHtml(c.tags || '')}')" style="border-left:3px solid ${color};cursor:pointer;">
            <div class="card-title" style="font-size:14px;margin-bottom:8px;">📌 ${escapeHtml(c.title)}</div>
            <div class="card-body" style="font-size:12px;color:var(--text-secondary);line-height:1.6;display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden;">${escapeHtml(preview)}</div>
            ${tagHtml ? `<div style="margin-top:10px;display:flex;gap:4px;flex-wrap:wrap;">${tagHtml}</div>` : ''}
        </div>`;
    }).join('');
}

function viewCardDetail(title, content, tags) {
    document.getElementById('cardModalTitle').textContent = title;
    document.getElementById('cardModalContent').innerHTML = mdToHtml(content);
    const tagContainer = document.getElementById('cardModalTags');
    if (tags) {
        tagContainer.innerHTML = tags.split(', ').map(t => `<span class="tag tag-blue">${escapeHtml(t)}</span>`).join(' ');
    } else {
        tagContainer.innerHTML = '';
    }
    document.getElementById('cardModal').style.display = 'flex';
}

// 点击遮罩关闭
document.addEventListener('click', e => {
    if (e.target.id === 'cardModal') document.getElementById('cardModal').style.display = 'none';
});

// 上传文件
async function uploadKnowledgeFile(input) {
    const files = input.files;
    if (!files.length) return;
    for (const file of files) {
        const fd = new FormData(); fd.append('file', file);
        try {
            const res = await fetch('/api/knowledge/upload', { method: 'POST', body: fd });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error);
            showToast(`「${file.name}」上传成功，${data.cards?.length || 0} 张卡片`, 'success');
        } catch (e) {
            showToast(`上传失败: ${e.message}`, 'error');
        }
    }
    input.value = '';
    loadCards();
}

document.addEventListener('DOMContentLoaded', loadCards);
