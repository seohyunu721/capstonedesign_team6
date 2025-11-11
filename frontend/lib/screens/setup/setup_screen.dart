import 'package:flutter/material.dart';
import '/screens/analysis/analysis_screen.dart';
import '/services/preferences_service.dart';
import '/core/constants/text_styles.dart';
import '/core/theme/colors.dart';

// --- 사용자 정보 입력 화면 ---
class SetupScreen extends StatefulWidget {
  @override
  _SetupScreenState createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  final List<String> _genres = ['발라드', '댄스', 'R&B', '록', '랩/힙합', '팝'];
  String? _selectedGender;
  String? _selectedGenre;
  RangeValues _selectedYears = const RangeValues(2010, 2025);
  final PreferencesService _prefsService = PreferencesService();

  Future<void> _savePreferences() async {
    if (_selectedGender == null || _selectedGenre == null) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('성별과 선호 장르를 모두 선택해주세요!')));
      return;
    }

    await _prefsService.savePreferences(
      gender: _selectedGender!,
      genre: _selectedGenre!,
      startYear: _selectedYears.start,
      endYear: _selectedYears.end,
    );

    // 설정 완료 후 AnalysisScreen으로 이동
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (context) => AnalysisScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Vocalize 맞춤 설정")),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                "당신을 위한 더 정확한 추천",
                style: AppTextStyles.headlineSmallBold(context),
              ),
              const SizedBox(height: 30),
              // --- 성별 선택 ---
              Text("추천받을 가수의 성별", style: AppTextStyles.titleLarge(context)),
              const SizedBox(height: 10),
              ToggleButtons(
                isSelected: [
                  _selectedGender == 'male',
                  _selectedGender == 'female',
                  _selectedGender == 'none',
                ],
                onPressed: (index) {
                  setState(() {
                    if (index == 0)
                      _selectedGender = 'male';
                    else if (index == 1)
                      _selectedGender = 'female';
                    else
                      _selectedGender = 'none';
                  });
                },
                borderRadius: BorderRadius.circular(10),
                fillColor: CustomColors.deepPurple.withOpacity(0.1),
                selectedColor: CustomColors.deepPurple,
                constraints: BoxConstraints(
                  minHeight: 40.0,
                  minWidth: (MediaQuery.of(context).size.width - 56) / 3,
                ),
                children: const [
                  Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16),
                    child: Text("남자"),
                  ),
                  Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16),
                    child: Text("여자"),
                  ),
                  Padding(
                    padding: EdgeInsets.symmetric(horizontal: 16),
                    child: Text("상관없음"),
                  ),
                ],
              ),
              const SizedBox(height: 30),
              // --- 장르 선택 ---
              Text("선호하는 장르", style: AppTextStyles.titleLarge(context)),
              const SizedBox(height: 10),
              Wrap(
                spacing: 8.0,
                runSpacing: 4.0,
                children: _genres
                    .map(
                      (genre) => ChoiceChip(
                        label: Text(genre),
                        selected: _selectedGenre == genre,
                        onSelected: (selected) {
                          setState(() {
                            _selectedGenre = genre;
                          });
                        },
                        selectedColor: CustomColors.primaryPurple[400],
                        labelStyle: TextStyle(
                          color: _selectedGenre == genre
                              ? Colors.white
                              : Colors.black,
                        ),
                      ),
                    )
                    .toList(),
              ),
              const SizedBox(height: 30),
              // --- 년도 선택 ---
              Text("선호하는 년도", style: AppTextStyles.titleLarge(context)),
              RangeSlider(
                values: _selectedYears,
                min: 1980,
                max: 2025,
                divisions: (2025 - 1980),
                labels: RangeLabels(
                  _selectedYears.start.round().toString(),
                  _selectedYears.end.round().toString(),
                ),
                onChanged: (RangeValues values) {
                  setState(() {
                    _selectedYears = values;
                  });
                },
              ),
              const SizedBox(height: 50),
              // --- 버튼 ---
              ElevatedButton(
                onPressed: _savePreferences,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 15),
                  textStyle: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                child: const Text("추천 시작하기"),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
