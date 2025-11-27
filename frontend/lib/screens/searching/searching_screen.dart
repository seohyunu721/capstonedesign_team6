import 'package:flutter/material.dart';
import '/services/result_storage_service.dart';
import '/core/theme/colors.dart';

// ⭐️ StatefulWidget으로 변경 ⭐️
class SearchingScreen extends StatefulWidget {
  const SearchingScreen({super.key});

  @override
  State<SearchingScreen> createState() => _SearchingScreenState();
}

// ⭐️ State 클래스 구현 ⭐️
class _SearchingScreenState extends State<SearchingScreen> {
  // ResultStorageService 인스턴스를 State에 보관
  final ResultStorageService _resultStorageService = ResultStorageService();

  // FutureBuilder의 future를 관리하기 위한 Key
  Key _futureKey = UniqueKey();

  // ResultCard에서 사용하던 정보 표시 타일 위젯
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

  // ⭐️ 핵심 함수: 분석 결과 삭제 및 화면 새로고침 ⭐️
  Future<void> _clearResultAndRefresh(BuildContext context) async {
    await _resultStorageService.clearAnalysisResult();

    // 사용자에게 피드백 제공
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('✅ 분석 결과가 성공적으로 삭제되었습니다.')));

    // FutureBuilder를 강제로 새로고침하여 빈 화면을 표시
    setState(() {
      _futureKey = UniqueKey(); // Key를 변경하여 FutureBuilder를 다시 빌드하도록 함
    });
  }

  @override
  Widget build(BuildContext context) {
    // final ResultStorageService resultStorageService = ResultStorageService(); // State 변수로 이동

    return Scaffold(
      appBar: AppBar(
        title: const Text("분석 결과 카드"),
        backgroundColor: CustomColors.deepPurple,
        foregroundColor: Colors.white,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "🔍 저장된 분석 리포트",
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: CustomColors.deepPurple,
              ),
            ),
            const SizedBox(height: 10),

            // FutureBuilder를 사용하여 비동기 데이터 로드
            FutureBuilder<Map<String, dynamic>?>(
              // ⭐️ Key와 State 변수 사용 ⭐️
              key: _futureKey,
              future: _resultStorageService.loadAnalysisResult(),
              builder: (context, snapshot) {
                // ... (기존 로딩, 오류, 데이터 있음, 데이터 없음 로직 유지) ...

                // 로딩 중
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(
                    child: Padding(
                      padding: EdgeInsets.all(40.0),
                      child: CircularProgressIndicator(),
                    ),
                  );
                }
                // 오류 발생
                else if (snapshot.hasError) {
                  return const Text(
                    "결과 로드 중 오류가 발생했습니다.",
                    style: TextStyle(color: CustomColors.accentRed),
                  );
                }
                // 데이터 로드 성공 (결과가 있을 경우)
                else if (snapshot.data != null) {
                  final analysisResult = snapshot.data!;
                  // ... (기존 변수 초기화 로직 유지) ...
                  final String bestMatch =
                      analysisResult['best_match'] as String? ?? 'N/A';
                  final String userVocalRange =
                      analysisResult['user_vocal_range'] as String? ?? '분석 불가';
                  final List<dynamic> recommended_songs =
                      analysisResult['recommended_songs'] is List
                      ? analysisResult['recommended_songs']
                      : [];
                  final List<dynamic> topKResults =
                      analysisResult['top_k_results'] is List
                      ? analysisResult['top_k_results']
                      : [];

                  return Card(
                    // ... (기존 Card 및 결과 표시 UI 로직 유지) ...
                    margin: const EdgeInsets.symmetric(vertical: 16),
                    elevation: 8,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(15),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(20.0),
                      child: Column(
                        children: [
                          Text(
                            "📊 나의 목소리 리포트",
                            style: Theme.of(context).textTheme.headlineSmall
                                ?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          const Divider(height: 30, thickness: 1),
                          // 이미지 (ResultCard 로직)
                          CircleAvatar(
                            radius: 50,
                            backgroundImage: AssetImage(
                              'assets/singers/${bestMatch.toLowerCase().replaceAll(" ", "")}.jpg',
                            ),
                            onBackgroundImageError: (e, s) {
                              print('이미지 로드 실패: $e');
                            },
                            backgroundColor: CustomColors.lightGrey,
                          ),
                          const SizedBox(height: 12),
                          const Text(
                            "가장 유사한 가수는...",
                            style: TextStyle(fontSize: 16),
                          ),
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
                          _buildInfoTile(
                            Icons.mic_none_outlined,
                            "나의 음역대",
                            userVocalRange,
                          ),
                          const SizedBox(height: 24),
                          // 추천곡 목록
                          const Align(
                            alignment: Alignment.centerLeft,
                            child: Text(
                              "🎶 추천곡 목록",
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
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
                                        color: CustomColors.primaryPurple,
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
                              padding: const EdgeInsets.symmetric(
                                vertical: 10.0,
                              ),
                              child: Text(
                                "당신의 음역대에 맞는 추천곡이 없습니다.",
                                style: TextStyle(
                                  color: CustomColors.mediumGrey,
                                ),
                              ),
                            ),
                          const SizedBox(height: 24),
                          // Top K 결과
                          Text(
                            "--- Top ${topKResults.length} 유사도 ---",
                            style: TextStyle(color: CustomColors.darkGrey),
                          ),
                          const SizedBox(height: 8),
                          ...topKResults.map((result) {
                            final Map<String, dynamic> resultData =
                                result as Map<String, dynamic>;
                            final singer =
                                resultData['singer'] as String? ?? 'N/A';
                            // final similarityValue =
                            //     resultData['similarity'] is double
                            //     ? resultData['similarity'] as double
                            //     : (resultData['similarity'] as int?)
                            //               ?.toDouble() ?? 0.0;

                            final dynamic similarityRaw =
                                resultData['similarity'];
                            double similarityValue = 0.0;

                            if (similarityRaw is double) {
                              similarityValue = similarityRaw;
                            } else if (similarityRaw is int) {
                              similarityValue = similarityRaw.toDouble();
                            } else if (similarityRaw is String) {
                              String cleanedString = similarityRaw
                                  .replaceAll('%', '')
                                  .trim();
                              similarityValue =
                                  double.tryParse(cleanedString) ?? 0.0;
                            }

                            final similarity = similarityValue.toStringAsFixed(
                              2,
                            );
                            return Text(
                              "$singer: $similarity",
                              style: const TextStyle(fontSize: 15),
                            );
                          }).toList(),
                        ],
                      ),
                    ),
                  );
                }
                // 데이터가 없을 경우
                else {
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 40.0),
                    child: Center(
                      child: Text(
                        "저장된 분석 결과가 없습니다.\n'분석' 탭에서 음성 분석을 진행해주세요.",
                        style: TextStyle(color: CustomColors.mediumGrey),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  );
                }
              },
            ),

            const Divider(height: 30, thickness: 1),
            // ⭐️ 새로 추가된 분석 결과 지우기 버튼 ⭐️
            ListTile(
              leading: const Icon(
                Icons.delete_sweep_outlined,
                color: CustomColors.accentRed,
              ),
              title: const Text(
                "분석 결과 지우기",
                style: TextStyle(color: CustomColors.accentRed),
              ),
              onTap: () => _clearResultAndRefresh(context),
            ),

            // ------------------------------------
            const Divider(height: 30, thickness: 1),
            const Text(
              "기타 설정 및 정보",
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            ListTile(
              leading: const Icon(
                Icons.info_outline,
                color: CustomColors.mediumGrey,
              ),
              title: const Text("앱 정보"),
              onTap: () {},
            ),
          ],
        ),
      ),
    );
  }
}
