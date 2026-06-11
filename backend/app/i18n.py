"""i18n translations for dashboard."""
TRANSLATIONS = {
    'zh': {
        'site_title': 'Sangwoo 管理后台', 'dashboard_title': '管理后台',
        'overview': '概览', 'analytics': '统计分析', 'modules': '模块开关',
        'health': '健康监控', 'backup': '备份恢复', 'uploads': '文件管理',
        'logout': '退出登录', 'login': '登录', 'username': '用户名', 'password': '密码',
        'total_products': '产品总数', 'product_count': '产品总数',
        'published_news': '已发布新闻', 'news_count': '新闻数量',
        'pending_reviews': '待审核咨询', 'submission_count': '待审咨询',
        'today_views': '今日访问',
        'recent_logs': '最近系统日志', 'time': '时间', 'level': '级别',
        'message': '消息', 'server_time': '服务器时间',
        'login_failed': '用户名或密码错误', 'submit': '提交',
        'no_products': '暂无产品', 'no_news': '暂无新闻',
        'no_submissions': '暂无咨询', 'no_logs': '暂无日志',
        'quick_actions': '快速操作', 'system_status': '系统状态',
        'pv_uv_chart': 'PV/UV 趋势 (近30天)', 'top_pages': '页面排行',
        'top_sources': '来源分布', 'page': '页面', 'source': '来源', 'count': '访问量',
        'cpu': 'CPU', 'memory': '内存', 'disk': '磁盘',
        'services': '服务状态', 'service_name': '服务', 'status': '状态',
        'details': '操作', 'running': '运行中', 'stopped': '未运行',
        'hostname': '主机名', 'platform': '平台', 'uptime': '运行时间', 'load_avg': '负载',
        'errors': '最近错误日志',
        'module_name': '功能模块', 'save': '保存设置', 'saved': '设置已保存',
        'manual_backup': '手动备份', 'run_backup': '立即备份', 'run_db_backup': '备份数据库',
        'backup_history': '备份历史', 'created_at': '时间', 'size': '大小',
        'auto_backup': '自动备份设置', 'daily_auto_backup': '每日自动备份',
        'backup_retention': '保留30天', 'download': '下载', 'restore': '恢复',
        'upload_files': '上传产品图片', 'product_slug': '产品 Slug',
        'select_files': '选择图片 (jpg/png/webp, 最大 5MB)', 'upload': '上传',
        'storage': '存储使用', 'total_storage': '总大小',
        'language': '语言', 'change_language': '切换语言',
        'system_info': '系统信息', 'toggle_modules': '功能模块开关',
        'about_company': '关于我们', 'contact': '联系方式', 'settings': '设置',
    },
    'en': {
        'site_title': 'Sangwoo Admin', 'dashboard_title': 'Dashboard',
        'overview': 'Overview', 'analytics': 'Analytics', 'modules': 'Modules',
        'health': 'Health', 'backup': 'Backup', 'uploads': 'Uploads',
        'logout': 'Logout', 'login': 'Login', 'username': 'Username', 'password': 'Password',
        'total_products': 'Total Products', 'product_count': 'Products',
        'published_news': 'Published News', 'news_count': 'News',
        'pending_reviews': 'Pending Reviews', 'submission_count': 'Submissions',
        'today_views': 'Today Views',
        'recent_logs': 'Recent Logs', 'time': 'Time', 'level': 'Level',
        'message': 'Message', 'server_time': 'Server Time',
        'login_failed': 'Invalid username or password', 'submit': 'Submit',
        'no_products': 'No products yet', 'no_news': 'No news yet',
        'no_submissions': 'No submissions yet', 'no_logs': 'No logs yet',
        'quick_actions': 'Quick Actions', 'system_status': 'System Status',
        'pv_uv_chart': 'PV/UV Trends (30 days)', 'top_pages': 'Top Pages',
        'top_sources': 'Top Sources', 'page': 'Page', 'source': 'Source', 'count': 'Views',
        'cpu': 'CPU', 'memory': 'Memory', 'disk': 'Disk',
        'services': 'Services', 'service_name': 'Service', 'status': 'Status',
        'details': 'Actions', 'running': 'Running', 'stopped': 'Stopped',
        'hostname': 'Hostname', 'platform': 'Platform', 'uptime': 'Uptime', 'load_avg': 'Load',
        'errors': 'Recent Errors',
        'module_name': 'Module Name', 'save': 'Save Settings', 'saved': 'Settings saved',
        'manual_backup': 'Manual Backup', 'run_backup': 'Run Backup', 'run_db_backup': 'Backup DB Only',
        'backup_history': 'Backup History', 'created_at': 'Created At', 'size': 'Size',
        'auto_backup': 'Auto Backup', 'daily_auto_backup': 'Daily Auto Backup',
        'backup_retention': 'Retain 30 days', 'download': 'Download', 'restore': 'Restore',
        'upload_files': 'Upload Product Images', 'product_slug': 'Product Slug',
        'select_files': 'Select Files (jpg/png/webp, max 5MB)', 'upload': 'Upload',
        'storage': 'Storage Usage', 'total_storage': 'Total Size',
        'language': 'Language', 'change_language': 'Switch Language',
        'system_info': 'System Info', 'toggle_modules': 'Toggle Modules',
        'about_company': 'About Us', 'contact': 'Contact', 'settings': 'Settings',
    },
}


def get_locale(request) -> str:
    """Get locale from cookie or accept-language header."""
    lang = request.cookies.get('lang', 'zh')
    if lang not in ('zh', 'en'):
        lang = 'zh'
    return lang


def t(key: str, locale: str = 'zh', **kwargs) -> str:
    """Translate a key to the given locale."""
    fallback = kwargs.get('default', key)
    if locale not in TRANSLATIONS:
        locale = 'zh'
    return TRANSLATIONS.get(locale, {}).get(key, fallback)
