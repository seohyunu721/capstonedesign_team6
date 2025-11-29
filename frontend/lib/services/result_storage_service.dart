import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class ResultStorageService {
  // 누적되게 변경
  static const String _resultKey = 'AnalysisResultList';

  Future<void> saveAnalysisResult(Map<String, dynamic> newResult) async {
    final prefs = await SharedPreferences.getInstance();
    final currentJsonStrings = prefs.getStringList(_resultKey) ?? [];
    final String newJsonString = jsonEncode(newResult);

    currentJsonStrings.insert(0, newJsonString);
    await prefs.setStringList(_resultKey, currentJsonStrings);
  }

  Future<List<Map<String, dynamic>>> loadAnalysisResults() async {
    final prefs = await SharedPreferences.getInstance();
    final List<String> jsonStringList = prefs.getStringList(_resultKey) ?? [];

    if (jsonStringList.isEmpty) {
      return [];
    }

    final decodedMaps = jsonStringList
        .map((jsonString) {
          try {
            final decoded = jsonDecode(jsonString);

            if (decoded != null && decoded is Map) {
              return decoded.cast<String, dynamic>();
            } else {
              print("분석 결과 디코딩 오류: JSON이 유효한 MAP 형태 아님");
              return <String, dynamic>{};
            }
          } catch (e) {
            print("분석 결과 디코딩 오류 발생: $e");
            return <String, dynamic>{};
          }
        })
        .where((map) => map.isNotEmpty)
        .toList();

    return decodedMaps;
  }

  Future<void> clearAnalysisResults() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_resultKey);
  }
}
