import 'package:flutter/material.dart';
import '/services/result_storage_service.dart';
import '/core/theme/colors.dart';
import 'dart:io' show Platform; // 이거 땜에 웹에서 실행 하면 오류 뜨기에 앱으로 만 실행
import '/widgets/result_card.dart'; // 추가: ResultCard import

class SearchingScreen extends StatefulWidget {
  const SearchingScreen({super.key});

  @override
  State<SearchingScreen> createState() => _SearchingScreenState();
}

class _SearchingScreenState extends State<SearchingScreen> {
  // ResultStorageService 인스턴스를 State에 보관
  final ResultStorageService _resultStorageService = ResultStorageService();

  // FutureBuilder의 future를 관리하기 위한 Key
  Key _futureKey = UniqueKey();

  Future<void> _clearResultAndRefresh(BuildContext context) async {
    await _resultStorageService.clearAnalysisResults();

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
            FutureBuilder<List<Map<String, dynamic>>>(
              // ⭐️ Key와 State 변수 사용 ⭐️
              key: _futureKey,
              future: _resultStorageService.loadAnalysisResults(),
              builder: (context, snapshot) {
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
                    "결과 로드 중 오류가 발생했습니다. ",
                    style: TextStyle(color: CustomColors.accentRed),
                  );
                }
                // 데이터 로드 성공 (결과가 있을 경우)
                else if (snapshot.hasData && snapshot.data!.isNotEmpty) {
                  final analysisResultList = snapshot.data!;
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: analysisResultList.asMap().entries.map((entry) {
                      final index = entry.key;
                      final result = entry.value;

                      final fileName = result['fileName'] ?? '파일 이름 미상';
                      final topKResults =
                          result['top_k_results'] as List<dynamic>? ?? [];

                      String topSingerInfo = '유사 가수: 정보 없음';

                      if (topKResults.isNotEmpty &&
                          topKResults.first is Map<String, dynamic>) {
                        final topResult =
                            topKResults.first as Map<String, dynamic>;
                        final singerName = topResult['singer'] ?? '미상';

                        // 유사도 임시 제거
                        // final similarityValue = topResult['similarity'];
                        // String similarityScore;

                        // if (similarityValue is num) {
                        //   similarityScore = similarityValue.toStringAsFixed(4);
                        // } else if (similarityValue is String) {
                        //   final parsedValue = double.tryParse(similarityValue);
                        //   similarityScore = parsedValue != null
                        //       ? parsedValue.toStringAsFixed(4)
                        //       : 'N/A';
                        // } else {
                        //   similarityScore = 'N/A';
                        // }

                        topSingerInfo = '$singerName';
                      }
                      final subtitleText =
                          '파일: $fileName | 유사 가수: $topSingerInfo';

                      return Padding(
                        padding: const EdgeInsets.only(bottom: 8.0),
                        child: Card(
                          elevation: 2,
                          child: ExpansionTile(
                            title: Text(
                              '분석 결과 #${index + 1}',
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            subtitle: Text(
                              subtitleText,
                              style: const TextStyle(fontSize: 12),
                            ),
                            children: [
                              Divider(
                                height: 1,
                                thickness: 1,
                                color: CustomColors.lightGrey,
                              ),
                              Padding(
                                padding: const EdgeInsets.all(16.0),
                                // ⭐️ ResultCard를 상세 내용으로 표시 ⭐️
                                child: ResultCard(analysisResult: result),
                              ),
                            ],
                          ),
                        ),
                      );
                    }).toList(),
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
          ],
        ),
      ),
    );
  }
}
