#!/usr/bin/env python3
"""Seed script for Sangwoo.top - populates initial content into the database."""
from datetime import datetime
from app.database import init_db, SessionLocal
from app.models import Products, News, AboutCompany, Contact, SiteSettings

PRODUCTS = [
    {
        "name_zh": "正官庄高丽参提取物",
        "name_en": "CheongKwanJang Red Ginseng Extract",
        "description_zh": "韩国正官庄品牌高丽参提取物，富含人参皂苷Rg1、Rb1等活性成分。精选六年根高丽参，采用现代化提取工艺，保留天然营养成分。适合提高免疫力、改善体质的日常保健。",
        "description_en": "Premium CheongKwanJang Red Ginseng extract rich in ginsenosides Rg1 and Rb1. Made from select 6-year-old Korean ginseng roots using modern extraction technology. Ideal for immune support and overall vitality.",
        "specifications": {"origin": "韩国济州岛", "net_weight": "100g", "shelf_life": "36个月", "storage": "阴凉干燥处保存", "ingredients": "高丽参提取物粉"},
        "images": ["/uploads/products/ginseng_01.jpg"],
        "slug": "cheongkwanjang-ginseng-extract",
        "price": "¥688",
        "is_active": True,
        "created_at": datetime(2026, 6, 11),
        "updated_at": datetime(2026, 6, 11),
    },
    {
        "name_zh": "初乳素奶粉",
        "name_en": "Colostrum Milk Powder",
        "description_zh": "精选新西兰优质初乳原料，富含免疫球蛋白、乳铁蛋白和生长因子。适合婴幼儿及需要增强免疫力的成年人。天然乳源，无添加人工色素和防腐剂。",
        "description_en": "Premium colostrum milk powder sourced from New Zealand, rich in immunoglobulins, lactoferrin, and growth factors. Suitable for infants and adults seeking immune support. Natural source with no artificial colors or preservatives.",
        "specifications": {"origin": "新西兰", "net_weight": "900g", "shelf_life": "24个月", "storage": "25°C以下保存", "ingredients": "初乳粉、脱脂奶粉"},
        "images": ["/uploads/products/colostrum_01.jpg"],
        "slug": "colostrum-milk-powder",
        "price": "¥458",
        "is_active": True,
        "created_at": datetime(2026, 6, 11),
        "updated_at": datetime(2026, 6, 11),
    },
    {
        "name_zh": "韩国传统韩方蜂蜜茶",
        "name_en": "Traditional Korean Honey Tea",
        "description_zh": "采用韩国传统韩方配方，精选野生蜂蜜搭配柠檬和柚子。天然润喉，缓解季节性不适。无添加蔗糖，蜂蜜含量超过60%。",
        "description_en": "Traditional Korean herbal honey blend with wild honey, lemon, and yuzu. Natural throat soothing relief for seasonal discomfort. No added sugar with over 60% honey content.",
        "specifications": {"origin": "韩国", "net_weight": "500g", "shelf_life": "18个月", "storage": "冷藏最佳", "ingredients": "野生蜂蜜、柠檬、柚子"},
        "images": ["/uploads/products/honey-tea_01.jpg"],
        "slug": "korean-honey-tea",
        "price": "¥168",
        "is_active": True,
        "created_at": datetime(2026, 6, 11),
        "updated_at": datetime(2026, 6, 11),
    },
    {
        "name_zh": "韩式发酵泡菜（辣白菜）",
        "name_en": "Traditional Korean Kimchi",
        "description_zh": "韩国传统发酵泡菜，选用新鲜大白菜、辣椒粉、大蒜、生姜等天然原料。经过30天自然发酵，富含益生菌和乳酸菌。韩国国家级非遗发酵工艺。",
        "description_en": "Traditionally fermented Korean kimchi made with fresh napa cabbage, gochugaru (chili flakes), garlic, and ginger. Naturally fermented for 30 days, rich in probiotics and lactic acid bacteria. A Korean National Intangible Cultural Heritage.",
        "specifications": {"origin": "韩国", "net_weight": "1kg", "shelf_life": "12个月", "storage": "0-4°C冷藏", "ingredients": "大白菜、辣椒粉、大蒜、生姜、鱼露、糯米粉"},
        "images": ["/uploads/products/kimchi_01.jpg"],
        "slug": "traditional-kimchi",
        "price": "¥88",
        "is_active": True,
        "created_at": datetime(2026, 6, 11),
        "updated_at": datetime(2026, 6, 11),
    },
    {
        "name_zh": "韩国天然海藻提取物",
        "name_en": "Korean Natural Seaweed Extract",
        "description_zh": "采集韩国西海岸天然海藻，低温萃取保留碘、钙、铁等矿物质和膳食纤维。适合日常补充微量元素，促进新陈代谢。",
        "description_en": "Harvested from the natural seaweed of the Korean west coast, cold-extracted to preserve iodine, calcium, iron, and dietary fiber. Ideal for daily mineral supplementation and metabolism support.",
        "specifications": {"origin": "韩国西海岸", "net_weight": "200g", "shelf_life": "24个月", "storage": "阴凉干燥处", "ingredients": "海藻提取物粉"},
        "images": ["/uploads/products/seaweed_01.jpg"],
        "slug": "korean-seaweed-extract",
        "price": "¥258",
        "is_active": True,
        "created_at": datetime(2026, 6, 11),
        "updated_at": datetime(2026, 6, 11),
    },
    {
        "name_zh": "韩式传统芝麻油",
        "name_en": "Traditional Korean Sesame Oil",
        "description_zh": "韩国传统冷榨芝麻油，选用优质黑芝麻低温研磨。富含不饱和脂肪酸、维生素E和芝麻素。适合凉拌、蘸酱和烹饪调味。",
        "description_en": "Traditional cold-pressed Korean sesame oil from premium black sesame seeds. Rich in unsaturated fatty acids, vitamin E, and sesamin. Perfect for salads, dipping sauces, and cooking.",
        "specifications": {"origin": "韩国", "net_weight": "500ml", "shelf_life": "18个月", "storage": "避光保存", "ingredients": "黑芝麻油100%"},
        "images": ["/uploads/products/sesame-oil_01.jpg"],
        "slug": "korean-sesame-oil",
        "price": "¥128",
        "is_active": True,
        "created_at": datetime(2026, 6, 11),
        "updated_at": datetime(2026, 6, 11),
    },
]

