// widgets/youtube_recommendation_sheet.dart

import 'package:flutter/material.dart';
// 경로에 맞게 수정하세요.
import '/core/theme/colors.dart'; 
import '../utils/analysis_logic.dart'; // 로직 파일 import

class YouTubeRecommendationSheet extends StatelessWidget {
  final List<Map<String, dynamic>> sections;
  final String defaultSinger;

  const YouTubeRecommendationSheet({
    Key? key,
    required this.sections,
    required this.defaultSinger,
  }) : super(key: key);

  // [핵심] 모달을 띄우는 static 메서드
  static void show(
      BuildContext context,
      List<Map<String, dynamic>> sections,
      String defaultSinger,
      ) {
    
    // 노래가 없는 섹션 필터링
    final validSections = sections.where((section) {
      final songs = section['songs'] as List?;
      return songs != null && songs.isNotEmpty;
    }).toList();

    if (validSections.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('표시할 추천곡 데이터가 없습니다.')),
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
        return YouTubeRecommendationSheet(
          sections: validSections,
          defaultSinger: defaultSinger,
        );
      },
    );
  }

  // --- UI 구성 ---

  @override
  Widget build(BuildContext context) {
    return FractionallySizedBox(
      heightFactor: 0.85,
      child: DefaultTabController(
        length: sections.length, 
        child: Column(
          children: [
            // 상단 핸들바 및 타이틀
            Padding(
              padding: const EdgeInsets.only(top: 16.0, bottom: 8.0),
              child: Container(
                width: 40,
                height: 5,
                decoration: BoxDecoration(
                  color: Colors.white30,
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
            ),
            const Text(
              "Top 매칭 가수 추천곡 리스트",
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            
            // 탭 버튼 영역
            Container(
              height: 40,
              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: TabBar(
                isScrollable: true,
                dividerColor: Colors.transparent,
                indicator: BoxDecoration(color: CustomColors.accentTeal, borderRadius: BorderRadius.circular(20)),
                labelColor: Colors.white,
                unselectedLabelColor: Colors.grey[400],
                labelStyle: const TextStyle(fontWeight: FontWeight.bold),
                tabs: sections.map((section) {
                  final rank = section['rank'];
                  final singer = section['singer'];
                  String icon = "#$rank";
                  if (rank == 1) icon = "🥇"; else if (rank == 2) icon = "🥈"; else if (rank == 3) icon = "🥉";
                  return Tab(
                    child: Padding(padding: const EdgeInsets.symmetric(horizontal: 16.0), child: Text('$icon $singer')),
                  );
                }).toList(),
              ),
            ),

            // 탭 내용 (리스트 뷰)
            Expanded(
              child: TabBarView(
                children: sections.map((section) {
                  return _buildSongList(
                    context,
                    section['songs'] as List<Map<String, dynamic>>,
                    section['singer'] as String,
                  );
                }).toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSongList(BuildContext context, List<Map<String, dynamic>> songs, String singer) {
    if (songs.isEmpty) {
       return const Center(child: Text('해당 가수의 추천 곡이 없습니다.', style: TextStyle(color: Colors.white70)));
    }
    
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 20),
      itemCount: songs.length,
      separatorBuilder: (_, __) => const SizedBox(height: 8),
      itemBuilder: (_, index) {
        final song = songs[index];
        return _buildListItem(context, song, singer, index + 1);
      },
    );
  }

  Widget _buildListItem(BuildContext context, Map<String, dynamic> song, String defaultSinger, int rank) {
    final songTitle = song['title'] ?? '';
    final videoId = song['youtube_video_id'] as String?;
    final youtubeUrl = song['youtube_url'] as String?;
    final singer = song['singer'] ?? defaultSinger;
    final displayTitle =
        song['youtube_title'] ?? song['title'] ?? '미확인 곡';
    final range =
        song['range'] ??
        ((song['lowest_note'] != null && song['highest_note'] != null)
            ? '${song['lowest_note']} ~ ${song['highest_note']}'
            : null);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 0.0, vertical: 4),
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
                  '$singer • 적합순위 $rank',
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
              if (youtubeUrl != null) {
                AnalysisLogic.openYouTubeUrl(context, youtubeUrl);
              } else {
                AnalysisLogic.openYouTubeSearch(context, singer, songTitle);
              }
            },
          ),
        ),
      ),
    );
  }
}