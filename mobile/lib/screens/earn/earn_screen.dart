import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/api_client.dart';
import '../../providers/app_providers.dart';

final walletSummaryProvider = FutureProvider.autoDispose((ref) async {
  final response = await ref.watch(apiClientProvider).dio.get('/wallet');
  return (response.data as Map).cast<String, dynamic>();
});

class EarnScreen extends ConsumerWidget {
  const EarnScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final wallet = ref.watch(walletSummaryProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Earn')),
      body: wallet.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(child: Text('Unable to load earnings: $error')),
        data: (data) => ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('Available coins'),
                  const SizedBox(height: 8),
                  Text('${data['balance_coins'] ?? 0}', style: Theme.of(context).textTheme.displaySmall),
                  Text('Estimated USD: ${data['estimated_usd'] ?? 0}'),
                ]),
              ),
            ),
            const SizedBox(height: 16),
            const ListTile(
              leading: Icon(Icons.verified_outlined),
              title: Text('Verified rewards'),
              subtitle: Text('Rewarded ads are credited only after server-side verification.'),
            ),
          ],
        ),
      ),
    );
  }
}
