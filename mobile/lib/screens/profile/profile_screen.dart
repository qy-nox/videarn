import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/app_providers.dart';
import '../../widgets/error_view.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: user.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => ErrorView(message: 'Unable to load profile: $e', onRetry: () => ref.invalidate(currentUserProvider)),
        data: (data) => ListView(padding: const EdgeInsets.all(20), children: [
          const CircleAvatar(radius: 42, child: Icon(Icons.person, size: 44)),
          const SizedBox(height: 12),
          Text(data.username ?? 'Set your username', style: Theme.of(context).textTheme.headlineSmall, textAlign: TextAlign.center),
          Text(data.email ?? '', textAlign: TextAlign.center),
          const SizedBox(height: 28),
          ListTile(leading: const Icon(Icons.settings), title: const Text('Settings'), trailing: const Icon(Icons.chevron_right), onTap: () {}),
          ListTile(leading: const Icon(Icons.logout), title: const Text('Sign out'), onTap: () async { await ref.read(authRepositoryProvider).logout(); if (context.mounted) Navigator.of(context).popUntil((route) => route.isFirst); }),
        ]),
      ),
    );
  }
}
