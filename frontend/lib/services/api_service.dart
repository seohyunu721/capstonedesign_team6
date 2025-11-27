import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class ApiService {
  // 플랫폼별 API URL 설정
  final String apiUrl = kIsWeb
      ? "http://127.0.0.1:8000"
      : (defaultTargetPlatform == TargetPlatform.android
            ? "http://10.0.2.2:8000"
            : "http://127.0.0.1:8000");

  Future<Map<String, dynamic>> analyzeVoice({
    required Uint8List fileBytes,
    required String fileName,
    required String gender,
    required String genre,
    required int startYear,
    required int endYear,
  }) async {
    try {
      var uri = Uri.parse("$apiUrl/analyze");
      var request = http.MultipartRequest('POST', uri);

      // 사용자 설정 필드 추가
      request.fields['gender'] = gender;
      request.fields['genre'] = genre;
      request.fields['start_year'] = startYear.toString();
      request.fields['end_year'] = endYear.toString();

      // 파일 추가
      request.files.add(
        http.MultipartFile.fromBytes(
          'voice_file', // 백엔드와 키 이름 일치
          fileBytes,
          filename: fileName,
        ),
      );
      // 시간 늘림 300
      var response = await request.send().timeout(const Duration(seconds: 300));

      if (response.statusCode == 200) {
        var responseBody = await response.stream.bytesToString();
        return jsonDecode(responseBody) as Map<String, dynamic>;
      } else {
        var responseBody = await response.stream.bytesToString();
        throw Exception("분석 실패: ${response.statusCode}\n$responseBody");
      }
    } catch (e) {
      rethrow;
    }
  }
}
