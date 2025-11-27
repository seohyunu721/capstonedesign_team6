import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class ResultStorageService {
  static const String _resultKey = 'lastAnalysisResult';

  Future<void> saveAnalysisResult(Map<String, dynamic> result) async {
    final prefs = await SharedPreferences.getInstance();
    final String jsonString = jsonEncode(result);
    await prefs.setString(_resultKey, jsonString);
  }

  Future<Map<String, dynamic>?> loadAnalysisResult() async {
    final prefs = await SharedPreferences.getInstance();
    final String? jsonString = prefs.getString(_resultKey);

    if (jsonString == null) {
      return null;
    }

    try {
      return jsonDecode(jsonString) as Map<String, dynamic>;
    } catch (e) {
      print(" 결과 값이 없음: $e");
      return null;
    }
  }

  Future<void> clearAnalysisResult() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_resultKey);
  }
}
