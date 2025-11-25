import 'dart:convert';
import 'package:http/http.dart' as http;

class SpotifyService {
  final String clientId = "a2c4860d3fd5488588e05b1e90f76b78";

  final String clientSecret = "1d8ac11f5f594384a31779cfe17a2941";

  // AccessToken 발급
  Future<String> _getAccessToken() async {
    final String basicAuth =
        "Basic ${base64Encode(utf8.encode('$clientId:$clientSecret'))}";

    final response = await http.post(
      Uri.parse("https://accounts.spotify.com/api/token"),
      headers: {
        "Authorization": basicAuth,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: {"grant_type": "client_credentials"},
    );

    final data = jsonDecode(response.body);
    return data["access_token"];
  }

  // 가수 이미지 URL 가져오기
  Future<String?> fetchArtistImage(String artistName) async {
    final accessToken = await _getAccessToken();

    final response = await http.get(
      Uri.parse("https://api.spotify.com/v1/search?q=$artistName&type=artist"),
      headers: {"Authorization": "Bearer $accessToken"},
    );

    final json = jsonDecode(response.body);
    final items = json["artists"]["items"];

    if (items.isEmpty) return null;

    final images = items[0]["images"];
    if (images.isEmpty) return null;

    return images[0]["url"]; // 가장 큰 이미지
  }
}
