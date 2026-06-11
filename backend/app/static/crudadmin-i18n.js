/**
 * CRUDAdmin 中文本地化脚本
 * 通过覆盖默认文本实现界面翻译
 */

const translations = {
  zh: {
    // 导航菜单
    'Dashboard': '仪表板',
    'Products': '产品',
    'News': '新闻',
    'Site Settings': '网站设置',
    'Settings': '设置',
    'About Company': '关于我们',
    'Contact': '联系方式',
    'Visitor Submissions': '访客提交',
    'Submissions': '访客提交',
    'Analytics': '访问统计',
    'System Log': '系统日志',
    'Admin Sessions': '管理会话',

    // 通用按钮
    'Create': '创建',
    'Create New': '创建新记录',
    'Edit': '编辑',
    'Delete': '删除',
    'Save': '保存',
    'Cancel': '取消',
    'Search': '搜索',
    'Filter': '筛选',
    'Reset': '重置',
    'Submit': '提交',
    'Confirm': '确认',
    'Close': '关闭',
    'Back': '返回',
    'List': '列表',

    // 表格操作
    'Actions': '操作',
    'Action': '操作',
    'View': '查看',
    'No records found': '未找到记录',
    'No data available': '暂无数据',
    'Showing': '显示第',
    'to': '至',
    'of': '共',
    'entries': '条',
    'record': '条记录',
    'records': '条记录',
    'previous': '上一页',
    'next': '下一页',
    'Page': '页',

    // 表单字段
    'Name': '名称',
    'Description': '描述',
    'Status': '状态',
    'Created At': '创建时间',
    'Updated At': '更新时间',
    'Active': '启用',
    'Inactive': '禁用',
    'Published': '已发布',
    'Draft': '草稿',
    'Key': '键',
    'Value': '值',
    'Title': '标题',
    'Content': '内容',
    'Slug': '链接标识',
    'Price': '价格',
    'Category': '分类',

    // 消息提示
    'Are you sure?': '确定要执行此操作吗？',
    'Are you sure you want to delete this record?': '确定要删除此记录吗？',
    'Deleted successfully': '删除成功',
    'Saved successfully': '保存成功',
    'Created successfully': '创建成功',
    'Updated successfully': '更新成功',
    'Error': '错误',
    'Success': '成功',
    'Warning': '警告',
    'Failed to delete': '删除失败',
    'Failed to save': '保存失败',

    // 登录
    'Login': '登录',
    'Log In': '登录',
    'Username': '用户名',
    'Password': '密码',
    'Logout': '退出',
    'Sign in to your account': '请登录您的账户',
    'Sign In': '登录',
    'Invalid credentials': '用户名或密码错误',

    // 其他
    'ID': 'ID',
    'Yes': '是',
    'No': '否',
    'True': '是',
    'False': '否',
    'None': '无',
    'Select': '选择',
    'All': '全部',
  }
};

/**
 * 递归遍历 DOM 子树，翻译文本节点
 */
