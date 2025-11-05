import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';
import 'package:cached_network_image/cached_network_image.dart'; //
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import 'dart:typed_data';
import 'dart:async';

import 'dart:io'; // 모바일 파일 처리를 위해 필요
import 'package:flutter_sound/flutter_sound.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:path_provider/path_provider.dart';
import 'package:flutter/foundation.dart'; // kIsWeb을 사용하기 위해 필요

// --- 앱 시작점 ---
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
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
          titleTextStyle: TextStyle(
            color: Colors.black,
            fontSize: 18,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
      home: isSetupComplete ? AnalysisScreen() : SetupScreen(),
    );
  }
}

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

  Future<void> _savePreferences() async {
    if (_selectedGender == null || _selectedGenre == null) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('성별과 선호 장르를 모두 선택해주세요!')));
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
              Text(
                "당신을 위한 더 정확한 추천",
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 30),
              Text(
                "추천받을 가수의 성별",
                style: Theme.of(context).textTheme.titleLarge,
              ),
              SizedBox(height: 10),
              ToggleButtons(
                isSelected: [
                  _selectedGender == 'male',
                  _selectedGender == 'female',
                  _selectedGender == 'none',
                ],
                onPressed: (index) {
                  setState(() {
                    if (index == 0) _selectedGender = 'male';
                    else if (index == 1) _selectedGender = 'female';
                    else _selectedGender = 'none';
                  });
                },
                borderRadius: BorderRadius.circular(10),
                fillColor: Colors.deepPurple.withOpacity(0.1),
                selectedColor: Colors.deepPurple,
                constraints: BoxConstraints(
                  minHeight: 40.0,
                  minWidth: (MediaQuery.of(context).size.width - 56) / 3,
                ),
                children: [
                  Padding(padding: EdgeInsets.symmetric(horizontal: 16), child: Text("남자")),
                  Padding(padding: EdgeInsets.symmetric(horizontal: 16), child: Text("여자")),
                  Padding(padding: EdgeInsets.symmetric(horizontal: 16), child: Text("상관없음")),
                ],
              ),
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

// --- 음성 분석 메인 화면 ---
class AnalysisScreen extends StatefulWidget {
  @override
  _AnalysisScreenState createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  // --- 상태 변수 ---
  final String apiUrl = kIsWeb ? "http://127.0.0.1:8000" : (Platform.isAndroid ? "http://10.0.2.2:8000" : "http://127.0.0.1:8000");
  final FlutterSoundRecorder _recorder = FlutterSoundRecorder();
  bool _isRecorderInitialized = false;
  bool _isRecording = false;

  String? _fileName;
  Uint8List? _fileBytes;
  String _tempRecordingPath = "";

  bool _isLoading = false;
  Map<String, dynamic>? _analysisResult;
  String _statusMessage = "분석할 음성 파일을 선택해주세요.";
  bool _isPickerOpening = false; // 이중 클릭 방지

  // --- 생명주기 함수 ---
  @override
  void initState() {
    super.initState();
    _initRecorder();
  }

  @override
  void dispose() {
    _recorder.closeRecorder();
    super.dispose();
  }

  // --- 핵심 로직 함수 ---

  Future<void> _initRecorder() async {
    await _recorder.openRecorder();
    var status = await Permission.microphone.request();
    if (status.isGranted) {
      setState(() => _isRecorderInitialized = true);
    } else {
      setState(() => _statusMessage = "마이크 권한이 필요합니다.");
    }
  }

  Future<void> _pickAndAnalyze() async {
    // 이중 클릭 방지
    if (_isPickerOpening) return;
    setState(() => _isPickerOpening = true);

    FilePickerResult? result;
    try {
      result = await FilePicker.platform.pickFiles(type: FileType.audio);
    } catch (e) {
      print("파일 피커 오류: $e");
    } finally {
      setState(() => _isPickerOpening = false);
    }

    if (result != null) {
      String fileName = result.files.single.name;
      Uint8List? fileBytes; // 최종 파일 데이터를 담을 변수

      // --- ⭐️ 웹/모바일 호환 로직 ⭐️ ---
      if (kIsWeb) {
        // 1. 웹(Web) 환경일 경우
        print("[Debug] 웹 플랫폼: bytes에서 직접 파일 읽기");
        fileBytes = result.files.single.bytes;
      } else {
        // 2. 모바일(Mobile) 환경일 경우
        print("[Debug] 모바일 플랫폼: path에서 파일 읽기");
        String? path = result.files.single.path;
        if (path != null) {
          fileBytes = await File(path).readAsBytes();
        }
      }
      // ---------------------------------

      // 파일 데이터를 성공적으로 가져왔는지 확인
      if (fileBytes != null) {
        setState(() {
          _fileName = fileName;
          _fileBytes = fileBytes;
          _statusMessage = "파일 선택 완료: $_fileName";
          _analysisResult = null;
        });
        _analyzeVoice(); // 분석 시작
      } else {
        print("파일 데이터를 확보하지 못했습니다.");
      }
    } else {
      print("파일 선택이 취소되었습니다.");
    }
  }

