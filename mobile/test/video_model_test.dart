import 'package:flutter_test/flutter_test.dart';
import 'package:clipearn_mobile/models/video.dart';

void main() {
  test('parses a feed video payload', () {
    final video = Video.fromJson({
      'id': 'v1',
      'creator_id': 'u1',
      'caption': 'Hello',
      'status': 'published',
      'duration_seconds': 30,
      'created_at': '2026-01-01T00:00:00Z',
      'stats': {'views': 12, 'likes': 3, 'comments': 2, 'shares': 1},
    });
    expect(video.id, 'v1');
    expect(video.stats.likes, 3);
  });
}
