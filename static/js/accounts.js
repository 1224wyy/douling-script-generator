/**
 * 对标视频页逻辑
 */

let currentVideoGroup = 'all';
let allVideos = [];

async function loadVideos() {
    try {
        allVideos = await apiGet('/api/videos');
        document.getElementById('allVideoCount').textContent = allVideos.length;
        const ungrouped = allVideos.filter(v => v.group_name === '全部视频').length;
        document.getElementById('ungroupedCount').textContent = ungrouped;
        renderVideos();
    } catch (e) {
        showToast('加载失败: ' + e.message, 'error');
    }
}

function filterVideos(group) {
    currentVideoGroup = group;
    renderVideos();
}

function renderVideos() {
    const videos = currentVideoGroup === 'all' ? allVideos : allVideos.filter(v => v.group_name === currentVideoGroup);
    const container = document.getElementById('videoList');
    if (videos.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🎬</div><p class="empty-state-text">暂无对标视频</p><p style="font-size:12px;color:var(--text-muted);">输入抖音链接开始解析，或手动输入视频内容</p></div>';
        return;
    }
    container.innerHTML = videos.map(v => `
        <div class="list-item">
            <div class="list-item-info">
                <div class="list-item-title">${v.title ? '🎬 ' + escapeHtml(v.title) : '🔗 ' + escapeHtml(v.url.substring(0, 50)) + '...'}</div>
                <div class="list-item-meta">
                    ${v.author ? '作者: ' + escapeHtml(v.author) + ' · ' : ''}
                    ${v.is_analyzed ? '<span class="tag tag-green">✅ 已分析</span>' : '<span class="tag tag-yellow">⏳ 未分析</span>'}
                    · ${formatDate(v.created_at)}
                </div>
            </div>
            <div class="list-item-actions">
                <button class="btn btn-sm btn-outline" onclick="viewVideoDetail(${v.id})">👁 查看</button>
                ${!v.is_analyzed ? `<button class="btn btn-sm btn-primary" onclick="analyzeVideoById(${v.id})">🔍 AI分析</button>` : ''}
                <button class="btn btn-sm btn-outline" onclick="changeVideoGroup(${v.id}, '${escapeHtml(v.group_name)}')">📁</button>
                <button class="btn btn-sm btn-danger" onclick="deleteVideo(${v.id})">🗑</button>
            </div>
        </div>
    `).join('');
}

// ===== 解析视频链接 =====
async function parseVideo() {
    const url = document.getElementById('videoUrlInput').value.trim();
    if (!url) {
        showToast('请输入视频链接', 'error');
        return;
    }
    if (!url.includes('douyin.com') && !url.includes('iesdouyin.com')) {
        showToast('请输入有效的抖音视频链接', 'error');
        return;
    }

    const inputEl = document.getElementById('videoUrlInput');
    const parseBtns = document.querySelectorAll('button[onclick="parseVideo()"]');
    parseBtns.forEach(b => { b.disabled = true; b.textContent = '⏳ 解析中...'; });

    try {
        const data = await apiPost('/api/videos/parse', { url });
        document.getElementById('videoUrlInput').value = '';
        loadVideos();

        if (data.parsed_detail) {
            const d = data.parsed_detail;
            let detailHtml = '';
            if (d.title) detailHtml += `<p><strong>📝 标题：</strong>${escapeHtml(d.title)}</p>`;
            if (d.author) detailHtml += `<p><strong>👤 作者：</strong>${escapeHtml(d.author)}</p>`;
            if (d.description && !d.description.startsWith('⚠️')) detailHtml += `<p><strong>📄 简介：</strong>${escapeHtml(d.description)}</p>`;
            if (d.tags && d.tags.length) detailHtml += `<p><strong>🏷 标签：</strong>${d.tags.map(t => `<span class="tag tag-pink">${escapeHtml(t)}</span>`).join(' ')}</p>`;
            if (d.music) detailHtml += `<p><strong>🎵 BGM：</strong>${escapeHtml(d.music)}</p>`;
            if (d.duration) detailHtml += `<p><strong>⏱ 时长：</strong>${escapeHtml(d.duration)}</p>`;

            const isPartial = d.parse_status === 'partial' || d.parse_status === 'needs_manual' || d.parse_status === 'failed';

            if (isPartial || !detailHtml) {
                detailHtml = (d.description || '<p style="color:var(--text-muted);">未能自动提取到视频详情（抖音有反爬机制）</p>') + `
                <div style="padding:14px;background:rgba(245,158,11,0.15);border:1px solid rgba(245,158,11,0.3);border-radius:8px;margin-top:12px;font-size:13px;">
                    ⚠️ <strong>自动解析不完整</strong><br>
                    抖音链接自动提取经常受风控限制。建议：<br>
                    1️⃣ 关闭此窗口<br>
                    2️⃣ 点击「✏️ 手动输入」按钮<br>
                    3️⃣ 粘贴视频的口播文案/字幕<br>
                    4️⃣ 然后点击「🔍 AI分析」进行深度分析
                </div>`;
            } else {
                detailHtml += `
                <div style="padding:12px;background:var(--accent-light);border-radius:8px;margin-top:12px;font-size:13px;">
                    💡 <strong>下一步：</strong>关闭窗口后，点击视频列表中的「🔍 AI分析」让AI分析此视频的爆款因素和可借鉴之处。
                </div>`;
            }

            showModal(isPartial ? '⚠️ 视频已保存（需手动补充内容）' : '✅ 视频解析成功', detailHtml, null, '好的');
        }
    } catch (e) {
        showToast('解析失败: ' + e.message, 'error');
    } finally {
        parseBtns.forEach(b => { b.disabled = false; b.textContent = '📥 解析链接'; });
    }
}

