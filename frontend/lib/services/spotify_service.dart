// SpotifyService.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';
import 'dart:io' show Platform;

class SpotifyService {
  // 백엔드 API URL 설정 (보안: Client Secret은 백엔드에서만 관리)
  final String apiUrl = kIsWeb
      ? "http://127.0.0.1:8000"
      : (defaultTargetPlatform == TargetPlatform.android
            ? "http://10.0.2.2:8000"
            : "http://127.0.0.1:8000");

  // 가수 이미지 URL 가져오기 (백엔드 API 호출)
  Future<String?> fetchArtistImage(String artistName) async {
    if (artistName.isEmpty || artistName == 'N/A') {
      return null;
    }

    try {
      // URL 인코딩
      final encodedName = Uri.encodeComponent(artistName);
      final uri = Uri.parse("$apiUrl/artist-image/$encodedName");

      final response = await http.get(
        uri,
        headers: {"Content-Type": "application/json"},
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode != 200) {
        print('❌ [Spotify] 백엔드 API 호출 실패: ${response.statusCode}');
        return null;
      }

      final json = jsonDecode(response.body);
      final imageUrl = json["image_url"] as String?;

      if (imageUrl == null || imageUrl.isEmpty) {
        print('⚠️ [Spotify] 이미지 URL이 없음: $artistName');
        return null;
      }

      return imageUrl;
    } catch (e) {
      print('❌ [Spotify] 이미지 가져오기 오류: $e');
      return null;
    }
  }
}
