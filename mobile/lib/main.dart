import 'package:flutter/material.dart';
import 'screens/splash_screen.dart';

void main() {
  runApp(const SentriApp());
}

class SentriApp extends StatelessWidget {
  const SentriApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Sentri',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const SplashScreen(),
      debugShowCheckedModeBanner: false,
    );
  }
}