// ===== 手动输入视频信息 =====
function showManualInput() {
    showModal('✏️ 手动输入视频信息', `
        <div class="form-group">
            <label class="form-label">视频链接（选填）</label>
            <input type="text" id="manualVideoUrl" class="form-input" placeholder="粘贴抖音链接或留空">
        </div>
        <div class="form-group">
            <label class="form-label">视频标题 <span class="required">*</span></label>
            <input type="text" id="manualVideoTitle" class="form-input" placeholder="输入视频标题或主题">
        </div>
        <div class="form-group">
            <label class="form-label">作者/账号名</label>
            <input type="text" id="manualVideoAuthor" class="form-input" placeholder="视频创作者">
        </div>
        <div class="form-group">
            <label class="form-label">视频文案/内容（用于AI分析）</label>
            <textarea id="manualVideoContent" class="form-textarea" placeholder="粘贴视频的口播文案、字幕内容、或者你认为值得分析的内容...&#10;&#10;这些内容将作为AI分析的素材。"></textarea>
        </div>
    `, async (overlay) => {
        const url = overlay.querySelector('#manualVideoUrl').value.trim();
        const title = overlay.querySelector('#manualVideoTitle').value.trim();
        const author = overlay.querySelector('#manualVideoAuthor').value.trim();
        const content = overlay.querySelector('#manualVideoContent').value.trim();

        if (!title) { showToast('请输入视频标题', 'error'); throw new Error(); }

        const res = await fetch('/api/videos/manual', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url || '手动输入', title, author, parsed_content: content }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);

        overlay.remove();
        showToast('视频信息已保存', 'success');
        loadVideos();
    }, '保存');
}

// ===== 深度分析视频 =====
async function analyzeVideoById(videoId) {
    const apiKey = getApiKey();
    if (!apiKey) {
        showToast('请先设置 DeepSeek API Key', 'error');
        return;
    }
    try {
        showToast('正在调用 AI 分析视频...', 'info');
        const data = await apiPost('/api/videos/analyze', { api_key: apiKey, video_id: videoId });
        showToast('视频分析完成！', 'success');
        loadVideos();
        viewVideoDetail(videoId);
    } catch (e) {
        showToast('分析失败: ' + e.message, 'error');
    }
}

