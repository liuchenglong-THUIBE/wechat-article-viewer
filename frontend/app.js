// 微信公众号文章阅读器 - 前端逻辑

// 状态管理
let state = {
    currentTab: 'tab-feed',
    expandedArticleIdFeed: null,
    accountsNavLevel: 'list',
    currentAccountId: null,
    expandedArticleIdAccounts: null,
    currentMyTab: 'recent',
    expandedArticleIdMy: null,
    collectedArticles: JSON.parse(localStorage.getItem('collectedArticles') || '[]'),
    recentRead: JSON.parse(localStorage.getItem('recentRead') || '[]'),
    articles: [],
    accounts: []
};

// API 基础地址
const API_BASE = './api';

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadData();
    renderFeed();
    renderAccountList();
    renderMy();
});

// 从后端 API 加载数据
async function loadData() {
    try {
        console.log('正在加载数据...');
        const [articlesRes, accountsRes] = await Promise.all([
            fetch(`${API_BASE}/articles.json`),
            fetch(`${API_BASE}/accounts.json`)
        ]);

        if (articlesRes.ok) {
            state.articles = await articlesRes.json();
            console.log('Loaded articles:', state.articles.length);
        }
        if (accountsRes.ok) {
            state.accounts = await accountsRes.json();
            console.log('Loaded accounts:', state.accounts.length);
        }

        if (state.articles.length === 0) {
            console.log('使用示例数据');
            state.articles = getSampleArticles();
            state.accounts = getSampleAccounts();
        }

        renderFeed();
        renderAccountList();

    } catch (e) {
        console.error('加载数据失败:', e);
        state.articles = getSampleArticles();
        state.accounts = getSampleAccounts();
        renderFeed();
        renderAccountList();
    }
}

// 切换主 Tab
function switchTab(tabId) {
    document.querySelectorAll('.tab-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-page').forEach(el => el.classList.remove('active'));

    document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');
    state.currentTab = tabId;

    if (tabId === 'tab-my') {
        renderMy();
    }
}

