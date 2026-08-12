import 'package:flutter/material.dart';
import 'auth_screen.dart';

class OnboardingScreen extends StatelessWidget {
  const OnboardingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const Icon(Icons.shield_outlined, size: 100, color: Colors.blueAccent),
              const SizedBox(height: 24),
              const Text(
                'Welcome to Sentri',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 12),
              const Text(
                'Sentri helps you detect scams, phishing, and malicious links before you act.',
                style: TextStyle(fontSize: 16, color: Colors.grey),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 40),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.pushReplacement(
                      context,
                      MaterialPageRoute(builder: (context) => const AuthScreen()),
                    );
                  },
                  child: const Padding(
                    padding: EdgeInsets.symmetric(vertical: 14.0),
                    child: Text('Get Started'),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}