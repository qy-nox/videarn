import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../providers/app_providers.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final email = TextEditingController();
  final password = TextEditingController();
  bool loading = false;
  String? error;
  @override
  void dispose() { email.dispose(); password.dispose(); super.dispose(); }
  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 420),
                child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                  const Icon(Icons.play_circle_fill, size: 72, color: Color(0xff8b5cf6)),
                  const SizedBox(height: 16),
                  Text('ClipEarn', style: Theme.of(context).textTheme.headlineLarge, textAlign: TextAlign.center),
                  const Text('Watch. Create. Connect. Earn.', textAlign: TextAlign.center),
                  const SizedBox(height: 40),
                  TextField(controller: email, decoration: const InputDecoration(labelText: 'Email')),
                  const SizedBox(height: 12),
                  TextField(controller: password, obscureText: true, decoration: const InputDecoration(labelText: 'Password')),
                  if (error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(error!, style: const TextStyle(color: Colors.red))),
                  const SizedBox(height: 20),
                  FilledButton(
                    onPressed: loading ? null : _login,
                    child: loading ? const CircularProgressIndicator() : const Text('Continue'),
                  ),
                  TextButton(onPressed: () {}, child: const Text('Phone or Google sign-in')),
                ]),
              ),
            ),
          ),
        ),
      );
      Future<void> _login() async {
        if (email.text.trim().isEmpty || password.text.isEmpty) {
          setState(() => error = 'Enter your email and password.');
          return;
        }
        setState(() { loading = true; error = null; });
        try {
          final credential = await FirebaseAuth.instance.signInWithEmailAndPassword(
            email: email.text.trim(),
            password: password.text,
          );
          final idToken = await credential.user?.getIdToken();
          if (idToken == null) throw StateError('Firebase did not return an ID token.');
          await ref.read(authRepositoryProvider).firebaseLogin(idToken);
          if (mounted) context.go('/home');
        } on FirebaseAuthException catch (e) {
          if (mounted) setState(() => error = e.message ?? 'Authentication failed.');
        } catch (e) {
          if (mounted) setState(() => error = 'Authentication failed: $e');
        } finally {
          if (mounted) setState(() => loading = false);
        }
      }
}