NEWS = [
    {
        "title_zh": "杉宇国际贸易正式开业，打造韩国食品进口新标杆",
        "title_en": "Sangwoo Trading Officially Opens, Setting New Standards for Korean Food Imports",
        "content_zh": "杉宇国际贸易有限公司于2026年6月正式成立，致力于将韩国优质食品和健康产品引入中国市场。公司总部位于上海，与韩国多家知名食品生产企业建立了长期合作关系。\n\n我们专注于三个核心品类：韩方保健品、传统发酵食品、天然调味品。所有产品均通过严格的质检流程，确保符合中国食品安全标准。\n\n杉宇国际的愿景是让每一位中国消费者都能品尝到正宗的韩国风味，感受韩国食品文化的独特魅力。",
        "content_en": "Sangwoo International Trading was officially established in June 2026, dedicated to bringing premium Korean food and health products to the Chinese market. Headquartered in Shanghai, the company has established long-term partnerships with leading Korean food manufacturers.\n\nWe focus on three core categories: Korean herbal health supplements, traditional fermented foods, and natural seasonings. All products undergo strict quality inspection processes to ensure compliance with Chinese food safety standards.\n\nSangwoo International's vision is to let every Chinese consumer taste authentic Korean flavors and experience the unique charm of Korean food culture.",
        "slug": "sangwoo-official-opening",
        "status": "published",
        "source": "manual",
        "created_at": datetime(2026, 6, 11),
        "published_at": datetime(2026, 6, 11),
    },
    {
        "title_zh": "韩国食品进口市场持续增长，2026年有望突破新高",
        "title_en": "Korean Food Import Market Continues Growth, Expected to Reach New Highs in 2026",
        "content_zh": "据韩国贸易协会最新数据，韩国食品出口在2025年达到创纪录的120亿美元，同比增长15%。中国市场占据韩国食品出口总额的28%，是最主要的海外市场。\n\n增长的主要驱动力来自韩国保健品和功能性食品的受欢迎程度。正官庄高丽参、韩国蜂蜜茶等传统健康产品在中国消费者中的知名度显著提升。\n\n行业分析师预计，随着中韩自由贸易协定的深入和消费者对健康食品需求的增加，韩国食品在中国市场的年增长率将保持在10-15%。",
        "content_en": "According to the latest data from the Korea Trade Association, Korean food exports reached a record $12 billion in 2025, up 15% year-over-year. The Chinese market accounts for 28% of total Korean food exports, making it the largest overseas market.\n\nThe main growth drivers come from the popularity of Korean health supplements and functional foods. Traditional health products like CheongKwanJang ginseng and Korean honey tea have seen significantly increased awareness among Chinese consumers.\n\nIndustry analysts expect that with the deepening of the China-Korea Free Trade Agreement and growing consumer demand for healthy foods, the annual growth rate of Korean food in the Chinese market will remain at 10-15%.",
        "slug": "korean-food-import-market-2026",
        "status": "published",
        "source": "manual",
        "created_at": datetime(2026, 6, 10),
        "published_at": datetime(2026, 6, 10),
    },
    {
        "title_zh": "韩方保健品的科学依据：人参皂苷的健康功效",
        "title_en": "Scientific Basis of Korean Herbal Supplements: Health Benefits of Ginsenosides",
        "content_zh": "近年来，人参皂苷的健康功效成为国际医学研究热点。多项临床研究证实，人参皂苷Rg1和Rb1具有抗氧化、抗炎和免疫调节作用。\n\n韩国医科大学2025年发表的研究显示，每日摄入200mg高丽参提取物持续12周可显著提高健康成年人的细胞免疫功能。该研究还发现，人参皂苷对改善认知功能和减少疲劳感有积极影响。\n\n杉宇国际贸易与韩国多家研究机构合作，确保所进口产品含有经过验证的有效成分含量。",
        "content_en": "In recent years, the health benefits of ginsenosides have become a hotspot in international medical research. Multiple clinical studies have confirmed that ginsenosides Rg1 and Rb1 have antioxidant, anti-inflammatory, and immunomodulatory effects.\n\nA 2025 study published by a Korean medical university showed that daily intake of 200mg red ginseng extract for 12 weeks significantly improved cellular immune function in healthy adults. The study also found positive effects on cognitive function and fatigue reduction.\n\nSangwoo International partners with multiple Korean research institutions to ensure imported products contain verified levels of active ingredients.",
        "slug": "science-behind-ginsenosides",
        "status": "published",
        "source": "manual",
        "created_at": datetime(2026, 6, 8),
        "published_at": datetime(2026, 6, 8),
    },
]

