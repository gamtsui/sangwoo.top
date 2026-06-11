"""
访问统计 - 前端埋点 API + 聚合查询
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Request, Response, Cookie
from fastapi.responses import JSONResponse
from sqlalchemy import func

from .database import init_db, get_session
from .models import Analytics, SystemLog

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/analytics.js")
async def analytics_script():
    """Return the analytics tracking JavaScript snippet."""
    return Response(
        content=_ANALYTICS_JS,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=86400",  # 1 day cache
        },
    )


@router.post("/api/analytics/track")
async def track_event(request: Request):
    """Receive analytics tracking event from frontend."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    init_db()
    session = next(get_session())
    try:
        cookie_id = data.get("cookie_id") or str(uuid.uuid4())[:16]
        analytics = Analytics(
            date=datetime.now(),
            page=data.get("page", ""),
            source=data.get("source", "direct"),
            user_agent=data.get("user_agent", "")[:500],
            cookie_id=cookie_id,
        )
        session.add(analytics)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Analytics track error: {e}")
    finally:
        session.close()

    return JSONResponse(content={"ok": True})


@router.get("/api/analytics/stats")
async def get_stats(days: int = 30):
    """Get aggregated analytics stats for the dashboard."""
    init_db()
    session = next(get_session())
    try:
        cutoff = datetime.now() - timedelta(days=days)

        # Total pageviews
        total_pv = session.query(func.count(Analytics.id)).filter(
            Analytics.date >= cutoff
        ).scalar() or 0

        # Unique visitors (by cookie_id)
        total_uv = session.query(
            func.count(func.distinct(Analytics.cookie_id))
        ).filter(Analytics.date >= cutoff).scalar() or 0

        # Top pages
        top_pages = (
            session.query(Analytics.page, func.count(Analytics.id).label("views"))
            .filter(Analytics.date >= cutoff)
            .group_by(Analytics.page)
            .order_by(func.count(Analytics.id).desc())
            .limit(10)
            .all()
        )

        # Top sources
        top_sources = (
            session.query(Analytics.source, func.count(Analytics.id).label("views"))
            .filter(Analytics.date >= cutoff)
            .group_by(Analytics.source)
            .order_by(func.count(Analytics.id).desc())
            .limit(10)
            .all()
        )

        # Daily PV
        daily = (
            session.query(
                Analytics.date.cast(str).label("day"),
                func.count(Analytics.id).label("pv"),
            )
            .filter(Analytics.date >= cutoff)
            .group_by(Analytics.date.cast(str))
            .order_by(Analytics.date.asc())
            .all()
        )

        return {
            "total_pv": total_pv,
            "total_uv": total_uv,
            "days": days,
            "top_pages": [{"page": p.page, "views": p.views} for p in top_pages],
            "top_sources": [{"source": s.source, "views": s.views} for s in top_sources],
            "daily": [{"day": d.day[:10], "pv": d.pv} for d in daily],
        }
    except Exception as e:
        logger.error(f"Analytics stats error: {e}")
        return {"error": str(e)}
    finally:
        session.close()


# ============ Frontend Analytics JS ============
_ANALYTICS_JS = """
(function() {
    'use strict';
    
    // Generate or retrieve cookie ID (7-day TTL)
    function getCookie(name) {
        var match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        return match ? match[2] : null;
    }
    
    function setCookie(name, value, days) {
        var expires = new Date(Date.now() + days * 864e5).toUTCString();
        document.cookie = name + '=' + value + '; expires=' + expires + '; path=/; SameSite=Lax';
    }
    
    var cookieId = getCookie('_sa_id');
    if (!cookieId) {
        cookieId = 'xxxxxxxxxxxxxxxx'.replace(/[x]/g, function() {
            return (Math.random() * 16 | 0).toString(16);
        });
        setCookie('_sa_id', cookieId, 7);
    }
    
    // Determine referrer source
    function getSource() {
        var ref = document.referrer || '';
        if (!ref || ref.includes(window.location.hostname)) return 'direct';
        if (ref.includes('google')) return 'google';
        if (ref.includes('bing')) return 'bing';
        if (ref.includes('naver')) return 'naver';
        if (ref.includes('yahoo')) return 'yahoo';
        if (ref.includes('facebook') || ref.includes('twitter') || ref.includes('instagram')) return 'social';
        return 'referral';
    }
    
    // Send tracking event
    function track() {
        var data = {
            cookie_id: cookieId,
            page: window.location.pathname + window.location.search,
            source: getSource(),
            user_agent: navigator.userAgent
        };
        
        // Use Beacon API for reliable delivery
        if (navigator.sendBeacon) {
            navigator.sendBeacon('/api/analytics/track', JSON.stringify(data));
        } else {
            // Fallback: image pixel
            var img = new Image(1, 1);
            img.src = '/api/analytics/track?' + encodeURIComponent(JSON.stringify(data));
        }
    }
    
    // Track page load
    track();
    
    // Track SPA navigation (if using history API)
    var origPushState = history.pushState;
    history.pushState = function() {
        origPushState.apply(this, arguments);
        track();
    };
    
    // Track on visibility change (tab switch)
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) track();
    });
    
    // Track before unload (delayed for beacon)
    window.addEventListener('beforeunload', track);
})();
"""
