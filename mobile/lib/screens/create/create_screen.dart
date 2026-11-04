import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../providers/app_providers.dart';

class CreateScreen extends ConsumerStatefulWidget {
  const CreateScreen({super.key});
  @override
  State<CreateScreen> createState() => _CreateScreenState();
}
class _CreateScreenState extends ConsumerState<CreateScreen> {
  final picker = ImagePicker();
  XFile? video;
  final caption = TextEditingController();
  bool uploading = false;
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Create video')),
    body: ListView(padding: const EdgeInsets.all(20), children: [
      OutlinedButton.icon(onPressed: uploading ? null : () async { final selected = await picker.pickVideo(source: ImageSource.gallery, maxDuration: const Duration(seconds: 90)); if (selected != null) setState(() => video = selected); }, icon: const Icon(Icons.video_library), label: Text(video == null ? 'Choose from gallery' : File(video!.path).path.split('/').last)),
      const SizedBox(height: 16),
      TextField(controller: caption, maxLines: 4, maxLength: 2200, decoration: const InputDecoration(labelText: 'Caption', border: OutlineInputBorder())),
      const SizedBox(height: 16),
      FilledButton.icon(onPressed: video == null || uploading ? null : () => _submit(), icon: const Icon(Icons.cloud_upload), label: Text(uploading ? 'Uploading...' : 'Upload video')),
    ]),
  );
  Future<void> _submit() async {
    final selected = video;
    if (selected == null) return;
    setState(() => uploading = true);
    try {
      await ref.read(videoRepositoryProvider).uploadAndCreate(
        file: File(selected.path),
        filename: selected.name,
        durationSeconds: 15,
        caption: caption.text.trim().isEmpty ? null : caption.text.trim(),
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Video uploaded and queued for processing.')),
        );
        setState(() => video = null);
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Upload failed: $e')),
      );
    } finally {
      if (mounted) setState(() => uploading = false);
    }
  }
  @override
  void dispose() { caption.dispose(); super.dispose(); }
}
