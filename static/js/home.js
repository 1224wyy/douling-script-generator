/**
 * 脚本生成页逻辑
 */

let selectedPlanIds = [];
let selectedKnowledgeIds = [];
let selectedVideoIds = [];

function updateRatioDisplay() {
    const creative = parseInt(document.getElementById('creativeRatio').value);
    document.getElementById('creativeValue').textContent = creative + '%';
    const remaining = 100 - creative;
    document.getElementById('planRatioText').textContent = Math.round(remaining * 0.35) + '%';
    document.getElementById('knowledgeRatioText').textContent = Math.round(remaining * 0.35) + '%';
    document.getElementById('videoRatioText').textContent = Math.round(remaining * 0.30) + '%';
}

// ===== 加载参考列表（含全选功能）=====
async function loadPlanRefs() {
    try {
        const plans = await apiGet('/api/plans');
        const container = document.getElementById('planRefs');
        if (plans.length === 0) {
            container.innerHTML = '<div class="empty-state" style="padding:20px"><p class="empty-state-text">暂无前期策划文档</p><a href="/planning" class="btn btn-sm btn-outline">前往创建</a></div>';
            return;
        }
        const allChecked = plans.every(p => selectedPlanIds.includes(p.id));
        container.innerHTML = `
            <label class="ref-item select-all-row" style="display:flex;align-items:center;gap:8px;padding:6px 8px;cursor:pointer;border-radius:6px;margin-bottom:6px;font-size:12px;background:var(--accent-light);border:1px solid rgba(59,130,246,0.2);">
                <input type="checkbox" onchange="toggleAllPlans(this, ${JSON.stringify(plans.map(p=>p.id))})" ${allChecked ? 'checked' : ''}>
                <strong>📋 全选（共${plans.length}条）</strong>
            </label>
        ` + plans.map(p => `
            <label class="ref-item" style="display:flex;align-items:center;gap:8px;padding:8px;cursor:pointer;border-radius:6px;margin-bottom:4px;font-size:13px;">
                <input type="checkbox" class="plan-cb" value="${p.id}" onchange="togglePlanRef(${p.id})" ${selectedPlanIds.includes(p.id) ? 'checked' : ''}>
                <span>📋 ${escapeHtml(p.title)}</span>
            </label>
        `).join('');
    } catch (e) { console.error(e); }
}

async function loadKnowledgeRefs() {
    try {
        const cards = await apiGet('/api/knowledge/cards');
        const container = document.getElementById('knowledgeRefs');
        if (cards.length === 0) {
            container.innerHTML = '<div class="empty-state" style="padding:20px"><p class="empty-state-text">暂无知识库文档</p></div>';
            return;
        }
        const allChecked = cards.every(c => selectedKnowledgeIds.includes(c.id));
        container.innerHTML = `
            <label class="ref-item select-all-row" style="display:flex;align-items:center;gap:8px;padding:6px 8px;cursor:pointer;border-radius:6px;margin-bottom:6px;font-size:12px;background:var(--accent-light);border:1px solid rgba(59,130,246,0.2);">
                <input type="checkbox" onchange="toggleAllKnowledge(this, ${JSON.stringify(cards.map(c=>c.id))})" ${allChecked ? 'checked' : ''}>
                <strong>📚 全选（共${cards.length}条）</strong>
            </label>
        ` + cards.map(c => `
            <label class="ref-item" style="display:flex;align-items:center;gap:8px;padding:8px;cursor:pointer;border-radius:6px;margin-bottom:4px;font-size:13px;">
                <input type="checkbox" class="knowledge-cb" value="${c.id}" onchange="toggleKnowledgeRef(${c.id})" ${selectedKnowledgeIds.includes(c.id) ? 'checked' : ''}>
                <span>📚 ${escapeHtml(c.title)}</span>
                <span style="font-size:10px;color:var(--text-muted);">${escapeHtml(c.tags)}</span>
            </label>
        `).join('');
    } catch (e) { console.error(e); }
}

