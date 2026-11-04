import 'package:dio/dio.dart';
import 'dart:io';
import '../core/api_client.dart';
import '../models/video.dart';

class VideoRepository {
  VideoRepository(this.client);
  final ApiClient client;

  Future<List<Video>> feed({bool following = false, String? cursor}) async {
    final response = await client.dio.get(
      following ? '/feed/following' : '/feed/for-you',
      queryParameters: {'limit': 20, if (cursor != null) 'cursor': cursor},
    );
    return (response.data as List)
        .map((item) => Video.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<Map<String, dynamic>>> comments(String videoId) async {
    final response = await client.dio.get('/videos/$videoId/comments');
    return (response.data as List).cast<Map<String, dynamic>>();
  }

  Future<void> like(String id, bool liked) async {
    await client.dio.request('/videos/$id/like', method: liked ? 'DELETE' : 'POST');
  }

  Future<void> addComment(String videoId, String body) async {
    await client.dio.post('/videos/$videoId/comments', data: {'body': body});
  }

  Future<Map<String, dynamic>> search(String query) async {
    final response = await client.dio.get('/search', queryParameters: {'q': query});
    return (response.data as Map).cast<String, dynamic>();
  }

  Future<Map<String, dynamic>> uploadUrl({
    required String filename,
    required String contentType,
    required int sizeBytes,
  }) async {
    final response = await client.dio.post('/videos/upload-url', data: {
      'filename': filename,
      'content_type': contentType,
      'size_bytes': sizeBytes,
    });
    return (response.data as Map).cast<String, dynamic>();
  }

  Future<void> uploadAndCreate({
    required File file,
    required String filename,
    required int durationSeconds,
    String? caption,
  }) async {
    final size = await file.length();
    final upload = await uploadUrl(
      filename: filename,
      contentType: 'video/mp4',
      sizeBytes: size,
    );
    await client.dio.put(
      upload['upload_url'] as String,
      data: file.openRead(),
      options: Options(
        headers: {
          Headers.contentLengthHeader: size,
          Headers.contentTypeHeader: 'video/mp4',
        },
        validateStatus: (status) => status != null && status >= 200 && status < 300,
      ),
    );
    await client.dio.post('/videos', data: {
      'source_key': upload['source_key'],
      'duration_seconds': durationSeconds,
      'caption': caption,
      'privacy': 'public',
    });
  }
}
