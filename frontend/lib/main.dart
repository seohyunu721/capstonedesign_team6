import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '/screens/analysis/analysis_screen.dart';
import '/screens/setup/setup_screen.dart';
import '/core/theme/app_theme.dart';

// --- 앱 시작점 ---
void main() async {
  // Flutter 엔진과 위젯 바인딩을 초기화합니다.
  WidgetsFlutterBinding.ensureInitialized();

  final prefs = await SharedPreferences.getInstance();
  // 'isSetupComplete' 상태를 확인하여 초기 설정 완료 여부를 결정합니다.
  final bool isSetupComplete = prefs.getBool('isSetupComplete') ?? false;

  runApp(MyApp(isSetupComplete: isSetupComplete));
}

class MyApp extends StatelessWidget {
  final bool isSetupComplete;
  const MyApp({Key? key, required this.isSetupComplete}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Vocalize: AI 음성 분석기',
      // 분리된 AppTheme 사용
      theme: AppTheme.lightTheme,
      // isSetupComplete 값에 따라 SetupScreen 또는 AnalysisScreen을 홈으로 지정
      home: isSetupComplete ? AnalysisScreen() : SetupScreen(),
    );
  }
}
