// import 'package:flutter/material.dart';
// import '/core/theme/colors.dart';

// class ResultCard extends StatelessWidget {
//   final Map<String, dynamic> analysisResult;

//   const ResultCard({Key? key, required this.analysisResult}) : super(key: key);

//   Widget _buildInfoTile(IconData icon, String title, String subtitle) {
//     return ListTile(
//       leading: Icon(icon, color: CustomColors.deepPurple),
//       title: Text(
//         title,
//         style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
//       ),
//       subtitle: Text(subtitle, style: const TextStyle(fontSize: 18)),
//     );
//   }

//   @override
//   Widget build(BuildContext context) {
//     String bestMatch = analysisResult['best_match'] ?? 'N/A';
//     String userVocalRange = analysisResult['user_vocal_range'] ?? '분석 불가';
//     List<dynamic> recommended_songs = analysisResult['recommended_songs'] ?? [];
//     List<dynamic> topKResults = analysisResult['top_k_results'] ?? [];

//     return Card(
//       child: Padding(
//         padding: const EdgeInsets.all(20.0),
//         child: Column(
//           children: [
//             Text(
//               "📊 나의 목소리 리포트",
//               style: Theme.of(
//                 context,
//               ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
//             ),
//             const Divider(height: 30, thickness: 1),
//             // 이미지 처리
//             CircleAvatar(
//               radius: 50,
//               // [수정] 온라인 이미지 대신 로컬 애셋 이미지 사용 (assets 폴더에 이미지 파일 필요)
//               backgroundImage: AssetImage(
//                 'assets/singers/${bestMatch.toLowerCase().replaceAll(" ", "")}.jpg',
//               ),
//               onBackgroundImageError: (e, s) => print('이미지 로드 실패: $e'),
//               backgroundColor: CustomColors.lightGrey,
//             ),
//             const SizedBox(height: 12),
//             const Text("가장 유사한 가수는...", style: TextStyle(fontSize: 16)),
//             Text(
//               bestMatch,
//               style: const TextStyle(
//                 fontSize: 32,
//                 fontWeight: FontWeight.bold,
//                 color: CustomColors.deepPurple,
//               ),
//             ),
//             const SizedBox(height: 24),
//             // 음역대 정보
//             _buildInfoTile(Icons.mic_none_outlined, "나의 음역대", userVocalRange),
//             const SizedBox(height: 24),
//             // 추천곡 목록
//             const Align(
//               alignment: Alignment.centerLeft,
//               child: Text(
//                 "🎶 추천곡 목록",
//                 style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
//               ),
//             ),
//             const Divider(height: 20),
//             if (recommended_songs.isNotEmpty)
//               Column(
//                 children: recommended_songs
//                     .map(
//                       (song) => ListTile(
//                         leading: Icon(
//                           Icons.music_note,
//                           color: CustomColors.primaryPurple[300],
//                         ),
//                         title: Text(
//                           song.toString(),
//                           style: const TextStyle(fontSize: 16),
//                         ),
//                       ),
//                     )
//                     .toList(),
//               )
//             else
//               Padding(
//                 padding: const EdgeInsets.symmetric(vertical: 10.0),
//                 child: Text(
//                   "당신의 음역대에 맞는 추천곡이 없습니다.",
//                   style: TextStyle(color: CustomColors.mediumGrey),
//                 ),
//               ),
//             const SizedBox(height: 24),
//             // Top K 결과
//             Text(
//               "--- Top ${topKResults.length} 유사도 ---",
//               style: TextStyle(color: CustomColors.darkGrey),
//             ),
//             const SizedBox(height: 8),
//             ...topKResults
//                 .map(
//                   (result) => Text(
//                     "${result['singer']}: ${result['similarity']}",
//                     style: const TextStyle(fontSize: 15),
//                   ),
//                 )
//                 .toList(),
//           ],
//         ),
//       ),
//     );
//   }
// }

import 'package:flutter/material.dart';
import '/core/theme/colors.dart';

class ResultCard extends StatelessWidget {
  final Map<String, dynamic> analysisResult;

  const ResultCard({Key? key, required this.analysisResult}) : super(key: key);

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

  @override
  Widget build(BuildContext context) {
    String bestMatch = analysisResult['best_match'] ?? 'N/A';
    String userVocalRange = analysisResult['user_vocal_range'] ?? '분석 불가';
    List<dynamic> recommended_songs = analysisResult['recommended_songs'] ?? [];
    List<dynamic> topKResults = analysisResult['top_k_results'] ?? [];

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 16),
      elevation: 8,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
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
            // 이미지 처리 (로컬 애셋이 없으면 배경색을 표시)
            CircleAvatar(
              radius: 50,
              // [참고] 이 AssetImage 경로는 'assets/singers/' 폴더에 이미지 파일이 실제로 있어야 작동합니다.
              backgroundImage: AssetImage(
                'assets/singers/${bestMatch.toLowerCase().replaceAll(" ", "")}.jpg',
              ),
              onBackgroundImageError: (e, s) {
                // 이미지 로드 실패 시, 에러 콘솔 출력 대신 사용자에게 피드백 제공
                print('이미지 로드 실패: $e');
              },
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
            // 추천곡 목록
            const Align(
              alignment: Alignment.centerLeft,
              child: Text(
                "🎶 추천곡 목록",
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ),
            const Divider(height: 20),
            if (recommended_songs.isNotEmpty)
              Column(
                children: recommended_songs
                    .map(
                      (song) => ListTile(
                        leading: Icon(
                          Icons.music_note,
                          color: CustomColors.primaryPurple[300],
                        ),
                        title: Text(
                          song.toString(),
                          style: const TextStyle(fontSize: 16),
                        ),
                      ),
                    )
                    .toList(),
              )
            else
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 10.0),
                child: Text(
                  "당신의 음역대에 맞는 추천곡이 없습니다.",
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
                    // 숫자를 소수점 둘째 자리까지 표시하도록 수정 (예상 데이터 구조)
                    "${result['singer']}: ${(result['similarity'] as double? ?? 0.0).toStringAsFixed(2)}",
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
