import 'package:flutter/material.dart';
import '/services/result_storage_service.dart';
import '/core/theme/colors.dart';
import 'dart:io' show Platform;
import '/widgets/result_card.dart'; // 추가: ResultCard import

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
                  // ResultCard로 통합
                  return ResultCard(analysisResult: analysisResult);
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