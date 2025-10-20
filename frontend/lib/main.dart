import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:shared_preferences/shared_preferences.dart'; 
import 'dart:convert';
import 'dart:typed_data';
import 'dart:async';

void main() async {
  // main 함수에서 async를 사용하기 위한 필수 코드
  WidgetsFlutterBinding.ensureInitialized();
  
  // 휴대폰 저장소에서 사용자 정보 입력 여부 확인
  final prefs = await SharedPreferences.getInstance();
  final bool isSetupComplete = prefs.getBool('isSetupComplete') ?? false;

  runApp(MyApp(isSetupComplete: isSetupComplete));
}

class MyApp extends StatelessWidget {
  
  final bool isSetupComplete;
  const MyApp({Key? key, required this.isSetupComplete}) : super(key: key);
  
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Vocalize: AI 음성 분석기',
      theme: ThemeData(
        scaffoldBackgroundColor: Colors.white,
        primarySwatch: Colors.deepPurple,
        fontFamily: 'Pretendard',
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.white,
          elevation: 1,
          centerTitle: true,
          titleTextStyle: TextStyle(color: Colors.black, fontSize: 18, fontWeight: FontWeight.w600),
        ),
      ),
      home: isSetupComplete ? AnalysisScreen() : SetupScreen(),
    );
  }
}

class SetupScreen extends StatefulWidget {
  @override
  _SetupScreenState createState() => _SetupScreenState();
}

class _SetupScreenState extends State<SetupScreen> {
  final List<String> _genres = ['발라드', '댄스', 'R&B', '록', '랩/힙합', '팝'];
  String? _selectedGender;
  String? _selectedGenre;
  RangeValues _selectedYears = const RangeValues(2010, 2025);

