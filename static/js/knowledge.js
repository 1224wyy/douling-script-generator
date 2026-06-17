/**
 * 知识库页逻辑
 */

let currentGroup = 'all';
let allDocs = [];

async function loadDocs() {
    try {
        allDocs = await apiGet('/api/knowledge/docs');
        // 同时加载卡片总数
        const cards = await apiGet('/api/knowledge/cards');
        document.getElementById('cardCount').textContent = cards.length;
        document.getElementById('docCount').textContent = allDocs.length;
        renderDocs();
        updateGroupTabs();
    } catch (e) {
        showToast('加载失败: ' + e.message, 'error');
    }
}

function updateGroupTabs() {
    const groups = new Set(allDocs.map(d => d.group_name || '未分组'));
    const container = document.getElementById('groupTabs');
    container.innerHTML = `
        <span class="tab ${currentGroup === 'all' ? 'active' : ''}" onclick="filterByGroup('all')">全部</span>
        ${[...groups].map(g => `<span class="tab ${currentGroup === g ? 'active' : ''}" onclick="filterByGroup('${escapeHtml(g)}')">${escapeHtml(g)}</span>`).join('')}
    `;
}

function filterByGroup(group) {
    currentGroup = group;
    renderDocs();
    updateGroupTabs();
}

function renderDocs() {
    const docs = currentGroup === 'all' ? allDocs : allDocs.filter(d => d.group_name === currentGroup);
    const container = document.getElementById('docList');
    if (docs.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📄</div><p class="empty-state-text">暂无知识文档</p></div>';
        return;
    }
    container.innerHTML = docs.map(d => `
        <div class="list-item">
            <div class="list-item-info">
                <div class="list-item-title">📄 ${escapeHtml(d.title)}</div>
                <div class="list-item-meta">
                    ${d.card_count} 个知识卡片 · ${escapeHtml(d.group_name)} · ${formatDate(d.created_at)}
                </div>
            </div>
            <div class="list-item-actions">
                <button class="btn btn-sm btn-outline" onclick="viewCards(${d.id})">📋 查看卡片</button>
                <button class="btn btn-sm btn-outline" onclick="changeGroup(${d.id}, '${escapeHtml(d.group_name)}')">📁 分组</button>
                <button class="btn btn-sm btn-danger" onclick="deleteDoc(${d.id})">🗑</button>
            </div>
        </div>
    `).join('');
}

// ===== 上传文件 =====
async function uploadKnowledgeFile(input) {
    const files = input.files;
    if (!files.length) return;

    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        try {
            const res = await fetch('/api/knowledge/upload', { method: 'POST', body: formData });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error);
            showToast(`「${file.name}」上传成功，已拆解为 ${data.cards?.length || 0} 个知识卡片`, 'success');
        } catch (e) {
            showToast(`「${file.name}」上传失败: ${e.message}`, 'error');
        }
    }
    input.value = '';
    loadDocs();
}

// ===== 拖拽上传支持 =====
['cardUploadZone', 'docUploadZone'].forEach(id => {
    const zone = document.getElementById(id);
    if (!zone) return;
    zone.addEventListener('dragover', e => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length) {
            const input = document.getElementById('knowledgeFileInput');
            const dt = new DataTransfer();
            for (const f of files) dt.items.add(f);
            input.files = dt.files;
            uploadKnowledgeFile(input);
        }
    });
});

// ===== 查看知识卡片 =====
async function viewCards(docId) {
    try {
        const cards = await apiGet('/api/knowledge/cards?doc_id=' + docId);
        const content = cards.length === 0
            ? '<p class="empty-state-text">暂无知识卡片</p>'
            : cards.map(c => `
                <div class="card" style="margin-bottom:12px;">
                    <div style="font-weight:600;margin-bottom:6px;">📌 ${escapeHtml(c.title)}</div>
                    <div style="font-size:13px;color:var(--text-secondary);line-height:1.7;">${mdToHtml(c.content)}</div>
                    <div style="margin-top:8px;">${c.tags.split(', ').map(t => `<span class="tag tag-blue">${escapeHtml(t)}</span>`).join(' ')}</div>
                </div>
            `).join('');
        document.getElementById('cardsContent').innerHTML = content;
        document.getElementById('cardsModal').style.display = 'flex';
    } catch (e) {
        showToast('加载失败', 'error');
    }
}

function closeCardsModal() {
    document.getElementById('cardsModal').style.display = 'none';
}

// ===== 分组管理 =====
function changeGroup(docId, currentName) {
    const newGroup = prompt('输入分组名称（留空=未分组）：', currentName || '');
    if (newGroup === null) return;
    apiPut('/api/knowledge/docs/' + docId, { group_name: newGroup || '未分组' }).then(() => {
        showToast('分组已更新', 'success');
        loadDocs();
    }).catch(e => showToast('更新失败', 'error'));
}

// ===== 删除文档 =====
async function deleteDoc(id) {
    if (confirm('确定删除此知识文档及所有关联卡片吗？')) {
        try {
            await apiDelete('/api/knowledge/docs?id=' + id);
            showToast('已删除', 'success');
            loadDocs();
        } catch (e) {
            showToast('删除失败', 'error');
        }
    }
}

function batchManage() {
    showToast('批量管理功能开发中', 'info');
}

document.addEventListener('DOMContentLoaded', loadDocs);