// 文章 Tab
function renderFeed() {
    const container = document.getElementById('feed-list');
    let articles = [...state.articles];

    articles = articles.sort((a, b) => {
        return compareArticlesByPublishTimeDesc(a, b);
    });

    if (articles.length === 0) {
        container.innerHTML = '<div class="loading">暂无文章</div>';
        return;
    }

    container.innerHTML = articles.map(article => {
        const isCollected = state.collectedArticles.includes(article.id);
        const isExpanded = state.expandedArticleIdFeed === article.id;
        const title = article.article_title || article.title || '无标题';
        const accountName = article.account_name || article.accountName || '未知公众号';
        const publishTime = getArticlePublishTime(article);
        const summary = article.article_summary || article.summary || '';
        const url = article.article_link || article.url || '#';

        return `
            <div class="article-card ${isExpanded ? 'expanded' : 'collapsed'}" data-id="${article.id}">
                <div class="article-card-header" onclick="toggleExpandFeed(${article.id})">
                    <div class="article-card-title">${escapeHtml(title)}</div>
                    <div class="article-card-meta">
                        <span class="account-name">${escapeHtml(accountName)}</span>
                        <span>${formatDate(publishTime)}</span>
                    </div>
                </div>
                <div class="article-card-expanded ${isExpanded ? 'show' : ''}">
                    ${summary ? `<div class="article-summary">${escapeHtml(summary)}</div>` : ''}
                    <div class="article-card-actions">
                        <a href="${url}" target="_blank" class="btn primary" style="text-decoration: none;">
                            <span>🔗</span> 阅读原文
                        </a>
                        <button class="btn collect ${isCollected ? 'active' : ''}" onclick="event.stopPropagation(); toggleCollect(${article.id})">
                            <span>${isCollected ? '⭐' : '☆'}</span> ${isCollected ? '已收藏' : '收藏'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function toggleExpandFeed(articleId) {
    const article = state.articles.find(a => a.id === articleId);
    if (!article) return;

    if (state.expandedArticleIdFeed === articleId) {
        state.expandedArticleIdFeed = null;
    } else {
        state.recentRead = state.recentRead.filter(item => item.id !== articleId);
        state.recentRead.unshift({ id: articleId, lastRead: Date.now() });
        if (state.recentRead.length > 20) state.recentRead = state.recentRead.slice(0, 20);
        localStorage.setItem('recentRead', JSON.stringify(state.recentRead));

        state.expandedArticleIdFeed = articleId;
    }

    renderFeed();
}

// 公众号 Tab
function renderAccountList() {
    const container = document.getElementById('account-list');

    if (state.accounts.length === 0) {
        container.innerHTML = '<div class="loading">暂无公众号</div>';
        return;
    }

    container.innerHTML = state.accounts.map(account => {
        const name = account.account_name || account.name || '未知';
        const description = account.description || '';
        return `
            <div class="account-card" onclick="openAccountArticles('${escapeHtml(name)}')">
                <div class="account-avatar" style="background: ${getAvatarColor(name)}">
                    ${name.charAt(0)}
                </div>
                <div class="account-info">
                    <h3>${escapeHtml(name)}</h3>
                    <p>${escapeHtml(description)}</p>
                </div>
                <div class="account-article-count">${getArticleCount(name)} 篇</div>
            </div>
        `;
    }).join('');
}

function getArticleCount(accountName) {
    return state.articles.filter(a => {
        const articleAccount = a.account_name || a.accountName || '';
        return articleAccount === accountName;
    }).length;
}

function openAccountArticles(accountName) {
    state.currentAccountId = accountName;
    state.expandedArticleIdAccounts = null;
    state.accountsNavLevel = 'articles';

    document.getElementById('accounts-header').innerHTML = '<span onclick="backToAccountList()" style="cursor:pointer;">←</span> ' + escapeHtml(accountName);
    document.getElementById('account-list').style.display = 'none';
    document.getElementById('account-articles').style.display = 'block';

    renderAccountArticles(accountName);
}

function renderAccountArticles(accountName) {
    const container = document.getElementById('account-articles');
    let articles = state.articles.filter(a => {
        const articleAccount = a.account_name || a.accountName || '';
        return articleAccount === accountName;
    });
    articles = articles.sort((a, b) => {
        return compareArticlesByPublishTimeDesc(a, b);
    });

    if (articles.length === 0) {
        container.innerHTML = '<div class="loading">暂无文章</div>';
        return;
    }

    container.innerHTML = articles.map(article => {
        const isCollected = state.collectedArticles.includes(article.id);
        const isExpanded = state.expandedArticleIdAccounts === article.id;
        const title = article.article_title || article.title || '无标题';
        const accountName = article.account_name || article.accountName || '未知公众号';
        const publishTime = getArticlePublishTime(article);
        const summary = article.article_summary || article.summary || '';
        const url = article.article_link || article.url || '#';

        return `
            <div class="article-card ${isExpanded ? 'expanded' : 'collapsed'}" data-id="${article.id}">
                <div class="article-card-header" onclick="toggleExpandAccounts(${article.id})">
                    <div class="article-card-title">${escapeHtml(title)}</div>
                    <div class="article-card-meta">
                        <span class="account-name">${escapeHtml(accountName)}</span>
                        <span>${formatDate(publishTime)}</span>
                    </div>
                </div>
                <div class="article-card-expanded ${isExpanded ? 'show' : ''}">
                    ${summary ? `<div class="article-summary">${escapeHtml(summary)}</div>` : ''}
                    <div class="article-card-actions">
                        <a href="${url}" target="_blank" class="btn primary" style="text-decoration: none;">
                            <span>🔗</span> 阅读原文
                        </a>
                        <button class="btn collect ${isCollected ? 'active' : ''}" onclick="event.stopPropagation(); toggleCollect(${article.id})">
                            <span>${isCollected ? '⭐' : '☆'}</span> ${isCollected ? '已收藏' : '收藏'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function toggleExpandAccounts(articleId) {
    const article = state.articles.find(a => a.id === articleId);
    if (!article) return;

    if (state.expandedArticleIdAccounts === articleId) {
        state.expandedArticleIdAccounts = null;
    } else {
        state.recentRead = state.recentRead.filter(item => item.id !== articleId);
        state.recentRead.unshift({ id: articleId, lastRead: Date.now() });
        if (state.recentRead.length > 20) state.recentRead = state.recentRead.slice(0, 20);
        localStorage.setItem('recentRead', JSON.stringify(state.recentRead));

        state.expandedArticleIdAccounts = articleId;
    }

    renderAccountArticles(state.currentAccountId);
}

function backToAccountList() {
    if (state.accountsNavLevel === 'list') return;

    state.accountsNavLevel = 'list';
    state.currentAccountId = null;
    state.expandedArticleIdAccounts = null;

    document.getElementById('accounts-header').textContent = '公众号';
    document.getElementById('account-list').style.display = 'block';
    document.getElementById('account-articles').style.display = 'none';
}

// 我的 Tab
function switchMyTab(tab) {
    state.currentMyTab = tab;
    document.querySelectorAll('.my-inner-tab').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.my-inner-page').forEach(el => el.classList.remove('active'));

    document.querySelector(`.my-inner-tab[data-my-tab="${tab}"]`).classList.add('active');
    document.getElementById(`my-${tab}`).classList.add('active');
}

function renderMy() {
    const recentContainer = document.getElementById('recent-list');
    if (state.recentRead.length === 0) {
        recentContainer.innerHTML = '<div class="empty-tip">暂无阅读记录</div>';
    } else {
        recentContainer.innerHTML = state.recentRead.slice(0, 20).map(item => {
            const article = state.articles.find(a => a.id === item.id);
            if (!article) return '';
            return renderArticleCard(article, 'my');
        }).join('');
    }

    const collectContainer = document.getElementById('collect-list');
    if (state.collectedArticles.length === 0) {
        collectContainer.innerHTML = '<div class="empty-tip">暂无收藏</div>';
    } else {
        const collected = [...state.collectedArticles].reverse();
        collectContainer.innerHTML = collected.map(id => {
            const article = state.articles.find(a => a.id === id);
            if (!article) return '';
            return renderArticleCard(article, 'my');
        }).join('');
    }
}

function renderArticleCard(article, context) {
    const isCollected = state.collectedArticles.includes(article.id);
    const isExpanded = state.expandedArticleIdMy === article.id;
    const title = article.article_title || article.title || '无标题';
    const accountName = article.account_name || article.accountName || '未知公众号';
    const publishTime = getArticlePublishTime(article);
    const summary = article.article_summary || article.summary || '';
    const url = article.article_link || article.url || '#';

    return `
        <div class="article-card ${isExpanded ? 'expanded' : 'collapsed'}" data-id="${article.id}">
            <div class="article-card-header" onclick="toggleExpandMy(${article.id})">
                <div class="article-card-title">${escapeHtml(title)}</div>
                <div class="article-card-meta">
                    <span class="account-name">${escapeHtml(accountName)}</span>
                    <span>${formatDate(publishTime)}</span>
                </div>
            </div>
            <div class="article-card-expanded ${isExpanded ? 'show' : ''}">
                ${summary ? `<div class="article-summary">${escapeHtml(summary)}</div>` : ''}
                <div class="article-card-actions">
                    <a href="${url}" target="_blank" class="btn primary" style="text-decoration: none;">
                        <span>🔗</span> 阅读原文
                    </a>
                    <button class="btn collect ${isCollected ? 'active' : ''}" onclick="event.stopPropagation(); toggleCollect(${article.id})">
                        <span>${isCollected ? '⭐' : '☆'}</span> ${isCollected ? '已收藏' : '收藏'}
                    </button>
                </div>
            </div>
        </div>
    `;
}

function toggleExpandMy(articleId) {
    const article = state.articles.find(a => a.id === articleId);
    if (!article) return;

    if (state.expandedArticleIdMy === articleId) {
        state.expandedArticleIdMy = null;
    } else {
        state.recentRead = state.recentRead.filter(item => item.id !== articleId);
        state.recentRead.unshift({ id: articleId, lastRead: Date.now() });
        if (state.recentRead.length > 20) state.recentRead = state.recentRead.slice(0, 20);
        localStorage.setItem('recentRead', JSON.stringify(state.recentRead));

        state.expandedArticleIdMy = articleId;
    }

    renderMy();
}

function toggleCollect(articleId) {
    if (state.collectedArticles.includes(articleId)) {
        state.collectedArticles = state.collectedArticles.filter(id => id !== articleId);
    } else {
        state.collectedArticles.push(articleId);
    }
    localStorage.setItem('collectedArticles', JSON.stringify(state.collectedArticles));

    if (state.currentTab === 'tab-feed') {
        renderFeed();
    } else if (state.currentTab === 'tab-accounts' && state.accountsNavLevel === 'articles') {
        renderAccountArticles(state.currentAccountId);
    } else if (state.currentTab === 'tab-my') {
        renderMy();
    }
}

// 工具函数
function getArticlePublishTime(article) {
    return article.publish_time || article.publishTime || '';
}

function compareArticlesByPublishTimeDesc(a, b) {
    const timeA = getArticlePublishTime(a);
    const timeB = getArticlePublishTime(b);
    const timestampA = Date.parse(timeA);
    const timestampB = Date.parse(timeB);

    if (Number.isNaN(timestampA) && Number.isNaN(timestampB)) {
        return String(timeB).localeCompare(String(timeA));
    }
    if (Number.isNaN(timestampA)) return 1;
    if (Number.isNaN(timestampB)) return -1;
    return timestampB - timestampA;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateInput) {
    if (!dateInput) return '';
    try {
        const date = new Date(dateInput);
        return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
    } catch (e) {
        return String(dateInput).slice(0, 10);
    }
}

function getAvatarColor(name) {
    const colors = [
        '#4f46e5', '#0891b2', '#059669', '#d97706', '#c026d3',
        '#be185d', '#ef4444', '#7c3aed', '#0ea5e9', '#10b981'
    ];
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
}

function getSampleArticles() {
    return [
        {
            id: 1,
            article_title: '欢迎使用公众号文章阅读器',
            article_summary: '这是一个用来在线阅读收藏微信公众号文章的前端项目。',
            publish_time: new Date().toISOString(),
            account_id: 1,
            account_name: '示例公众号',
            article_link: 'https://github.com'
        },
        {
            id: 2,
            article_title: '如何配置自己的文章数据',
            article_summary: '通过导出脚本可以从数据库导出文章和公众号列表 JSON 文件。',
            publish_time: new Date(Date.now() - 86400000).toISOString(),
            account_id: 1,
            account_name: '示例公众号',
            article_link: 'https://github.com'
        }
    ];
}

function getSampleAccounts() {
    return [
        {
            id: 1,
            account_name: '示例公众号',
            description: '这是一个示例公众号'
        }
    ];
}
