/**
 * 前期策划 - AI 聊天模式
 */

let chatHistory = [];
let currentPlanContent = '';
let currentPlanTitle = '';

// ===== 聊天功能 =====
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg) return;

    const apiKey = getApiKey();
    if (!apiKey) {
        showToast('请先设置 DeepSeek API Key', 'error');
        return;
    }

    // 添加用户消息
    appendMessage('user', msg);
    chatHistory.push({ role: 'user', content: msg });
    input.value = '';

    // 显示 AI 正在输入
    const loadingDiv = appendMessage('ai', '<span class="loading-spinner"></span> 思考中...', 'loading-msg');
    scrollToBottom();

    try {
        const response = await apiPost('/api/planning/chat', {
            api_key: apiKey,
            history: chatHistory,
        });

        // 移除加载提示
        loadingDiv.remove();

        // 添加 AI 回复
        appendMessage('ai', response.reply);
        chatHistory.push({ role: 'assistant', content: response.reply });

        // 更新右侧预览
        if (response.plan_summary) {
            currentPlanTitle = response.plan_title || '策划方案';
            currentPlanContent = response.plan_summary;
            updatePlanPreview();
        }
    } catch (e) {
        loadingDiv.remove();
        appendMessage('ai', '抱歉，发生错误：' + e.message, 'error-msg');
    }

    scrollToBottom();
}

function appendMessage(role, content, cssClass) {
    const container = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = `chat-msg ${role}${cssClass ? ' ' + cssClass : ''}`;
    const avatar = role === 'ai' ? '🤖' : '👤';
    div.innerHTML = `
        <div class="msg-avatar">${avatar}</div>
        <div class="msg-bubble">${mdToHtml(content)}</div>
    `;
    container.appendChild(div);
    return div;
}

function scrollToBottom() {
    const container = document.getElementById('chatMessages');
    setTimeout(() => { container.scrollTop = container.scrollHeight; }, 100);
}

function clearChat() {
    if (chatHistory.length > 0 && !confirm('确定开始新对话吗？当前对话将被清除。')) return;
    chatHistory = [];
    currentPlanContent = '';
    currentPlanTitle = '';
    document.getElementById('chatMessages').innerHTML = `
        <div class="chat-msg ai">
            <div class="msg-avatar">🤖</div>
            <div class="msg-bubble">
                你好！我是你的 AI 策划助手。<br><br>
                告诉我你想做什么类型的抖音账号？比如：<br>
                • 赛道（美妆/美食/知识/育儿...）<br>
                • 目标受众<br>
                • 有什么特别的想法或需求？<br><br>
                我会一步步帮你细化策划方案 💡
            </div>
        </div>`;
    document.getElementById('currentPlanCard').style.display = 'none';
}

// ===== 策划预览 =====
function updatePlanPreview() {
    document.getElementById('currentPlanTitle').textContent = '📋 ' + currentPlanTitle;
    document.getElementById('currentPlanContent').innerHTML = mdToHtml(currentPlanContent);
    document.getElementById('currentPlanCard').style.display = 'block';
}

async function saveCurrentPlan() {
    if (!currentPlanContent) {
        showToast('暂无策划内容可保存', 'error');
        return;
    }
    try {
        await apiPost('/api/plans', {
            title: currentPlanTitle,
            content: currentPlanContent,
            source_type: 'ai',
        });
        showToast('策划已保存！', 'success');
        refreshPlans();
    } catch (e) {
        showToast('保存失败: ' + e.message, 'error');
    }
}

// ===== 策划文档列表 =====
async function refreshPlans() {
    try {
        const plans = await apiGet('/api/plans');
        const container = document.getElementById('planList');
        if (plans.length === 0) {
            container.innerHTML = '<div class="empty-state" style="padding:20px;"><p class="empty-state-text">暂无策划文档</p></div>';
            return;
        }
        container.innerHTML = plans.map(p => `
            <div class="list-item">
                <div class="list-item-info">
                    <div class="list-item-title">📋 ${escapeHtml(p.title)}</div>
                    <div class="list-item-meta">${p.source_type === 'ai' ? '🤖 AI生成' : '📄 上传'} · ${formatDate(p.created_at)} · ${(p.content||'').length}字</div>
                </div>
                <div class="list-item-actions">
                    <button class="btn btn-sm btn-outline" onclick="loadPlanToChat(${p.id})">💬 加载到对话</button>
                    <button class="btn btn-sm btn-outline" onclick="viewPlan(${p.id})">👁</button>
                    <button class="btn btn-sm btn-danger" onclick="deletePlan(${p.id})">🗑</button>
                </div>
            </div>`).join('');
    } catch (e) {
        showToast('加载失败: ' + e.message, 'error');
    }
}

async function loadPlanToChat(id) {
    try {
        const plan = await apiGet('/api/plans/' + id);
        currentPlanTitle = plan.title;
        currentPlanContent = plan.content;
        updatePlanPreview();
        showToast('策划已加载到右侧预览', 'success');
    } catch (e) { showToast('加载失败', 'error'); }
}

async function viewPlan(id) {
    try {
        const plan = await apiGet('/api/plans/' + id);
        showModal(escapeHtml(plan.title), `<div class="result-box">${mdToHtml(plan.content)}</div>`, null, '关闭');
    } catch (e) { showToast('加载失败', 'error'); }
}

async function deletePlan(id) {
    if (confirm('确定删除？')) {
        try {
            await apiDelete('/api/plans/' + id);
            showToast('已删除', 'success');
            refreshPlans();
        } catch (e) { showToast('删除失败', 'error'); }
    }
}

// ===== 上传文档 =====
function uploadPlanDoc() { document.getElementById('planFileInput').click(); }
async function handlePlanUpload(input) {
    const file = input.files[0];
    if (!file) return;
    const form = new FormData(); form.append('file', file);
    try {
        const res = await fetch('/api/plans/upload', { method: 'POST', body: form });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        showToast('文档上传解析成功！', 'success');
        refreshPlans();
    } catch (e) { showToast('上传失败: ' + e.message, 'error'); }
    input.value = '';
}

document.addEventListener('DOMContentLoaded', refreshPlans);
