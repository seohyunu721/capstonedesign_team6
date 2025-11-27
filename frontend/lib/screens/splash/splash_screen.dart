import 'dart:async';
// import 'package:frontend/widgets/custom_curved_nav_bar.dart';
import 'package:lottie/lottie.dart';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
// import '/screens/analysis/analysis_screen.dart';
import '/screens/navigator/main_navigator_screen.dart';
import '/screens/setup/setup_screen.dart';
import '/core/theme/colors.dart';

class SplashScreen extends StatefulWidget {
  final bool isSetupComplete; // 받아오기

  const SplashScreen({super.key, required this.isSetupComplete});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    _navigateToNextScreen();
  }

  Future<void> _navigateToNextScreen() async {
    await Future.delayed(const Duration(seconds: 3));

    final prefs = await SharedPreferences.getInstance();

    final bool isSetupComplete = prefs.getBool('isSetupComplete') ?? false;

    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (context) {
          if (isSetupComplete) {
            return const MainNavigatorScreen(initialIndex: 1);
          } else {
            return SetupScreen();
          }
        }, // const 키워드 추가
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: CustomColors.deepPurple, // CustomColors가 정의되어 있다고 가정합니다.
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            LottieBuilder.asset(
              'assets/Lottie/Square Box.json',
              width: 200,
              height: 200,
            ),
            const SizedBox(height: 20),
            const Text(
              'Vocalize',
              style: TextStyle(
                color: CustomColors.white,
                fontWeight: FontWeight.bold,
                fontFamily: 'Pretendard',
              ),
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}