async function loadVideoRefs() {
    try {
        const videos = await apiGet('/api/videos');
        const container = document.getElementById('videoRefs');
        const analyzed = videos.filter(v => v.is_analyzed);
        if (analyzed.length === 0) {
            container.innerHTML = '<div class="empty-state" style="padding:20px"><p class="empty-state-text">暂无已分析的对标视频</p></div>';
            return;
        }
        const allChecked = analyzed.every(v => selectedVideoIds.includes(v.id));
        container.innerHTML = `
            <label class="ref-item select-all-row" style="display:flex;align-items:center;gap:8px;padding:6px 8px;cursor:pointer;border-radius:6px;margin-bottom:6px;font-size:12px;background:var(--accent-light);border:1px solid rgba(59,130,246,0.2);">
                <input type="checkbox" onchange="toggleAllVideos(this, ${JSON.stringify(analyzed.map(v=>v.id))})" ${allChecked ? 'checked' : ''}>
                <strong>🎬 全选（共${analyzed.length}条）</strong>
            </label>
        ` + analyzed.map(v => `
            <label class="ref-item" style="display:flex;align-items:center;gap:8px;padding:8px;cursor:pointer;border-radius:6px;margin-bottom:4px;font-size:13px;">
                <input type="checkbox" class="video-cb" value="${v.id}" onchange="toggleVideoRef(${v.id})" ${selectedVideoIds.includes(v.id) ? 'checked' : ''}>
                <span>🎬 ${escapeHtml(v.title)}</span>
                <span style="font-size:11px;color:var(--text-muted);margin-left:auto;">✅已分析</span>
            </label>
        `).join('');
    } catch (e) {
        console.error(e);
    }
}

function togglePlanRef(id) {
    const idx = selectedPlanIds.indexOf(id);
    if (idx >= 0) selectedPlanIds.splice(idx, 1);
    else selectedPlanIds.push(id);
}
function toggleKnowledgeRef(id) {
    const idx = selectedKnowledgeIds.indexOf(id);
    if (idx >= 0) selectedKnowledgeIds.splice(idx, 1);
    else selectedKnowledgeIds.push(id);
}
function toggleVideoRef(id) {
    const idx = selectedVideoIds.indexOf(id);
    if (idx >= 0) selectedVideoIds.splice(idx, 1);
    else selectedVideoIds.push(id);
}

// ===== 全选/取消全选 =====
function toggleAllPlans(cb, allIds) {
    if (cb.checked) {
        selectedPlanIds = [...new Set([...selectedPlanIds, ...allIds])];
    } else {
        selectedPlanIds = selectedPlanIds.filter(id => !allIds.includes(id));
    }
    document.querySelectorAll('.plan-cb').forEach(el => {
        el.checked = cb.checked;
    });
    loadPlanRefs(); // 重新渲染更新状态
}

function toggleAllKnowledge(cb, allIds) {
    if (cb.checked) {
        selectedKnowledgeIds = [...new Set([...selectedKnowledgeIds, ...allIds])];
    } else {
        selectedKnowledgeIds = selectedKnowledgeIds.filter(id => !allIds.includes(id));
    }
    document.querySelectorAll('.knowledge-cb').forEach(el => {
        el.checked = cb.checked;
    });
    loadKnowledgeRefs();
}

function toggleAllVideos(cb, allIds) {
    if (cb.checked) {
        selectedVideoIds = [...new Set([...selectedVideoIds, ...allIds])];
    } else {
        selectedVideoIds = selectedVideoIds.filter(id => !allIds.includes(id));
    }
    document.querySelectorAll('.video-cb').forEach(el => {
        el.checked = cb.checked;
    });
    loadVideoRefs();
}

