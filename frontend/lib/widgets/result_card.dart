import 'package:flutter/material.dart';
import '/core/theme/colors.dart';
import 'package:url_launcher/url_launcher.dart';
import 'dart:io' show Platform; // 추가

class ResultCard extends StatefulWidget {
  final Map<String, dynamic> analysisResult;

  const ResultCard({Key? key, required this.analysisResult}) : super(key: key);

  @override
  State<ResultCard> createState() => _ResultCardState();
}

class _ResultCardState extends State<ResultCard> {
  // note 문자열 -> midi 변환
  int? _noteToMidi(String? note) {
    if (note == null) return null;
    final RegExp regex = RegExp(r'^([A-Ga-g])([#♯b♭]?)(\d)$');
    final match = regex.firstMatch(note.replaceAll('♯', '#').replaceAll('♭', 'b'));
    if (match == null) return null;
    const scale = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11};
    int octave = int.parse(match.group(3)!);
    int base = scale[match.group(1)!.toUpperCase()]!;
    String acc = match.group(2) ?? "";
    if (acc.contains('#')) base += 1;
    if (acc.contains('b')) base -= 1;
    return base + (octave + 1) * 12;
  }

  // 곡과 사용자의 음역대 겹침 점수 계산(0에 가까울수록 많이 겹침)
  int _rangeMatchScore(Map<String, dynamic> song, int userLowMidi, int userHighMidi) {
    int? low = _noteToMidi(song['lowest_note']?.toString());
    int? high = _noteToMidi(song['highest_note']?.toString());
    if (low == null || high == null) return 100000; // 음역대 정보 없는 곡은 맨 뒤
    // 음역대가 겹치면 거리 0
    bool overlap = userHighMidi >= low && userLowMidi <= high;
    if (overlap) return 0;
    // 중심 거리 계산
    int songMid = (low + high) ~/ 2;
    int userMid = (userLowMidi + userHighMidi) ~/ 2;
    return (songMid - userMid).abs();
  }

  void _openYouTubeRecommendationSheet(
    BuildContext context,
    List<Map<String, dynamic>> sections,
    String defaultSinger,
  ) {
    final tabSections = sections
        .map((section) => {
              'singer': section['singer'] ?? defaultSinger,
              'songs': (section['songs'] as List?)
                      ?.whereType<Map<String, dynamic>>()
                      .toList() ??
                  const <Map<String, dynamic>>[],
              'rank': section['rank'] ?? 0,
            })
        .where((section) => section['songs'].isNotEmpty)
        .toList();

    if (tabSections.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('표시할 YouTube 추천곡이 없습니다.')),
      );
      return;
    }

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.black.withOpacity(0.9),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) {
        return FractionallySizedBox(
          heightFactor: 0.85,
          child: DefaultTabController(
            length: tabSections.length,
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  child: Container(
                    width: 60,
                    height: 6,
                    decoration: BoxDecoration(
                      color: Colors.white24,
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                ),
                Text(
                  'YouTube 추천곡',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                      ),
                ),
                const SizedBox(height: 12),
                TabBar(
                  isScrollable: true,
                  dividerColor: Colors.white24,
                  labelColor: Colors.white,
                  unselectedLabelColor: Colors.white60,
                  indicatorColor: CustomColors.accentTeal,
                  tabs: tabSections
                      .map(
                        (section) => Tab(
                          text:
                              'Top${section['rank'] ?? ''} ${section['singer']}',
                        ),
                      )
                      .toList(),
                ),
                const SizedBox(height: 8),
                Expanded(
                  child: TabBarView(
                    children: tabSections.map((section) {
                      final singer = section['singer'] as String;
                      final songs =
                          (section['songs'] as List<Map<String, dynamic>>);
                      return _buildSingerTabView(
                        songs,
                        singer,
                        rankLabel: section['rank'] ?? 0,
                      );
                    }).toList(),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Future<void> _openYouTubeSearch(String singer, String songTitle) async {
    String searchQuery = Uri.encodeComponent('$singer $songTitle');
    String youtubeUrl = 'https://www.youtube.com/results?search_query=$searchQuery';
    
    print('🔍 [YouTube] 검색 시도: $youtubeUrl');
    debugPrint('🔍 [YouTube] 검색 시도: $youtubeUrl');
    
    try {
      final uri = Uri.parse(youtubeUrl);
      print('🔍 [YouTube] URI 파싱 완료: $uri');
      
      final canLaunch = await canLaunchUrl(uri);
      print('🔍 [YouTube] canLaunchUrl 결과: $canLaunch');
      
      if (canLaunch) {
        print('🔍 [YouTube] launchUrl 호출 중...');
        final result = await launchUrl(uri, mode: LaunchMode.externalApplication);
        print('✅ [YouTube] 검색 성공: $result');
        debugPrint('✅ [YouTube] 검색 성공');
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('YouTube를 여는 중...')),
          );
        }
      } else {
        print('❌ [YouTube] URL을 실행할 수 없습니다: $youtubeUrl');
        debugPrint('❌ [YouTube] URL을 실행할 수 없습니다: $youtubeUrl');
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('YouTube를 열 수 없습니다. 브라우저나 YouTube 앱이 필요합니다.')),
          );
        }
      }
    } catch (e, stackTrace) {
      print('❌ [YouTube] 검색 오류: $e');
      print('❌ [YouTube] 스택 트레이스: $stackTrace');
      debugPrint('❌ [YouTube] 검색 오류: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('오류 발생: $e')),
        );
      }
    }
  }

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

  Widget _buildYouTubePlayer(Map<String, dynamic> songInfo, String defaultSinger) {
    String songTitle = songInfo['title'] ?? '';
    String? videoId = songInfo['youtube_video_id'];
    String? youtubeUrl = songInfo['youtube_url'];
    // songInfo에 singer가 있으면 사용, 없으면 defaultSinger 사용
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
                print('🎵 [추천곡] 곡 정보 클릭됨: $songTitle - $singer');
                if (youtubeUrl != null) {
                  _openYouTubeUrl(youtubeUrl);
                } else {
                  _openYouTubeSearch(singer, songTitle);
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
                            Icon(Icons.open_in_new, size: 16, color: CustomColors.deepPurple),
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
                  print('🎵 [YouTube] 버튼 클릭됨!');
                  print('🎵 [YouTube] youtubeUrl: $youtubeUrl');
                  print('🎵 [YouTube] singer: $singer, songTitle: $songTitle');
                  debugPrint('🎵 [YouTube] 버튼 클릭됨');
                  
                  if (youtubeUrl != null) {
                    print('🎵 [YouTube] _openYouTubeUrl 호출');
                    _openYouTubeUrl(youtubeUrl);
                  } else {
                    print('🎵 [YouTube] _openYouTubeSearch 호출');
                    _openYouTubeSearch(singer, songTitle);
                  }
                },
                icon: const Icon(Icons.play_arrow),
                label: Text(videoId != null ? 'YouTube에서 전체 보기' : 'YouTube에서 검색'),
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
    final imageUrl =
        videoId != null ? 'https://img.youtube.com/vi/$videoId/hqdefault.jpg' : null;

    return GestureDetector(
      onTap: () {
        print('🖼️ [YouTube] 비디오 프리뷰 클릭됨!');
        print('🖼️ [YouTube] youtubeUrl: $youtubeUrl');
        debugPrint('🖼️ [YouTube] 비디오 프리뷰 클릭됨');
        
        if (youtubeUrl != null) {
          print('🖼️ [YouTube] _openYouTubeUrl 호출');
          _openYouTubeUrl(youtubeUrl);
        } else {
          print('🖼️ [YouTube] _openYouTubeSearch 호출');
          _openYouTubeSearch(singer, songTitle);
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
                  errorBuilder: (_, __, ___) => Container(color: Colors.black45),
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

  Widget _buildSingerTabView(
      List<Map<String, dynamic>> songs, String singer,
      {int rankLabel = 0}) {
    if (songs.isEmpty) {
      return const Center(
        child: Text(
          '표시할 곡이 없습니다.',
          style: TextStyle(color: Colors.white70),
        ),
      );
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 12, 20, 4),
          child: Align(
            alignment: Alignment.centerLeft,
            child: Text(
              'Top${rankLabel > 0 ? rankLabel : ''} • $singer 전곡',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.symmetric(vertical: 8),
            itemCount: songs.length,
            separatorBuilder: (_, __) => const SizedBox(height: 6),
            itemBuilder: (_, index) {
              return _buildYouTubeListTile(
                songs[index],
                singer,
                index + 1,
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildYouTubeListTile(
      Map<String, dynamic> songInfo, String defaultSinger, int rank) {
    final songTitle = songInfo['title'] ?? '';
    final videoId = songInfo['youtube_video_id'] as String?;
    final youtubeUrl = songInfo['youtube_url'] as String?;
    final singer = songInfo['singer'] ?? defaultSinger;
    final displayTitle =
        songInfo['youtube_title'] ?? songInfo['title'] ?? '미확인 곡';
    final range = songInfo['range'] ??
        ((songInfo['lowest_note'] != null && songInfo['highest_note'] != null)
            ? '${songInfo['lowest_note']} ~ ${songInfo['highest_note']}'
            : null);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 10),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.06),
          borderRadius: BorderRadius.circular(20),
        ),
        child: ListTile(
          contentPadding: const EdgeInsets.all(12),
          leading: ClipRRect(
            borderRadius: BorderRadius.circular(14),
            child: videoId != null
                ? Image.network(
                    'https://img.youtube.com/vi/$videoId/hqdefault.jpg',
                    width: 70,
                    height: 70,
                    fit: BoxFit.cover,
                  )
                : Container(
                    width: 70,
                    height: 70,
                    color: Colors.white10,
                    child: const Icon(Icons.music_note, color: Colors.white54),
                  ),
          ),
          title: Text(
            displayTitle,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 16,
              fontWeight: FontWeight.bold,
            ),
          ),
          subtitle: Padding(
            padding: const EdgeInsets.only(top: 4.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$singer • 추천순위 $rank',
                  style: const TextStyle(color: Colors.white70),
                ),
                if (range != null)
                  Text(
                    '음역대 $range',
                    style: const TextStyle(color: Colors.white54, fontSize: 12),
                  ),
              ],
            ),
          ),
          trailing: IconButton(
            icon: const Icon(Icons.open_in_new, color: Colors.white),
            onPressed: () {
              print('📋 [YouTube] 리스트 아이템 클릭됨!');
              print('📋 [YouTube] youtubeUrl: $youtubeUrl');
              debugPrint('📋 [YouTube] 리스트 아이템 클릭됨');
              
              if (youtubeUrl != null) {
                print('📋 [YouTube] _openYouTubeUrl 호출');
                _openYouTubeUrl(youtubeUrl);
              } else {
                print('📋 [YouTube] _openYouTubeSearch 호출');
                _openYouTubeSearch(singer, songTitle);
              }
            },
          ),
        ),
      ),
    );
  }

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
          formattedSongs.sort(
            (a, b) => _rangeMatchScore(a, userLowMidi, userHighMidi)
                .compareTo(_rangeMatchScore(b, userLowMidi, userHighMidi)),
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
          .map((song) => {
                'title': song['title'],
                'singer': song['singer'] ?? defaultSinger,
                'youtube_video_id': song['youtube_video_id'],
                'youtube_url': song['youtube_url'],
                'youtube_title': song['youtube_title'],
              })
          .toList();
      sections.add({
        'singer': defaultSinger,
        'songs': fallbackSongs,
        'rank': rankCounter,
      });
    }

    return sections;
  }

  Future<void> _openYouTubeUrl(String url) async {
    print('🔗 [YouTube] URL 열기 시도: $url');
    debugPrint('🔗 [YouTube] URL 열기 시도: $url');
    
    try {
      final uri = Uri.parse(url);
      print('🔗 [YouTube] URI 파싱 완료: $uri');
      
      final canLaunch = await canLaunchUrl(uri);
      print('🔗 [YouTube] canLaunchUrl 결과: $canLaunch');
      
      if (canLaunch) {
        print('🔗 [YouTube] launchUrl 호출 중...');
        final result = await launchUrl(uri, mode: LaunchMode.externalApplication);
        print('✅ [YouTube] URL 열기 성공: $result');
        debugPrint('✅ [YouTube] URL 열기 성공');
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('YouTube를 여는 중...')),
          );
        }
      } else {
        print('❌ [YouTube] URL을 실행할 수 없습니다: $url');
        debugPrint('❌ [YouTube] URL을 실행할 수 없습니다: $url');
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('YouTube를 열 수 없습니다. 브라우저나 YouTube 앱이 필요합니다.')),
          );
        }
      }
    } catch (e, stackTrace) {
      print('❌ [YouTube] URL 열기 오류: $e');
      print('❌ [YouTube] 스택 트레이스: $stackTrace');
      debugPrint('❌ [YouTube] URL 열기 오류: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('오류 발생: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    String bestMatch = widget.analysisResult['best_match'] ?? 'N/A';
    String userVocalRange = widget.analysisResult['user_vocal_range'] ?? '분석 불가';
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
        {'singer': bestMatch, 'songs': matchedSingerSongs}
      ];
    }

    // 사용자 음역대 파싱 (ex: "C3 ~ F4")
    int? userLowMidi, userHighMidi;
    final userVocalRangeStr = userVocalRange.replaceAll(' ', '');
    final parts = userVocalRangeStr.split('~');
    if (parts.length == 2) {
      userLowMidi = _noteToMidi(parts[0]);
      userHighMidi = _noteToMidi(parts[1]);
    }

    // graph URL 처리 (서버가 반환한 절대/상대 URL, AVD 대응)
    final String? rawGraphUrl = widget.analysisResult['pitch_graph_url'] as String?;
    String? graphUrl = rawGraphUrl;
    if (graphUrl != null && Platform.isAndroid) {
      graphUrl = graphUrl.replaceFirst('127.0.0.1', '10.0.2.2').replaceFirst('localhost', '10.0.2.2');
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
            // 이미지 처리
            CircleAvatar(
              radius: 50,
              // [수정] 온라인 이미지 대신 로컬 애셋 이미지 사용 (assets 폴더에 이미지 파일 필요)
              backgroundImage: AssetImage(
                'assets/singers/${bestMatch.toLowerCase().replaceAll(" ", "")}.jpg',
              ),
              onBackgroundImageError: (e, s) => print('이미지 로드 실패: $e'),
              backgroundColor: CustomColors.lightGrey,
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
                    const Text("📊 음역대 정밀 분석", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
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
                              child: Text("그래프를 불러올 수 없습니다.", textAlign: TextAlign.center),
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
                      ? () => _openYouTubeRecommendationSheet(
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
                  return Card(
                    margin: const EdgeInsets.symmetric(vertical: 8.0),
                    child: ListTile(
                      leading: Icon(Icons.music_note, color: CustomColors.deepPurple),
                      title: Text(songTitle),
                      subtitle: Text(bestMatch),
                      trailing: Icon(Icons.open_in_new, color: CustomColors.deepPurple),
                      onTap: () {
                        print('🎵 [추천곡] 클릭됨: $songTitle - $bestMatch');
                        _openYouTubeSearch(bestMatch, songTitle);
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
              style: TextStyle(color: CustomColors.darkGrey),
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