// ===== 查看视频详情（含编辑内容功能） =====
async function viewVideoDetail(id) {
    try {
        const video = await apiGet('/api/videos/' + id);

        let bodyHtml = '';
        bodyHtml += `<div style="margin-bottom:12px;font-size:13px;color:var(--text-secondary);">
            作者: ${escapeHtml(video.author)} · ${formatDate(video.created_at)}
            ${video.is_analyzed ? ' <span class="tag tag-green">✅ 已分析</span>' : ' <span class="tag tag-yellow">⏳ 未分析</span>'}
        </div>`;

        // 显示解析内容
        bodyHtml += `<div style="margin-bottom:16px;">
            <h4 style="font-size:14px;margin-bottom:8px;">📄 视频解析内容</h4>
            <div style="background:var(--bg-primary);padding:12px;border-radius:8px;font-size:13px;line-height:1.7;">${escapeHtml(video.parsed_content)}</div>
            <button class="btn btn-sm btn-outline" style="margin-top:8px;" onclick="editVideoContent(${video.id})">✏️ 编辑内容</button>
        </div>`;

        // 显示AI分析结果
        if (video.is_analyzed) {
            bodyHtml += `<div>
                <h4 style="font-size:14px;margin-bottom:8px;">🔍 AI 深度分析</h4>
                <div class="result-box" style="max-height:400px;">${mdToHtml(video.analysis)}</div>
            </div>`;
        } else {
            bodyHtml += `<div style="padding:16px;background:var(--accent-light);border-radius:8px;font-size:13px;text-align:center;">
                <p>此视频尚未进行AI分析</p>
                <button class="btn btn-primary" style="margin-top:8px;" onclick="closeModalAndAnalyze(${video.id})">🔍 开始 AI 分析</button>
            </div>`;
        }

        showModal(escapeHtml(video.title), bodyHtml, null, '关闭');
    } catch (e) {
        showToast('加载失败', 'error');
    }
}

// ===== 编辑视频内容 =====
async function editVideoContent(id) {
    try {
        const video = await apiGet('/api/videos/' + id);
        showModal('编辑视频内容', `
            <div class="form-group">
                <label class="form-label">视频标题</label>
                <input type="text" id="editVideoTitle" class="form-input" value="${escapeHtml(video.title)}">
            </div>
            <div class="form-group">
                <label class="form-label">作者</label>
                <input type="text" id="editVideoAuthor" class="form-input" value="${escapeHtml(video.author)}">
            </div>
            <div class="form-group">
                <label class="form-label">视频文案/内容（这些内容将作为AI分析的素材）</label>
                <textarea id="editVideoContent" class="form-textarea" style="min-height:200px;">${escapeHtml(video.parsed_content)}</textarea>
            </div>
        `, async (overlay) => {
            const title = overlay.querySelector('#editVideoTitle').value.trim();
            const author = overlay.querySelector('#editVideoAuthor').value.trim();
            const content = overlay.querySelector('#editVideoContent').value.trim();

            const res = await fetch('/api/videos/' + id, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, author, parsed_content: content }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error);

            overlay.remove();
            showToast('内容已更新', 'success');
            loadVideos();
            viewVideoDetail(id);
        }, '保存');
    } catch (e) {
        showToast('加载失败: ' + e.message, 'error');
    }
}

function closeModalAndAnalyze(id) {
    // 关闭当前弹窗
    document.querySelectorAll('.modal-overlay').forEach(o => o.remove());
    analyzeVideoById(id);
}

// ===== 分组和删除 =====
async function changeVideoGroup(id, currentName) {
    const newGroup = prompt('输入分组名称：', currentName || '');
    if (newGroup === null) return;
    try {
        await apiPut('/api/videos/' + id, { group_name: newGroup || '全部视频' });
        showToast('分组已更新', 'success');
        loadVideos();
    } catch (e) { showToast('更新失败', 'error'); }
}

async function deleteVideo(id) {
    if (confirm('确定删除此视频吗？')) {
        try {
            await apiDelete('/api/videos/' + id);
            showToast('已删除', 'success');
            loadVideos();
        } catch (e) { showToast('删除失败', 'error'); }
    }
}

function batchVideoOp() {
    showToast('批量操作功能开发中', 'info');
}

document.addEventListener('DOMContentLoaded', loadVideos);