// ===== 生成脚本 =====
async function startGenerate() {
    const title = document.getElementById('scriptTitle').value.trim();
    const requirement = document.getElementById('scriptRequirement').value.trim();
    const creativeRatio = parseInt(document.getElementById('creativeRatio').value);
    const apiKey = getApiKey();

    if (!title || !requirement) {
        showToast('请填写脚本标题和创作需求', 'error');
        return;
    }
    if (!apiKey) {
        showToast('请先在导航栏输入 DeepSeek API Key', 'error');
        return;
    }

    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="loading-spinner"></span> AI 生成中...';

    const resultArea = document.getElementById('resultArea');
    const resultContent = document.getElementById('resultContent');
    resultArea.style.display = 'block';
    resultContent.innerHTML = '<div style="text-align:center;padding:40px;"><span class="loading-spinner"></span><p style="margin-top:12px;color:var(--text-secondary);">正在调用 DeepSeek AI 生成脚本...</p></div>';

    const fastMode = document.getElementById('fastMode')?.checked || false;
    try {
        const data = await apiPost('/api/generate', {
            api_key: apiKey,
            title: title,
            requirement: requirement,
            creative_ratio: creativeRatio,
            plan_ids: selectedPlanIds,
            knowledge_ids: selectedKnowledgeIds,
            video_ids: selectedVideoIds,
            fast_mode: fastMode,
        });
        resultContent.innerHTML = mdToHtml(data.script.content);
        lastGeneratedScriptId = data.script.id;
        showToast('脚本生成成功！', 'success');
    } catch (e) {
        resultContent.innerHTML = `<p style="color:var(--danger);">生成失败：${escapeHtml(e.message)}</p>`;
        showToast('生成失败: ' + e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '✨ 开始生成脚本';
    }
}

function copyResult() {
    const content = document.getElementById('resultContent').innerText;
    navigator.clipboard.writeText(content).then(() => {
        showToast('已复制到剪贴板', 'success');
    }).catch(() => {
        showToast('复制失败，请手动选择复制', 'error');
    });
}

let lastGeneratedScriptId = null;

async function saveResult() {
    const title = document.getElementById('scriptTitle').value.trim();
    const content = document.getElementById('resultContent').innerText;
    try {
        const data = await apiPost('/api/scripts', { title, content });
        lastGeneratedScriptId = data.script.id;
        showToast('脚本已保存', 'success');
    } catch (e) {
        showToast('保存失败: ' + e.message, 'error');
    }
}

function downloadResult(format) {
    const id = lastGeneratedScriptId;
    if (!id) {
        // 如果没有保存，先保存再下载
        const title = document.getElementById('scriptTitle').value.trim();
        const content = document.getElementById('resultContent').innerText;
        if (!title || !content) {
            showToast('请先生成脚本', 'error');
            return;
        }
        apiPost('/api/scripts', { title, content }).then(data => {
            lastGeneratedScriptId = data.script.id;
            window.open(`/api/scripts/${data.script.id}/download.${format}`, '_blank');
        }).catch(e => showToast('保存失败: ' + e.message, 'error'));
    } else {
        window.open(`/api/scripts/${id}/download.${format}`, '_blank');
    }
}

// 页面加载时获取参考数据
document.addEventListener('DOMContentLoaded', () => {
    loadPlanRefs();
    loadKnowledgeRefs();
    loadVideoRefs();
});

// 监听标题输入变化
document.addEventListener('DOMContentLoaded', () => {
    const titleInput = document.getElementById('scriptTitle');
    const reqInput = document.getElementById('scriptRequirement');
    const hint = document.getElementById('generateHint');

    function checkInputs() {
        if (titleInput.value.trim() && reqInput.value.trim()) {
            hint.textContent = '✅ 信息已就绪，点击按钮开始生成';
            hint.style.color = 'var(--success)';
        } else {
            hint.textContent = '请填写 脚本标题 和 创作需求 后开始生成';
            hint.style.color = 'var(--text-muted)';
        }
    }
    titleInput.addEventListener('input', checkInputs);
    reqInput.addEventListener('input', checkInputs);
});
