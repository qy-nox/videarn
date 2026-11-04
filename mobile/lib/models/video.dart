class VideoStats {
  const VideoStats({
    required this.views,
    required this.likes,
    required this.comments,
    required this.shares,
  });
  final int views;
  final int likes;
  final int comments;
  final int shares;
  factory VideoStats.fromJson(Map<String, dynamic> json) => VideoStats(
        views: (json['views'] as num?)?.toInt() ?? 0,
        likes: (json['likes'] as num?)?.toInt() ?? 0,
        comments: (json['comments'] as num?)?.toInt() ?? 0,
        shares: (json['shares'] as num?)?.toInt() ?? 0,
      );
}

class Video {
  const Video({
    required this.id,
    required this.creatorId,
    required this.caption,
    required this.status,
    required this.durationSeconds,
    required this.thumbnailUrl,
    required this.createdAt,
    required this.stats,
  });
  final String id;
  final String creatorId;
  final String? caption;
  final String status;
  final int durationSeconds;
  final String? thumbnailUrl;
  final DateTime createdAt;
  final VideoStats stats;
  factory Video.fromJson(Map<String, dynamic> json) => Video(
        id: json['id'] as String,
        creatorId: json['creator_id'] as String,
        caption: json['caption'] as String?,
        status: json['status'] as String? ?? 'published',
        durationSeconds: (json['duration_seconds'] as num?)?.toInt() ?? 0,
        thumbnailUrl: json['thumbnail_url'] as String?,
        createdAt: DateTime.tryParse(json['created_at'] as String? ?? '') ??
            DateTime.now(),
        stats: VideoStats.fromJson(
            (json['stats'] as Map?)?.cast<String, dynamic>() ?? const {}),
      );
}
