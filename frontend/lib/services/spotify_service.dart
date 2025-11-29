// SpotifyService.dart
import 'dart:convert';
import 'package:http/http.dart' as http;

class SpotifyService {
  // 🚨 여기에 사용자의 유효한 Client ID와 Secret을 입력해야 합니다.
  final String clientId = "2c4860d3fd5488588e05b1e90f76b78";
  final String clientSecret = "1d8ac11f5f594384a31779cfe17a2941";

  // 1단계: AccessToken 발급
  Future<String?> _getAccessToken() async {
    final String basicAuth =
        "Basic ${base64Encode(utf8.encode('$clientId:$clientSecret'))}";

    try {
      final response = await http.post(
        // 🌟 공식 URL로 수정 1: 토큰 발급 엔드포인트
        Uri.parse(
          "https://accounts.spotify.com/api/token", // 토큰 발급하고 바꿔야 함
        ), // <--- 이 주소를 확인하세요!
        headers: {
          "Authorization": basicAuth,
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: {"grant_type": "client_credentials"},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print("✅ Spotify Token 발급 성공.");
        return data["access_token"];
      } else {
        print("❌ Spotify Token 발급 실패 (Status: ${response.statusCode})");
        print("응답 본문: ${response.body}");
        return null;
      }
    } catch (e) {
      print("❌ Spotify Token 요청 중 예외 발생: $e");
      return null;
    }
  }

  // 2단계: 가수 이미지 URL 가져오기 (Search API)
  Future<String?> fetchArtistImage(String artistName) async {
    final accessToken = await _getAccessToken();
    if (accessToken == null) return null;

    final query = Uri.encodeQueryComponent(artistName);

    try {
      final response = await http.get(
        // 🌟 공식 URL로 수정 2: 아티스트 검색 엔드포인트
        Uri.parse(
          "https://api.spotify.com/v1/search?q=$query&type=artist&limit=1", // 이것도
        ), // <--- 이 주소를 확인하세요!
        headers: {"Authorization": "Bearer $accessToken"},
      );

      if (response.statusCode == 200) {
        final json = jsonDecode(response.body);
        final items = json["artists"]["items"];

        if (items.isEmpty) {
          print("❌ Spotify 검색 결과 없음: $artistName");
          return null;
        }

        final images = items[0]["images"];
        if (images == null || images.isEmpty) {
          print("❌ Spotify 검색 결과에 이미지가 포함되어 있지 않음.");
          return null;
        }

        final imageUrl = images[0]["url"];
        print("✅ Spotify 이미지 URL 가져오기 성공: $imageUrl");
        return imageUrl;
      } else {
        print("❌ Spotify Artist 검색 실패 (Status: ${response.statusCode})");
        print("응답 본문: ${response.body}");
        return null;
      }
    } catch (e) {
      print("❌ Spotify Artist 검색 중 예외 발생: $e");
      return null;
    }
  }
}