function translateNode(node, trans) {
  if (node.nodeType === Node.TEXT_NODE) {
    const text = node.textContent?.trim();
    if (text && trans[text]) {
      node.textContent = trans[text];
      return true;
    }
    return false;
  }

  if (node.nodeType === Node.ELEMENT_NODE) {
    // 跳过 script/style
    if (['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(node.tagName)) return false;
    // 如果有子节点被翻译了，返回 true
    let translated = false;
    node.childNodes.forEach(child => {
      if (translateNode(child, trans)) translated = true;
    });
    // 翻译 placeholder
    if (node.getAttribute && node.hasAttribute('placeholder')) {
      const ph = node.getAttribute('placeholder');
      if (trans[ph]) {
        node.setAttribute('placeholder', trans[ph]);
        translated = true;
      }
    }
    // 翻译 aria-label / title
    ['aria-label', 'title'].forEach(attr => {
      if (node.getAttribute && node.hasAttribute(attr)) {
        const val = node.getAttribute(attr);
        if (trans[val]) {
          node.setAttribute(attr, trans[val]);
          translated = true;
        }
      }
    });
    return translated;
  }
  return false;
}

/**
 * 安全地翻译页面内容（避免重复翻译）
 */
function applyTranslations(locale) {
  if (locale !== 'zh' || !translations.zh) return;

  const trans = translations.zh;

  // 翻译 placeholder (input, textarea, select)
  document.querySelectorAll('input[placeholder], textarea[placeholder]').forEach(el => {
    const ph = el.getAttribute('placeholder');
    if (trans[ph]) el.setAttribute('placeholder', trans[ph]);
  });

  // 翻译标签文字（只翻译纯净文本节点，避免部分翻译）
  document.querySelectorAll('th, td, button, label, .btn, a.nav-link, a.menu-item, summary, option, .sidebar-item, a.sidebar-link, .card-title, h1, h2, h3, h4, h5, .page-title, .breadcrumb-item, .form-label, .input-group-text, .table-header, .pagination span, .dropdown-item').forEach(el => {
    // 只处理只有一个文本子节点的元素
    if (el.childNodes.length === 1 && el.childNodes[0].nodeType === Node.TEXT_NODE) {
      const text = el.textContent?.trim();
      if (text && trans[text]) {
        el.textContent = trans[text];
      }
    }
  });

  // 翻译纯文本节点（无子元素的标签）
  document.querySelectorAll('legend, caption, figcaption').forEach(el => {
    const text = el.textContent?.trim();
    if (text && trans[text]) el.textContent = trans[text];
  });

  // 翻译 select option
  document.querySelectorAll('select option').forEach(el => {
    const text = el.textContent?.trim();
    if (text && trans[text]) el.textContent = trans[text];
  });

  // 翻译 input::placeholder via CSS attribute
  document.querySelectorAll('input, textarea').forEach(el => {
    if (el.dataset.translated) return;
    const ph = el.placeholder;
    if (trans[ph]) {
      el.setAttribute('placeholder', trans[ph]);
      el.dataset.translated = '1';
    }
  });
}

/**
 * 获取当前语言
 */
function getLang() {
  return document.cookie.match(/lang=(zh|en)/)?.[1] || 'zh';
}

/**
 * 添加语言切换按钮到 CRUDAdmin 页面
 */
function addLangSwitch() {
  const lang = getLang();
  const existing = document.getElementById('crudadmin-lang-switch');
  if (existing) return;

  const container = document.createElement('div');
  container.id = 'crudadmin-lang-switch';
  container.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;display:flex;gap:4px;';

  const currentPath = window.location.pathname + window.location.search;
  const enLink = document.createElement('a');
  enLink.href = `/admin/dashboard/lang?lang=en&redirect=${encodeURIComponent(currentPath)}`;
  enLink.className = lang === 'en' ? 'bg-blue-600 text-white px-3 py-1 rounded' : 'bg-gray-700 text-gray-300 px-3 py-1 rounded hover:bg-gray-600';
  enLink.textContent = 'EN';
  enLink.style.textDecoration = 'none';

  const zhLink = document.createElement('a');
  zhLink.href = `/admin/dashboard/lang?lang=zh&redirect=${encodeURIComponent(currentPath)}`;
  zhLink.className = lang === 'zh' ? 'bg-blue-600 text-white px-3 py-1 rounded' : 'bg-gray-700 text-gray-300 px-3 py-1 rounded hover:bg-gray-600';
  zhLink.textContent = '中文';
  zhLink.style.textDecoration = 'none';

  container.appendChild(enLink);
  container.appendChild(zhLink);
  document.body.appendChild(container);
}

/**
 * 初始化
 */
document.addEventListener('DOMContentLoaded', () => {
  const lang = getLang();
  applyTranslations(lang);
  addLangSwitch();

  // 监听 HTMX / fetch 后的 DOM 更新
  document.body.addEventListener('htmx:afterSwap', () => {
    applyTranslations(getLang());
    addLangSwitch();
  });

  // 轮询检测 DOM 变化（CRUDAdmin 可能用原生 fetch 替换内容）
  let lastHash = '';
  const observer = new MutationObserver(() => {
    // 只在 DOM 真正变化时翻译，避免无限循环
    const currentText = document.body.innerText.substring(0, 200);
    if (currentText !== lastHash) {
      lastHash = currentText;
      applyTranslations(getLang());
      addLangSwitch();
    }
  });
  observer.observe(document.body, { childList: true, subtree: true, characterData: true });
});
