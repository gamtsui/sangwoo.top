export const locales = {
  zh: {
    name: '中文',
    native: '简体中文',
    nav: {
      home: '首页',
      products: '产品',
      news: '资讯',
      about: '关于',
      contact: '联系',
      compare: '对比',
      finder: '查找',
    },
    home: {
      hero_title: '韩国顶级食品，全球品味',
      hero_subtitle: 'Sangwoo 为您精选韩国 finest 的食材与美食',
      hero_cta: '探索产品',
      products_title: '精选产品',
      products_more: '查看全部产品',
      news_title: '最新资讯',
      news_more: '查看全部资讯',
      about_title: '关于我们',
      about_cta: '了解更多',
      contact_title: '联系我们',
      contact_cta: '发送消息',
    },
    products: {
      title: '我们的产品',
      no_products: '暂无产品',
      specifications: '规格参数',
      description: '产品描述',
      back: '返回列表',
      compare_title: '产品对比',
      compare_select: '选择产品对比',
      compare_add: '添加对比',
      compare_remove: '移除',
      compare_start: '开始对比',
      finder_title: '产品查找器',
      finder_search: '搜索产品...',
      finder_category: '类别',
      finder_price: '价格范围',
      finder_results: '搜索结果',
      finder_no_results: '未找到匹配的产品',
    },
    news: {
      title: '最新资讯',
      no_news: '暂无资讯',
      back: '返回列表',
      read_more: '阅读更多',
      published: '发布日期',
    },
    about: {
      title: '关于 Sangwoo',
      mission: '我们的使命',
      history: '发展历程',
    },
    contact: {
      title: '联系我们',
      name: '姓名',
      email: '邮箱',
      subject: '主题',
      message: '留言内容',
      send: '发送',
      sending: '发送中...',
      success: '发送成功！我们会尽快回复您。',
      error: '发送失败，请稍后重试。',
      address: '地址',
      phone: '电话',
    },
    footer: {
      rights: '版权所有',
      all_rights: '保留所有权利',
    },
  },
  en: {
    name: 'EN',
    native: 'English',
    nav: {
      home: 'Home',
      products: 'Products',
      news: 'News',
      about: 'About',
      contact: 'Contact',
      compare: 'Compare',
      finder: 'Finder',
    },
    home: {
      hero_title: 'Premium Korean Food, Global Taste',
      hero_subtitle: 'Sangwoo brings you the finest ingredients and cuisine from Korea',
      hero_cta: 'Explore Products',
      products_title: 'Featured Products',
      products_more: 'View All Products',
      news_title: 'Latest News',
      news_more: 'View All News',
      about_title: 'About Us',
      about_cta: 'Learn More',
      contact_title: 'Contact Us',
      contact_cta: 'Send Message',
    },
    products: {
      title: 'Our Products',
      no_products: 'No products available',
      specifications: 'Specifications',
      description: 'Description',
      back: 'Back to List',
      compare_title: 'Product Comparison',
      compare_select: 'Select Products to Compare',
      compare_add: 'Add to Compare',
      compare_remove: 'Remove',
      compare_start: 'Start Comparison',
      finder_title: 'Product Finder',
      finder_search: 'Search products...',
      finder_category: 'Category',
      finder_price: 'Price Range',
      finder_results: 'Search Results',
      finder_no_results: 'No matching products found',
    },
    news: {
      title: 'Latest News',
      no_news: 'No news available',
      back: 'Back to List',
      read_more: 'Read More',
      published: 'Published',
    },
    about: {
      title: 'About Sangwoo',
      mission: 'Our Mission',
      history: 'Our History',
    },
    contact: {
      title: 'Contact Us',
      name: 'Name',
      email: 'Email',
      subject: 'Subject',
      message: 'Message',
      send: 'Send',
      sending: 'Sending...',
      success: 'Sent successfully! We will get back to you soon.',
      error: 'Failed to send. Please try again later.',
      address: 'Address',
      phone: 'Phone',
    },
    footer: {
      rights: 'All Rights Reserved',
      all_rights: 'All Rights Reserved',
    },
  },
};

export function t(locale, path) {
  const keys = path.split('.');
  let result = locales[locale] || locales.zh;
  for (const key of keys) {
    if (result && typeof result === 'object') {
      result = result[key];
    } else {
      return path;
    }
  }
  return result || path;
}

export function getLocale(locale) {
  return locales[locale] || locales.zh;
}
