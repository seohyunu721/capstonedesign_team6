// lib/widgets/result_card.dart

import 'package:flutter/material.dart';
import '/core/theme/colors.dart'; // [필수] CustomColors가 정의된 경로를 확인하세요.
import 'dart:io' show Platform;
import '/services/spotify_service.dart'; // [필수] SpotifyService가 정의된 경로를 확인하세요.

// ------------------------------------------------------------------
// [경로 수정됨] result_card.dart (lib/widgets)의 위치에 맞춰 경로를 수정했습니다.
// ------------------------------------------------------------------

// 1. analysis_logic.dart는 일반적으로 lib/utils에 위치하므로 절대 경로 사용
import '/utils/analysis_logic.dart'; 

// 2. youtube_recommendation_sheet.dart는 result_card.dart와 같은 lib/widgets에 위치한다고 가정하고 상대 경로 사용
import 'youtube_recommendation_sheet.dart'; 

// ------------------------------------------------------------------

class ResultCard extends StatefulWidget {
  final Map<String, dynamic> analysisResult;

  const ResultCard({Key? key, required this.analysisResult}) : super(key: key);

  @override
  State<ResultCard> createState() => _ResultCardState();
}

class _ResultCardState extends State<ResultCard> {
  final SpotifyService _spotifyService = SpotifyService();
  String? _artistImageUrl;
  bool _isLoadingImage = false;

  @override
  void initState() {
    super.initState();
    _loadArtistImage();
  }

  Future<void> _loadArtistImage() async {
    final bestMatch = widget.analysisResult['best_match'] ?? 'N/A';
    if (bestMatch == 'N/A') return;

    setState(() {
      _isLoadingImage = true;
    });

    try {
      final imageUrl = await _spotifyService.fetchArtistImage(bestMatch);
      if (mounted) {
        setState(() {
          _artistImageUrl = imageUrl;
          _isLoadingImage = false;
        });
      }
    } catch (e) {
      print('❌ [ResultCard] Spotify 이미지 로드 실패: $e');
      if (mounted) {
        setState(() {
          _isLoadingImage = false;
        });
      }
    }
  }

  // --- UI 컴포넌트 ---

  Widget _buildInfoTile(IconData icon, String title, String subtitle) {
    return ListTile(
      leading: Icon(icon, color: CustomColors.deepPurple),
      title: Text(
        title,
        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
      ),
      subtitle: Text(subtitle, style: const TextStyle(fontSize: 18)),
    );
  }