def seed():
    print("=== Sangwoo.top Database Seed ===")
    init_db()
    db = SessionLocal()
    try:
        # Products
        count = db.query(Products).count()
        if count == 0:
            for p in PRODUCTS:
                db.add(Products(**p))
            print(f"  Inserted {len(PRODUCTS)} products.")
        else:
            print(f"  Products already has {count} rows, skipping.")

        # News
        count = db.query(News).count()
        if count == 0:
            for n in NEWS:
                db.add(News(**n))
            print(f"  Inserted {len(NEWS)} news articles.")
        else:
            print(f"  News already has {count} rows, skipping.")

        # About
        count = db.query(AboutCompany).count()
        if count == 0:
            db.add(AboutCompany(
                content_zh="杉宇国际贸易有限公司成立于2026年，总部位于上海。我们专注于韩国优质食品和健康产品的进口业务，致力于将韩国传统与现代食品文化带给中国消费者。\n\n公司拥有专业的采购团队，与韩国正官庄、传统发酵食品工坊等知名生产商建立了稳定的合作关系。我们严格执行韩国原产地认证和中国进口食品检验标准，确保每一款产品都是品质保证。\n\n杉宇国际的使命是搭建中韩食品文化的桥梁，让中国消费者享受到正宗、安全、优质的韩国食品。",
                content_en="Sangwoo International Trading was established in 2026 and is headquartered in Shanghai. We specialize in importing premium Korean food and health products, dedicated to bringing Korean traditional and modern food culture to Chinese consumers.\n\nOur professional procurement team has established stable partnerships with renowned Korean producers such as CheongKwanJang and traditional fermented food workshops. We strictly enforce Korean origin certification and Chinese import food inspection standards to ensure quality assurance for every product.\n\nSangwoo International's mission is to build a bridge between Chinese and Korean food cultures, allowing Chinese consumers to enjoy authentic, safe, and premium Korean food.",
                updated_at=datetime(2026, 6, 11),
            ))
            print("  Inserted about company info.")
        else:
            print("  About already has data, skipping.")

        # Contact
        count = db.query(Contact).count()
        if count == 0:
            db.add(Contact(
                email="contact@sangwoo.top",
                phone="+86-21-5888-8888",
                address_zh="中国上海市浦东新区陆家嘴金融中心88号 18楼",
                address_en="18F, No.88 Lujiazui Financial Center, Pudong New Area, Shanghai, China",
                social_media={"weixin": "SangwooShanghai", "weibo": "@杉宇国际贸易"},
                form_enabled=True,
                updated_at=datetime(2026, 6, 11),
            ))
            print("  Inserted contact info.")
        else:
            print("  Contact already has data, skipping.")

        db.commit()
        print("=== Seed complete ===")
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
