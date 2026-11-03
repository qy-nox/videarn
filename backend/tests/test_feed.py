from datetime import datetime, timezone, timedelta
from app.services.feed import FeedService
from app.models import VideoStats

def test_feed_score_decays_with_age():
    stats = VideoStats(views=10, likes=10, comments=2, shares=1)
    now = datetime.now(timezone.utc)
    assert FeedService.score(stats, now) > FeedService.score(stats, now - timedelta(days=30))

def test_feed_score_weights_engagement():
    now = datetime.now(timezone.utc)
    low = VideoStats(likes=1, comments=0, shares=0)
    high = VideoStats(likes=1, comments=1, shares=1)
    assert FeedService.score(high, now) > FeedService.score(low, now)