  Widget _buildYouTubePlayer(
    Map<String, dynamic> songInfo,
    String defaultSinger,
  ) {
    String songTitle = songInfo['title'] ?? '';
    String? videoId = songInfo['youtube_video_id'];
    String? youtubeUrl = songInfo['youtube_url'];
    String singer = songInfo['singer'] ?? defaultSinger;

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8.0),
      child: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            GestureDetector(
              onTap: () {
                if (youtubeUrl != null) {
                  AnalysisLogic.openYouTubeUrl(context, youtubeUrl);
                } else {
                  AnalysisLogic.openYouTubeSearch(context, singer, songTitle);
                }
              },
              child: Row(
                children: [
                  Icon(Icons.music_video, color: CustomColors.deepPurple),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                songTitle,
                                style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            Icon(
                              Icons.open_in_new,
                              size: 16,
                              color: CustomColors.deepPurple,
                            ),
                          ],
                        ),
                        Text(
                          singer,
                          style: TextStyle(
                            fontSize: 14,
                            color: CustomColors.mediumGrey,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            _buildVideoPreview(
              videoId: videoId,
              youtubeUrl: youtubeUrl,
              singer: singer,
              songTitle: songTitle,
            ),
            const SizedBox(height: 12),
            // YouTube 링크 버튼
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () {
                  if (youtubeUrl != null) {
                    AnalysisLogic.openYouTubeUrl(context, youtubeUrl);
                  } else {
                    AnalysisLogic.openYouTubeSearch(context, singer, songTitle);
                  }
                },
                icon: const Icon(Icons.play_arrow),
                label: Text(
                  videoId != null ? 'YouTube에서 전체 보기' : 'YouTube에서 검색',
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: CustomColors.deepPurple,
                  foregroundColor: Colors.white,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVideoPreview({
    required String? videoId,
    required String? youtubeUrl,
    required String singer,
    required String songTitle,
  }) {
    final imageUrl = videoId != null
        ? 'https://img.youtube.com/vi/$videoId/hqdefault.jpg'
        : null;

    return GestureDetector(
      onTap: () {
        if (youtubeUrl != null) {
          AnalysisLogic.openYouTubeUrl(context, youtubeUrl);
        } else {
          AnalysisLogic.openYouTubeSearch(context, singer, songTitle);
        }
      },
      child: AspectRatio(
        aspectRatio: 16 / 9,
        child: ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: Stack(
            fit: StackFit.expand,
            children: [
              if (imageUrl != null)
                Image.network(
                  imageUrl,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) =>
                      Container(color: Colors.black45),
                )
              else
                Container(color: Colors.black45),
              Container(
                decoration: const BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.bottomCenter,
                    end: Alignment.topCenter,
                    colors: [Colors.black54, Colors.transparent],
                  ),
                ),
              ),
              const Center(
                child: CircleAvatar(
                  radius: 28,
                  backgroundColor: Colors.black54,
                  child: Icon(Icons.play_arrow, color: Colors.white, size: 36),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // --- 데이터 처리 로직 (AnalysisLogic 호출) ---
  
  List<Map<String, dynamic>> _buildSingerSongSections(
    List<dynamic> youtubeSongs,
    List<dynamic> singerFullSongs,
    String defaultSinger,
    int? userLowMidi,
    int? userHighMidi,
  ) {
    final Map<String, Map<String, dynamic>> youtubeLookup = {};
    for (final song in youtubeSongs) {
      if (song is Map<String, dynamic>) {
        final title = (song['title'] ?? '').toString().toLowerCase();
        if (title.isNotEmpty) {
          youtubeLookup[title] = song;
        }
      }
    }

    final List<Map<String, dynamic>> sections = [];
    int rankCounter = 1;
    for (final entry in singerFullSongs) {
      if (entry is! Map<String, dynamic>) continue;
      final singer = entry['singer'] ?? defaultSinger;
      final songs = (entry['songs'] as List<dynamic>?) ?? const [];
      final List<Map<String, dynamic>> formattedSongs = [];

      for (final song in songs) {
        if (song is! Map<String, dynamic>) continue;
        final title = (song['title'] ?? '').toString();
        if (title.isEmpty) continue;
        final key = title.toLowerCase();
        final ytInfo = youtubeLookup[key];

        formattedSongs.add({
          'title': title,
          'singer': singer,
          'lowest_note': song['lowest_note'],
          'highest_note': song['highest_note'],
          'youtube_video_id': ytInfo?['youtube_video_id'],
          'youtube_url': ytInfo?['youtube_url'],
          'youtube_title': ytInfo?['youtube_title'],
        });
      }

      if (formattedSongs.isNotEmpty) {
        if (userLowMidi != null && userHighMidi != null) {
          // AnalysisLogic의 정적 메서드 사용
          formattedSongs.sort(
            (a, b) => AnalysisLogic.rangeMatchScore(
              a,
              userLowMidi,
              userHighMidi,
            ).compareTo(AnalysisLogic.rangeMatchScore(b, userLowMidi, userHighMidi)),
          );
        }
        sections.add({
          'singer': singer,
          'songs': formattedSongs,
          'rank': rankCounter,
        });
        rankCounter++;
      }
    }

    // fallback: youtube 정보만이라도 표시
    if (sections.isEmpty && youtubeSongs.isNotEmpty) {
      final fallbackSongs = youtubeSongs
          .whereType<Map<String, dynamic>>()
          .map(
            (song) => {
              'title': song['title'],
              'singer': song['singer'] ?? defaultSinger,
              'youtube_video_id': song['youtube_video_id'],
              'youtube_url': song['youtube_url'],
              'youtube_title': song['youtube_title'],
            },
          )
          .toList();
      sections.add({
        'singer': defaultSinger,
        'songs': fallbackSongs,
        'rank': rankCounter,
      });
    }

    return sections;
  }

  // --- build 메서드 ---

  @override
  Widget build(BuildContext context) {
    String bestMatch = widget.analysisResult['best_match'] ?? 'N/A';
    String userVocalRange =
        widget.analysisResult['user_vocal_range'] ?? '분석 불가';
    List<dynamic> recommended_songs =
        widget.analysisResult['recommended_songs'] ?? [];
    List<dynamic> topKResults = widget.analysisResult['top_k_results'] ?? [];
    final top3SongsWithYoutube =
        widget.analysisResult['top3_songs_with_youtube'] ?? [];
    List<dynamic> matchedSingerSongs =
        widget.analysisResult['matched_singer_full_songs'] ?? [];
    List<dynamic> topSingersFullSongs =
        widget.analysisResult['top_singers_full_songs'] ?? [];

    if (topSingersFullSongs.isEmpty && matchedSingerSongs.isNotEmpty) {
      topSingersFullSongs = [
        {'singer': bestMatch, 'songs': matchedSingerSongs},
      ];
    }

    // 사용자 음역대 파싱 (ex: "C3 ~ F4")
    int? userLowMidi, userHighMidi;
    final userVocalRangeStr = userVocalRange.replaceAll(' ', '');
    final parts = userVocalRangeStr.split('~');
    if (parts.length == 2) {
      // AnalysisLogic의 정적 메서드 사용
      userLowMidi = AnalysisLogic.noteToMidi(parts[0]);
      userHighMidi = AnalysisLogic.noteToMidi(parts[1]);
    }

    // graph URL 처리
    final String? rawGraphUrl =
        widget.analysisResult['pitch_graph_url'] as String?;
    String? graphUrl = rawGraphUrl;
    if (graphUrl != null && Platform.isAndroid) {
      graphUrl = graphUrl
          .replaceFirst('127.0.0.1', '10.0.2.2')
          .replaceFirst('localhost', '10.0.2.2');
    }
    debugPrint('ResultCard: graphUrl -> $graphUrl');

    final sections = _buildSingerSongSections(
      top3SongsWithYoutube,
      topSingersFullSongs,
      bestMatch,
      userLowMidi,
      userHighMidi,
    );

    final List<Map<String, dynamic>> mergedSongs = [];
    for (final section in sections) {
      final songs =
          (section['songs'] as List<Map<String, dynamic>>?) ?? const [];
      mergedSongs.addAll(songs);
    }
    final bool hasPlaylist = mergedSongs.isNotEmpty;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            Text(
              "📊 나의 목소리 리포트",
              style: Theme.of(
                context,
              ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
            ),
            const Divider(height: 30, thickness: 1),
            // 이미지 처리 (Spotify API 사용)
            CircleAvatar(
              radius: 50,
              backgroundColor: CustomColors.lightGrey,
              backgroundImage: _artistImageUrl != null
                  ? NetworkImage(_artistImageUrl!)
                  : null,
              child: _isLoadingImage
                  ? const CircularProgressIndicator()
                  : _artistImageUrl == null
                      ? Icon(
                          Icons.person,
                          size: 50,
                          color: CustomColors.mediumGrey,
                        )
                      : null,
              onBackgroundImageError: _artistImageUrl != null
                  ? (e, s) {
                      print('❌ [ResultCard] Spotify 이미지 로드 실패: $e');
                      if (mounted) {
                        setState(() {
                          _artistImageUrl = null;
                        });
                      }
                    }
                  : null,
            ),
            const SizedBox(height: 12),
            const Text("가장 유사한 가수는...", style: TextStyle(fontSize: 16)),
            Text(
              bestMatch,
              style: const TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
                color: CustomColors.deepPurple,
              ),
            ),
            const SizedBox(height: 24),
            // 음역대 정보
            _buildInfoTile(Icons.mic_none_outlined, "나의 음역대", userVocalRange),
            const SizedBox(height: 24),
            // 그래프 이미지 표시 (있으면)
            if (graphUrl != null && graphUrl.isNotEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      "📊 음역대 정밀 분석",
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Container(
                      decoration: BoxDecoration(
                        border: Border.all(color: Colors.grey.shade300),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Image.network(
                          graphUrl,
                          fit: BoxFit.contain,
                          errorBuilder: (_, error, stackTrace) {
                            debugPrint('ResultCard image error: $error');
                            return const Padding(
                              padding: EdgeInsets.all(20.0),
                              child: Text(
                                "그래프를 불러올 수 없습니다.",
                                textAlign: TextAlign.center,
                              ),
                            );
                          },
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            // Top3 추천곡 YouTube 플레이어
            Row(
              children: [
                Expanded(
                  child: Text(
                    "🎶 Top 추천곡 (YouTube)",
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                TextButton.icon(
                  onPressed: hasPlaylist
                      ? () => YouTubeRecommendationSheet.show( // 정적 메서드 호출
                            context,
                            sections,
                            bestMatch,
                          )
                      : null,
                  icon: const Icon(Icons.queue_music),
                  label: const Text("Top3 리스트 보기"),
                ),
              ],
            ),
            const Divider(height: 20),
            if (hasPlaylist)
              _buildYouTubePlayer(mergedSongs.first, bestMatch)
            else if (recommended_songs.isNotEmpty)
              // YouTube 정보가 아직 없을 때 (로딩 중)
              Column(
                children: recommended_songs.take(3).map((song) {
                  final songTitle = song.toString();
                  // [수정] top3SongsWithYoutube에서 해당 노래의 정보를 찾습니다.
                  final ytInfo = top3SongsWithYoutube.firstWhere(
                    (ytSong) => ytSong is Map && ytSong['title'] == songTitle,
                    orElse: () => null,
                  );
                  final youtubeUrl = ytInfo?['youtube_url'];

                  return Card(
                    margin: const EdgeInsets.symmetric(vertical: 8.0),
                    child: ListTile(
                      leading: Icon(
                        Icons.music_note,
                        color: CustomColors.deepPurple,
                      ),
                      title: Text(songTitle),
                      subtitle: Text(bestMatch),
                      trailing: Icon(
                        Icons.open_in_new,
                        color: CustomColors.deepPurple,
                      ),
                      onTap: () {
                        // [수정] URL이 있으면 바로 열고, 없으면 검색합니다.
                        if (youtubeUrl != null) {
                          AnalysisLogic.openYouTubeUrl(context, youtubeUrl);
                        } else {
                          AnalysisLogic.openYouTubeSearch(context, bestMatch, songTitle);
                        }
                      },
                    ),
                  );
                }).toList(),
              )
            else if (recommended_songs.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 10.0),
                child: Text(
                  "당신의 음역대에 맞는 추천곡이 없습니다.",
                  style: TextStyle(color: CustomColors.mediumGrey),
                ),
              )
            else
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 10.0),
                child: Text(
                  "추천곡을 불러오는 중...",
                  style: TextStyle(color: CustomColors.mediumGrey),
                ),
              ),
            const SizedBox(height: 24),
            // Top K 결과
            Text(
              "--- Top ${topKResults.length} 유사도 ---",
              style: TextStyle(color: CustomColors.darkGery),
            ),
            const SizedBox(height: 8),
            ...topKResults
                .map(
                  (result) => Text(
                    "${result['singer']}: ${result['similarity']}",
                    style: const TextStyle(fontSize: 15),
                  ),
                )
                .toList(),
          ],
        ),
      ),
    );
  }
}
