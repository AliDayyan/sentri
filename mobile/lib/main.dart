import 'package:flutter/material.dart';
import 'screens/splash_screen.dart';

void main() {
  runApp(const SentriApp());
}

class SentriApp extends StatefulWidget {
  const SentriApp({super.key});

  static _SentriAppState? of(BuildContext context) =>
      context.findAncestorStateOfType<_SentriAppState>();

  @override
  State<SentriApp> createState() => _SentriAppState();
}

class _SentriAppState extends State<SentriApp> {
  ThemeMode _themeMode = ThemeMode.system;

  void setThemeMode(ThemeMode mode) {
    setState(() {
      _themeMode = mode;
    });
  }

  ThemeMode get themeMode => _themeMode;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sentri',
      themeMode: _themeMode,
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
        brightness: Brightness.light,
      ),
      darkTheme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF121212),
      ),
      home: const SplashScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}