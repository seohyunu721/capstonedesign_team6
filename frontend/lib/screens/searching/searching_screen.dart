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

                      // 결과 맵에서 요약 정보를 추출합니다. (키 이름은 실제 데이터에 맞춰 수정하세요!)
                      final timestamp = result['timestamp'] ?? '일시 미상';
                      final score =
                          result['score']?.toString() ?? 'N/A'; // 점수 정보
                      return Padding(
                        padding: const EdgeInsets.only(bottom: 8.0),
                        child: Card(
                          // 각 항목을 카드로 감싸 박스 느낌 강조
                          elevation: 2,
                          child: ExpansionTile(
                            // 접혀 있을 때 보이는 제목 (몇 번째 분석 결과인지 표시)
                            title: Text(
                              '분석 결과 #${index + 1}',
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            // 접혀 있을 때 보이는 부제목 (요약 정보)
                            subtitle: Text('분석 일시: $timestamp, 종합 점수: $score점'),

                            // 박스를 눌렀을 때 펼쳐지는 내용 (상세 ResultCard 포함)
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
