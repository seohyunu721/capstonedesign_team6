import 'package:flutter/material.dart';
import '/screens/analysis/analysis_screen.dart';
import '/screens/setup/setup_screen.dart';
import '/core/theme/app_theme.dart';
import '/screens/splash/splash_screen.dart';

// --- 앱 시작점 ---
void main() async {
  // Flutter 엔진과 위젯 바인딩을 초기화합니다.
  WidgetsFlutterBinding.ensureInitialized();

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Vocalize: AI 음성 분석기',
      // 분리된 AppTheme 사용
      theme: AppTheme.lightTheme,
      // isSetupComplete 값에 따라 SetupScreen 또는 AnalysisScreen을 홈으로 지정
      home: SplashScreen(),
    );
  }
}
