import 'package:shared_preferences/shared_preferences.dart';

class PreferencesService {
  // 설정 저장
  Future<void> savePreferences({
    required String gender,
    required String genre,
    required double startYear,
    required double endYear,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isSetupComplete', true);
    await prefs.setString('gender', gender);
    await prefs.setString('genre', genre);
    await prefs.setDouble('startYear', startYear);
    await prefs.setDouble('endYear', endYear);
  }

  // 설정 불러오기
  Future<Map<String, dynamic>> loadPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    return {
      'gender': prefs.getString('gender') ?? 'none',
      'genre': prefs.getString('genre') ?? 'none',
      'startYear': prefs.getDouble('startYear')?.round() ?? 1980,
      'endYear': prefs.getDouble('endYear')?.round() ?? 2025,
    };
  }
}
