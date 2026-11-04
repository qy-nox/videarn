import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../models/video.dart';
import '../repositories/auth_repository.dart';
import '../repositories/video_repository.dart';

final tokenStoreProvider = Provider<TokenStore>((_) => TokenStore());
final apiClientProvider = Provider<ApiClient>(
    (ref) => ApiClient(ref.watch(tokenStoreProvider)));
final authRepositoryProvider =
    Provider<AuthRepository>((ref) => AuthRepository(ref.watch(apiClientProvider)));
final videoRepositoryProvider =
    Provider<VideoRepository>((ref) => VideoRepository(ref.watch(apiClientProvider)));

final feedProvider = FutureProvider.autoDispose
    .family<List<Video>, bool>((ref, following) async {
  return ref.watch(videoRepositoryProvider).feed(following: following);
});

final currentUserProvider = FutureProvider.autoDispose((ref) {
  return ref.watch(authRepositoryProvider).currentUser();
});
