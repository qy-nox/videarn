import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:video_player/video_player.dart';
import '../../models/video.dart';
import '../../providers/app_providers.dart';
import '../../widgets/error_view.dart';

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});
  @override
  ConsumerState<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends ConsumerState<HomeScreen> {
  bool following = false;
  @override
  Widget build(BuildContext context) {
    final feed = ref.watch(feedProvider(following));
    return Scaffold(
      backgroundColor: Colors.black,
      body: feed.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => ErrorView(message: 'Unable to load videos: $error', onRetry: () => ref.invalidate(feedProvider(following))),
        data: (videos) => videos.isEmpty
            ? const Center(child: Text('No videos available yet.'))
            : Stack(children: [
                PageView.builder(
                  scrollDirection: Axis.vertical,
                  itemCount: videos.length,
                  itemBuilder: (_, index) => VideoCard(video: videos[index]),
                ),
                SafeArea(
                  child: Align(
                    alignment: Alignment.topCenter,
                    child: SegmentedButton<bool>(
                      segments: const [
                        ButtonSegment(value: false, label: Text('For You')),
                        ButtonSegment(value: true, label: Text('Following')),
                      ],
                      selected: {following},
                      onSelectionChanged: (value) => setState(() => following = value.first),
                    ),
                  ),
                ),
              ]),
      ),
    );
  }
}

class VideoCard extends ConsumerStatefulWidget {
  const VideoCard({required this.video, super.key});
  final Video video;
  @override
  ConsumerState<VideoCard> createState() => _VideoCardState();
}

class _VideoCardState extends ConsumerState<VideoCard> {
  VideoPlayerController? controller;
  bool liked = false;
  @override
  void initState() { super.initState(); }
  @override
  void dispose() { controller?.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) => Stack(fit: StackFit.expand, children: [
        if (widget.video.thumbnailUrl != null)
          Image.network(widget.video.thumbnailUrl!, fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => const ColoredBox(color: Colors.black)),
        const DecoratedBox(decoration: BoxDecoration(gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: [Colors.transparent, Colors.black87]))),
        Positioned(
          right: 12, bottom: 140,
          child: Column(children: [
            IconButton(onPressed: () async { await ref.read(videoRepositoryProvider).like(widget.video.id, liked); setState(() => liked = !liked); }, icon: Icon(liked ? Icons.favorite : Icons.favorite_border, color: liked ? Colors.red : Colors.white, size: 32)),
            Text('${widget.video.stats.likes}'),
            IconButton(onPressed: () => _comments(context), icon: const Icon(Icons.comment_outlined, size: 30)),
            Text('${widget.video.stats.comments}'),
            IconButton(onPressed: () {}, icon: const Icon(Icons.share_outlined, size: 30)),
          ]),
        ),
        Positioned(left: 16, right: 70, bottom: 32, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('@${widget.video.creatorId.substring(0, 8)}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          if (widget.video.caption != null) Padding(padding: const EdgeInsets.only(top: 8), child: Text(widget.video.caption!)),
        ])),
      ]);
  Future<void> _comments(BuildContext context) async {
    showModalBottomSheet(context: context, isScrollControlled: true, builder: (_) => CommentsSheet(videoId: widget.video.id));
  }
}

class CommentsSheet extends ConsumerStatefulWidget {
  const CommentsSheet({required this.videoId, super.key});
  final String videoId;
  @override
  ConsumerState<CommentsSheet> createState() => _CommentsSheetState();
}
class _CommentsSheetState extends ConsumerState<CommentsSheet> {
  final input = TextEditingController();
  @override
  Widget build(BuildContext context) => SafeArea(child: Padding(padding: const EdgeInsets.all(16), child: Column(mainAxisSize: MainAxisSize.min, children: [
    const Text('Comments', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
    const SizedBox(height: 16),
    TextField(controller: input, decoration: InputDecoration(hintText: 'Add a comment', suffixIcon: IconButton(icon: const Icon(Icons.send), onPressed: () async { if (input.text.trim().isEmpty) return; await ref.read(videoRepositoryProvider).addComment(widget.videoId, input.text.trim()); input.clear(); if (mounted) setState(() {}); }))),
  ])));
  @override
  void dispose() { input.dispose(); super.dispose(); }
}
