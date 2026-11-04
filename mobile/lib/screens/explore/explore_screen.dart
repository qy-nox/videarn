import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/app_providers.dart';
import '../../widgets/error_view.dart';

class ExploreScreen extends ConsumerStatefulWidget {
  const ExploreScreen({super.key});
  @override
  ConsumerState<ExploreScreen> createState() => _ExploreScreenState();
}
class _ExploreScreenState extends ConsumerState<ExploreScreen> {
  final query = TextEditingController();
  Map<String, dynamic>? results;
  Object? error;
  bool loading = false;
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: TextField(controller: query, textInputAction: TextInputAction.search, onSubmitted: (_) => search(), decoration: const InputDecoration(hintText: 'Search users or videos', border: InputBorder.none),)),
    body: loading ? const Center(child: CircularProgressIndicator()) : error != null ? ErrorView(message: '$error', onRetry: search) : results == null ? const Center(child: Text('Search ClipEarn')) : ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Users', style: Theme.of(context).textTheme.titleLarge),
        ...((results!['users'] as List? ?? const []).map((item) => ListTile(leading: const CircleAvatar(child: Icon(Icons.person)), title: Text(item['username']?.toString() ?? 'User')))),
        Text('Videos', style: Theme.of(context).textTheme.titleLarge),
        ...((results!['videos'] as List? ?? const []).map((item) => ListTile(leading: const Icon(Icons.video_library), title: Text(item['caption']?.toString() ?? 'Video')))),
      ],
    ),
  );
  Future<void> search() async { if (query.text.trim().isEmpty) return; setState(() { loading = true; error = null; }); try { results = await ref.read(videoRepositoryProvider).search(query.text.trim()); } catch (e) { error = e; } finally { if (mounted) setState(() => loading = false); } }
  @override
  void dispose() { query.dispose(); super.dispose(); }
}
