/**
 * 全局应用逻辑
 * - API Key 管理
 * - Toast 提示
 * - 通用 HTTP 请求
 */

// ===== API Key 管理 =====
function getApiKey() {
    return localStorage.getItem('deepseek_api_key') || '';
}

function setApiKey(key) {
    localStorage.setItem('deepseek_api_key', key);
}

function initApiKey() {
    const input = document.getElementById('apiKeyInput');
    if (!input) return;
    input.value = getApiKey();
}

document.addEventListener('DOMContentLoaded', initApiKey);

// 全局监听 API Key 保存按钮
document.addEventListener('click', function (e) {
    if (e.target.id === 'saveApiKeyBtn' || e.target.closest('#saveApiKeyBtn')) {
        const input = document.getElementById('apiKeyInput');
        const key = input.value.trim();
        if (key) {
            setApiKey(key);
            showToast('API Key 已保存', 'success');
        } else {
            showToast('请输入 API Key', 'error');
        }
    }
});

// ===== Toast 提示 =====
let toastTimer = null;
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;

    clearTimeout(toastTimer);
    toast.textContent = message;
    toast.className = 'toast ' + type + ' show';
    toastTimer = setTimeout(() => {
        toast.className = 'toast';
    }, 2500);
}

// ===== HTTP 请求 =====
async function apiGet(url) {
    const res = await fetch(url);
    if (!res.ok) {
        const err = await res.json().catch(() => ({ error: '请求失败' }));
        throw new Error(err.error || '请求失败');
    }
    return res.json();
}

async function apiPost(url, data) {
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ error: '请求失败' }));
        throw new Error(err.error || '请求失败');
    }
    return res.json();
}

async function apiPut(url, data) {
    const res = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ error: '请求失败' }));
        throw new Error(err.error || '请求失败');
    }
    return res.json();
}

async function apiDelete(url) {
    const res = await fetch(url, { method: 'DELETE' });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ error: '请求失败' }));
        throw new Error(err.error || '请求失败');
    }
    return res.json();
}

// ===== 通用工具 =====
function formatDate(isoString) {
    if (!isoString) return '';
    const d = new Date(isoString);
    return d.toLocaleDateString('zh-CN', {
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit'
    });
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Markdown 转 HTML（支持表格、标题、列表、粗体等）
function mdToHtml(md) {
    if (!md) return '';

    let lines = md.split('\n');
    let html = '';
    let inTable = false;
    let inList = false;

    for (let i = 0; i < lines.length; i++) {
        let line = lines[i];

        // 表格处理
        if (line.includes('|') && line.trim().startsWith('|')) {
            let cells = line.split('|').filter(c => c.trim() !== '');
            let isHeader = cells.every(c => /^[-:\s]+$/.test(c.trim()));

            if (isHeader) continue; // skip separator row

            if (!inTable) {
                html += '<table class="md-table"><thead><tr>';
                cells.forEach(c => html += `<th>${c.trim()}</th>`);
                html += '</tr></thead><tbody>';
                inTable = true;
            } else {
                html += '<tr>';
                cells.forEach(c => html += `<td>${processInline(c.trim())}</td>`);
                html += '</tr>';
            }
            continue;
        } else if (inTable) {
            html += '</tbody></table>';
            inTable = false;
        }

        // 标题
        if (/^#### (.+)/.test(line)) {
            html += '<h4 class="md-h4">' + processInline(line.replace(/^#### /, '')) + '</h4>';
            continue;
        }
        if (/^### (.+)/.test(line)) {
            html += '<h3 class="md-h3">' + processInline(line.replace(/^### /, '')) + '</h3>';
            continue;
        }
        if (/^## (.+)/.test(line)) {
            html += '<h2 class="md-h2">' + processInline(line.replace(/^## /, '')) + '</h2>';
            continue;
        }
        if (/^# (.+)/.test(line)) {
            html += '<h1 class="md-h1">' + processInline(line.replace(/^# /, '')) + '</h1>';
            continue;
        }

        // 分割线
        if (/^---+$/.test(line.trim())) {
            html += '<hr class="md-hr">';
            continue;
        }

        // 列表
        let listMatch = line.match(/^(\s*)[-*]\s(.+)/);
        if (listMatch) {
            if (!inList) { html += '<ul class="md-ul">'; inList = true; }
            html += '<li>' + processInline(listMatch[2]) + '</li>';
            continue;
        } else if (inList) {
            html += '</ul>';
            inList = false;
        }

        // 数字列表
        let numMatch = line.match(/^(\d+)[.)]\s(.+)/);
        if (numMatch) {
            if (!inList) { html += '<ol class="md-ol">'; inList = true; }
            html += '<li>' + processInline(numMatch[2]) + '</li>';
            continue;
        } else if (inList && line.trim() === '') {
            html += (html.endsWith('</ul>') ? '' : (html.includes('<ol') ? '</ol>' : '</ul>'));
            inList = false;
        }

        // 空行
        if (line.trim() === '') {
            html += '<br>';
            continue;
        }

        // 普通段落
        html += '<p>' + processInline(line) + '</p>';
    }

    if (inTable) html += '</tbody></table>';
    if (inList) html += (html.includes('<ol') ? '</ol>' : '</ul>');

    return html;
}

function processInline(text) {
    if (!text) return '';
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code class="md-code">$1</code>');
}

// ===== 弹窗 =====
function showModal(title, content, onConfirm, confirmText = '确定') {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.innerHTML = `
        <div class="modal">
            <div class="modal-header">
                <h3 class="modal-title">${title}</h3>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">✕</button>
            </div>
            <div class="modal-body">${content}</div>
            <div class="modal-footer">
                <button class="btn btn-outline cancel-btn">取消</button>
                <button class="btn btn-primary confirm-btn">${confirmText}</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);

    overlay.querySelector('.cancel-btn').addEventListener('click', () => overlay.remove());
    overlay.querySelector('.confirm-btn').addEventListener('click', async () => {
        if (onConfirm) {
            try {
                await onConfirm(overlay);
            } catch (e) {
                // keep modal open on error
            }
        }
    });

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.remove();
    });
    return overlay;
}

// ===== 折叠面板 =====
document.addEventListener('click', function (e) {
    const header = e.target.closest('.collapsible-header');
    if (header) {
        const panel = header.closest('.collapsible');
        if (panel) panel.classList.toggle('open');
    }
});