  Future<void> _startRecording() async {
    if (!_isRecorderInitialized || kIsWeb) {
      setState(() => _statusMessage = kIsWeb ? "웹에서는 녹음을 지원하지 않습니다." : "마이크 권한이 필요합니다.");
      return;
    }

    Directory tempDir = await getTemporaryDirectory();
    _tempRecordingPath = '${tempDir.path}/voice_${DateTime.now().millisecondsSinceEpoch}.wav';

    try {
      await _recorder.startRecorder(
        toFile: _tempRecordingPath,
        codec: Codec.pcm16WAV,
      );
      setState(() {
        _isRecording = true;
        _statusMessage = "🎙️ 녹음 중...";
        _fileName = _tempRecordingPath.split('/').last;
      });
    } catch (e) {
      setState(() => _statusMessage = "녹음 시작 실패: $e");
    }
  }

  Future<void> _stopRecordingAndAnalyze() async {
    if (!_isRecorderInitialized) return;

    try {
      final path = await _recorder.stopRecorder();
      setState(() => _isRecording = false);

      if (path != null) {
        final fileBytes = await File(path).readAsBytes();
        setState(() {
          _fileBytes = fileBytes;
          _fileName = path.split('/').last;
          _statusMessage = "녹음 완료! 분석을 시작합니다.";
        });
        await _analyzeVoice(); // [수정] 메인 분석 함수 호출
      }
    } catch (e) {
      setState(() => _statusMessage = "녹음 중지 실패: $e");
    }
  }

  Future<void> _analyzeVoice() async {
    if (_fileBytes == null) return;
    setState(() {
      _isLoading = true;
      _statusMessage = "음성을 분석 중입니다...";
    });

    try {
      final prefs = await SharedPreferences.getInstance();
      final String userGender = prefs.getString('gender') ?? 'none';
      final String userGenre = prefs.getString('genre') ?? 'none';
      final double startYear = prefs.getDouble('startYear') ?? 1980.0;
      final double endYear = prefs.getDouble('endYear') ?? 2025.0;

      var uri = Uri.parse("$apiUrl/analyze");
      var request = http.MultipartRequest('POST', uri);

      request.fields['gender'] = userGender;
      request.fields['genre'] = userGenre;
      request.fields['start_year'] = startYear.round().toString();
      request.fields['end_year'] = endYear.round().toString();

      request.files.add(
        http.MultipartFile.fromBytes(
          'voice_file', // [수정] 백엔드와 키 이름 일치
          _fileBytes!,
          filename: _fileName!,
        ),
      );
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

  // --- UI 위젯들 ---
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
              if (!_isLoading) _buildUploadWidget(),
              SizedBox(height: 40),
              if (_isLoading) _buildLoadingWidget(),
              if (!_isLoading && _analysisResult != null) _buildResultWidget(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildUploadWidget() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        GestureDetector(
          onTap: (_isLoading || _isPickerOpening) ? null : _pickAndAnalyze,
          child: Column(
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
        ),
        SizedBox(height: 30),
        ElevatedButton.icon(
          onPressed: _isRecording ? _stopRecordingAndAnalyze : _startRecording,
          icon: Icon(_isRecording ? Icons.stop : Icons.mic),
          label: Text(_isRecording ? "녹음 중지" : "음성 녹음하기"),
        ),
        if (_isRecording)
          Padding(
            padding: const EdgeInsets.only(top: 8.0),
            child: Text("🎙️ 녹음 중입니다...", style: TextStyle(color: Colors.redAccent)),
          ),
      ],
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
              // [수정] 온라인 이미지 대신 로컬 애셋 이미지 사용
              backgroundImage: AssetImage(
                'assets/singers/${bestMatch.toLowerCase().replaceAll(" ", "")}.jpg',
              ),
              onBackgroundImageError: (e, s) => print('이미지 로드 실패: $e'),
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