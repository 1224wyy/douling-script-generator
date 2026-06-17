/**
 * 历史记录页逻辑
 */

async function loadHistory() {
    try {
        const [scripts, stats] = await Promise.all([
            apiGet('/api/scripts'),
            apiGet('/api/stats'),
        ]);

        // 更新统计
        document.getElementById('scriptCount').textContent = stats.script_count;
        document.getElementById('scriptLimit').textContent = '/ ' + stats.script_limit;
        document.getElementById('keywordCount').textContent = stats.keyword_count;
        document.getElementById('videoCount').textContent = stats.video_count;
        document.getElementById('listQuota').textContent = stats.script_count + ' / ' + stats.script_limit + ' 上限';

        // 渲染列表
        const container = document.getElementById('scriptList');
        if (scripts.length === 0) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📜</div><p class="empty-state-text">暂无历史脚本</p><p style="font-size:12px;color:var(--text-muted);">前往脚本生成页创建第一个脚本</p></div>';
            return;
        }

        container.innerHTML = scripts.map(s => `
            <div class="list-item">
                <div class="list-item-info">
                    <div class="list-item-title">📝 ${escapeHtml(s.title)}</div>
                    <div class="list-item-meta">
                        创意权重: ${s.creative_ratio}% · 关键词: ${escapeHtml(s.keywords)} · ${formatDate(s.created_at)}
                    </div>
                </div>
                <div class="list-item-actions">
                    <button class="btn btn-sm btn-outline" onclick="viewScript(${s.id})">👁</button>
                    <button class="btn btn-sm btn-outline" onclick="copyScriptContent(${s.id})">📋</button>
                    <button class="btn btn-sm btn-outline" onclick="downloadScript(${s.id},'md')">📥</button>
                    <button class="btn btn-sm btn-outline" onclick="downloadScript(${s.id},'docx')">📝</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteScript(${s.id})">🗑</button>
                </div>
            </div>
        `).join('');
    } catch (e) {
        showToast('加载失败: ' + e.message, 'error');
    }
}

async function viewScript(id) {
    try {
        const script = await apiGet('/api/scripts/' + id);
        document.getElementById('detailTitle').textContent = script.title;
        document.getElementById('detailContent').innerHTML = mdToHtml(script.content);
        document.getElementById('detailModal').style.display = 'flex';
    } catch (e) {
        showToast('加载失败', 'error');
    }
}

function closeDetailModal() {
    document.getElementById('detailModal').style.display = 'none';
}

async function copyScriptContent(id) {
    try {
        const script = await apiGet('/api/scripts/' + id);
        await navigator.clipboard.writeText(script.content);
        showToast('脚本内容已复制到剪贴板', 'success');
    } catch (e) {
        showToast('复制失败', 'error');
    }
}

function downloadScript(id, format) {
    window.open(`/api/scripts/${id}/download?format=${format}`, '_blank');
}

async function deleteScript(id) {
    if (confirm('确定删除此脚本吗？')) {
        try {
            await apiDelete('/api/scripts/' + id);
            showToast('已删除', 'success');
            loadHistory();
        } catch (e) {
            showToast('删除失败', 'error');
        }
    }
}

// 弹窗关闭事件
document.addEventListener('click', function (e) {
    if (e.target.id === 'detailModal') {
        document.getElementById('detailModal').style.display = 'none';
    }
});

document.addEventListener('DOMContentLoaded', loadHistory);
