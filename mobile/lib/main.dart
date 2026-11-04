import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:firebase_core/firebase_core.dart';
import 'routing/app_router.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();
  runApp(const ClipEarnApp());
}

class ClipEarnApp extends StatelessWidget {
  const ClipEarnApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp.router(
        title: 'ClipEarn',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          brightness: Brightness.dark,
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff8b5cf6), brightness: Brightness.dark),
          scaffoldBackgroundColor: const Color(0xff080a12),
          useMaterial3: true,
        ),
        localizationsDelegates: const [
          GlobalMaterialLocalizations.delegate,
          GlobalWidgetsLocalizations.delegate,
          GlobalCupertinoLocalizations.delegate,
        ],
        supportedLocales: const [Locale('en'), Locale('bn')],
        routerConfig: appRouter,
      );
}
