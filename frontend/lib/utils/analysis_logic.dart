// utils/analysis_logic.dart

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class AnalysisLogic {
  
  /// Note 문자열 (예: C4, G#5)을 MIDI 값으로 변환
  static int? noteToMidi(String? note) {
    if (note == null) return null;
    final RegExp regex = RegExp(r'^([A-Ga-g])([#♯b♭]?)(\d)$');
    final match = regex.firstMatch(
      note.replaceAll('♯', '#').replaceAll('♭', 'b'),
    );
    if (match == null) return null;
    const scale = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11};
    int octave = int.parse(match.group(3)!);
    int base = scale[match.group(1)!.toUpperCase()]!;
    String acc = match.group(2) ?? "";
    if (acc.contains('#')) base += 1;
    if (acc.contains('b')) base -= 1;
    return base + (octave + 1) * 12;
  }

  /// 곡과 사용자의 음역대 겹침 점수 계산
  static int rangeMatchScore(
    Map<String, dynamic> song,
    int userLowMidi,
    int userHighMidi,
  ) {
    int? low = noteToMidi(song['lowest_note']?.toString());
    int? high = noteToMidi(song['highest_note']?.toString());
    if (low == null || high == null) return 100000; // 음역대 정보 없으면 후순위
    
    bool overlap = userHighMidi >= low && userLowMidi <= high;
    if (overlap) return 0; // 겹치면 최고 점수
    
    // 겹치지 않으면 중간 음 높이 차이로 점수 부여
    int songMid = (low + high) ~/ 2;
    int userMid = (userLowMidi + userHighMidi) ~/ 2;
    return (songMid - userMid).abs();
  }

  /// YouTube URL 열기
  static Future<void> openYouTubeUrl(BuildContext context, String url) async {
    try {
      final uri = Uri.parse(url);
      if (await canLaunchUrl(uri)) {
        await launchUrl(uri, mode: LaunchMode.externalApplication);
      } else {
        if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('YouTube를 열 수 없습니다.')),
          );
        }
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('오류 발생: $e')),
        );
      }
    }
  }

  /// YouTube 검색 열기
  static Future<void> openYouTubeSearch(BuildContext context, String singer, String songTitle) async {
    String searchQuery = Uri.encodeComponent('$singer $songTitle');
    String youtubeUrl = 'https://www.youtube.com/results?search_query=$searchQuery';
    await openYouTubeUrl(context, youtubeUrl);
  }
}