  Future<void> _savePreferences() async {
    if (_selectedGender == null || _selectedGenre == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('성별과 선호 장르를 모두 선택해주세요!')),
      );
      return;
    }

    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isSetupComplete', true);
    await prefs.setString('gender', _selectedGender!);
    await prefs.setString('genre', _selectedGenre!);
    await prefs.setDouble('startYear', _selectedYears.start);
    await prefs.setDouble('endYear', _selectedYears.end);

    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (context) => AnalysisScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Vocalize 맞춤 설정")),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text("당신을 위한 더 정확한 추천", style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
              SizedBox(height: 30),

              Text("추천받을 가수의 성별", style: Theme.of(context).textTheme.titleLarge),
              SizedBox(height: 10),
              ToggleButtons(
                isSelected: [
                  _selectedGender == 'male',
                  _selectedGender == 'female',
                  _selectedGender == 'none', // '상관없음' 상태 추가
                ],
                onPressed: (index) {
                  setState(() {
                    if (index == 0) {
                      _selectedGender = 'male';
                    } else if (index == 1) {
                      _selectedGender = 'female';
                    } else {
                      _selectedGender = 'none'; // '상관없음' 값 설정
                    }
                  });
                },
                borderRadius: BorderRadius.circular(10),
                fillColor: Colors.deepPurple.withOpacity(0.1),
                selectedColor: Colors.deepPurple,
                constraints: BoxConstraints(minHeight: 40.0, minWidth: (MediaQuery.of(context).size.width - 56) / 3), // 3개 버튼에 맞게 너비 조정
                children: [
                  Padding(padding: EdgeInsets.symmetric(horizontal: 16), child: Text("남자")),
                  Padding(padding: EdgeInsets.symmetric(horizontal: 16), child: Text("여자")),
                  Padding(padding: EdgeInsets.symmetric(horizontal: 16), child: Text("상관없음")), // 버튼 추가
                ],
              ),
              // --------------------------

              SizedBox(height: 30),
              
              Text("선호하는 장르", style: Theme.of(context).textTheme.titleLarge),
              SizedBox(height: 10),
              Wrap(
                spacing: 8.0,
                runSpacing: 4.0,
                children: _genres.map((genre) => ChoiceChip(
                  label: Text(genre),
                  selected: _selectedGenre == genre,
                  onSelected: (selected) { setState(() { _selectedGenre = genre; }); },
                  selectedColor: Colors.deepPurple[400],
                  labelStyle: TextStyle(color: _selectedGenre == genre ? Colors.white : Colors.black),
                )).toList(),
              ),
              SizedBox(height: 30),

              Text("선호하는 년도", style: Theme.of(context).textTheme.titleLarge),
              RangeSlider(
                values: _selectedYears,
                min: 1980,
                max: 2025,
                divisions: (2025 - 1980),
                labels: RangeLabels(
                  _selectedYears.start.round().toString(),
                  _selectedYears.end.round().toString(),
                ),
                onChanged: (RangeValues values) { setState(() { _selectedYears = values; }); },
              ),
              SizedBox(height: 50),

              ElevatedButton(
                onPressed: _savePreferences,
                child: Text("추천 시작하기"),
                style: ElevatedButton.styleFrom(
                  padding: EdgeInsets.symmetric(vertical: 15),
                  textStyle: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class AnalysisScreen extends StatefulWidget {
  @override
  _AnalysisScreenState createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  final String apiUrl = "http://127.0.0.1:8000";
  
  String? _fileName;
  Uint8List? _fileBytes;
  bool _isLoading = false;
  Map<String, dynamic>? _analysisResult;
  String _statusMessage = "분석할 음성 파일을 선택해주세요.";

  Future<void> _pickAndAnalyze() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(type: FileType.audio);
    if (result != null && result.files.single.bytes != null) {
      setState(() {
        _fileName = result.files.single.name;
        _fileBytes = result.files.single.bytes;
        _statusMessage = "파일 선택 완료: $_fileName";
        _analysisResult = null;
      });
      _analyzeVoice();
    }
  }

  Future<void> _analyzeVoice() async {
    if (_fileBytes == null) return;
    setState(() {
      _isLoading = true;
      _statusMessage = "음성을 분석 중입니다...";
    });

    try {
      // --- 수정된 부분: 저장된 모든 사용자 정보 불러오기 ---
      final prefs = await SharedPreferences.getInstance();
      final String userGender = prefs.getString('gender') ?? 'none';
      final String userGenre = prefs.getString('genre') ?? 'none';
      final double startYear = prefs.getDouble('startYear') ?? 1980.0;
      final double endYear = prefs.getDouble('endYear') ?? 2025.0;
      // ----------------------------------------------------

      var uri = Uri.parse("$apiUrl/analyze");
      var request = http.MultipartRequest('POST', uri);

      // --- 수정된 부분: 모든 사용자 정보를 백엔드로 전송 ---
      request.fields['gender'] = userGender;
      request.fields['genre'] = userGenre;
      request.fields['start_year'] = startYear.round().toString();
      request.fields['end_year'] = endYear.round().toString();
      // ---------------------------------------------------

      request.files.add(http.MultipartFile.fromBytes('voice_file', _fileBytes!, filename: _fileName!));
      var response = await request.send().timeout(const Duration(seconds: 90));
      
      if (response.statusCode == 200) {
        var responseBody = await response.stream.bytesToString();
        setState(() {
          _analysisResult = jsonDecode(responseBody);
          _statusMessage = "분석 완료!";
        });
      } else {
        var responseBody = await response.stream.bytesToString();
        setState(() {
          _statusMessage = "분석 실패: ${response.statusCode}\n$responseBody";
        });
      }
    } catch (e) {
      setState(() {
        _statusMessage = "오류 발생: $e";
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Vocalize")),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // 로딩 중이 아닐 때만 파일 업로드 UI 표시
              if (!_isLoading) _buildUploadWidget(),
              
              SizedBox(height: 40),

              // 로딩 중일 때 로딩 UI 표시
              if (_isLoading) _buildLoadingWidget(),
              
              // 결과가 있을 때만 결과 카드 표시
              if (!_isLoading && _analysisResult != null) _buildResultWidget(),
            ],
          ),
        ),
      ),
    );
  }

  // --- UI를 구성하는 헬퍼 위젯들 ---

  Widget _buildUploadWidget() {
    return GestureDetector(
      onTap: _pickAndAnalyze,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.upload_file_outlined, size: 100, color: Colors.grey[300]),
          SizedBox(height: 16),
          Text(
            _fileName ?? "노래 업로드하기",
            style: TextStyle(fontSize: 18, color: Colors.grey[600]),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildLoadingWidget() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text("노래 분석 중...", style: Theme.of(context).textTheme.titleLarge),
        SizedBox(height: 20),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 40.0),
          child: LinearProgressIndicator(),
        ),
      ],
    );
  }

  Widget _buildResultWidget() {
    String bestMatch = _analysisResult?['best_match'] ?? 'N/A';
    String userVocalRange = _analysisResult?['user_vocal_range'] ?? '분석 불가';
    List<dynamic> recommendedSongs = _analysisResult?['recommended_songs'] ?? [];
    List<dynamic> topKResults = _analysisResult?['top_k_results'] ?? [];
    
    Map<String, String> singerImageUrls = {
      'iu': 'https://i.scdn.co/image/ab67616100005174f7143ba09d29b200021c27f6',
      'younha': 'https://i.scdn.co/image/ab6761610000517405532578503c5b3b0799b6f1',
      'sungsikyung': 'https://i.scdn.co/image/ab67616100005174a7065e4490f230537487d63b',
      'kwill': 'https://i.scdn.co/image/ab6761610000517406a0c0e5a889f4b16260a996',
    };

    return Card(
      elevation: 6,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            Text("📊 나의 목소리 리포트", style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
            Divider(height: 30, thickness: 1),
            CircleAvatar(
              radius: 50,
              backgroundImage: CachedNetworkImageProvider(singerImageUrls[bestMatch.toLowerCase()] ?? 'https://via.placeholder.com/150'),
              backgroundColor: Colors.grey[200],
            ),
            SizedBox(height: 12),
            Text("가장 유사한 가수는...", style: TextStyle(fontSize: 16)),
            Text(bestMatch, style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: Colors.deepPurple)),
            SizedBox(height: 24),
            _buildInfoTile(Icons.mic_none_outlined, "나의 음역대", userVocalRange),
            SizedBox(height: 24),
            Align(
              alignment: Alignment.centerLeft,
              child: Text("🎶 추천곡 목록", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            ),
            Divider(height: 20),
            if (recommendedSongs.isNotEmpty)
              Column(
                children: recommendedSongs.map((song) => ListTile(
                  leading: Icon(Icons.music_note, color: Colors.deepPurple[300]),
                  title: Text(song.toString(), style: TextStyle(fontSize: 16)),
                )).toList(),
              )
            else
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 10.0),
                child: Text("당신의 음역대에 맞는 추천곡이 없습니다.", style: TextStyle(color: Colors.grey)),
              ),
            SizedBox(height: 24),
            Text("--- Top 3 유사도 ---", style: TextStyle(color: Colors.grey[700])),
            SizedBox(height: 8),
            ...topKResults.map((result) => Text("${result['singer']}: ${result['similarity']}", style: TextStyle(fontSize: 15))).toList(),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoTile(IconData icon, String title, String subtitle) {
    return ListTile(
      leading: Icon(icon, color: Colors.deepPurple),
      title: Text(title, style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
      subtitle: Text(subtitle, style: TextStyle(fontSize: 18)),
    );
  }
}