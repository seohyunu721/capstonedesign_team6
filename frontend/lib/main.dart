import 'dart:async';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';
import 'dart:convert';
import 'dart:typed_data';

void main() => runApp(MyApp());

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '음성 분석 앱',
      theme: ThemeData(
        primarySwatch: Colors.deepPurple, // 테마 색상 변경
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      home: AnalysisScreen(),
    );
  }
}

class AnalysisScreen extends StatefulWidget {
  @override
  _AnalysisScreenState createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  // 안드로이드 에뮬레이터: '10.0.2.2', iOS 시뮬레이터/웹: '127.0.0.1'
  final String apiUrl = "http://127.0.0.1:8000";
  
  String? _fileName;
  Uint8List? _fileBytes;

  String _status = "분석할 음성 파일을 선택해주세요.";
  bool _isLoading = false;
  Map<String, dynamic>? _analysisResult;

  Future<void> _pickFile() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.audio,
    );

    if (result != null && result.files.single.bytes != null) {
      setState(() {
        _fileName = result.files.single.name;
        _fileBytes = result.files.single.bytes;
        _status = "파일 선택 완료: $_fileName";
        _analysisResult = null;
      });
    } else {
      print("파일 선택이 취소되었거나 파일 데이터를 읽을 수 없습니다.");
    }
  }

  Future<void> _analyzeVoice() async {
    if (_fileBytes == null) return;

    setState(() {
      _isLoading = true;
      _status = "음성을 분석 중입니다...";
      _analysisResult = null;
    });

    try {
      var uri = Uri.parse("$apiUrl/analyze");
      var request = http.MultipartRequest('POST', uri);
      
      request.files.add(
        http.MultipartFile.fromBytes(
          'voice_file', 
          _fileBytes!, 
          filename: _fileName!
        ),
      );

      print(">>> [Flutter] 1. 백엔드로 분석 요청을 보냅니다...");
      // 60초 타임아웃 설정
      var response = await request.send().timeout(const Duration(seconds: 60));
      
      print(">>> [Flutter] 2. 서버로부터 응답을 받았습니다. 상태 코드: ${response.statusCode}");
      if (response.statusCode == 200) {
        var responseBody = await response.stream.bytesToString();
        setState(() {
          _analysisResult = jsonDecode(responseBody);
          _status = "분석 완료!";
        });
      } else {
        var responseBody = await response.stream.bytesToString();
        setState(() {
          _status = "분석 실패: ${response.statusCode}\n$responseBody";
        });
      }
    } on TimeoutException catch (e) {
      print(">>> [Flutter] 오류: 요청 시간 초과");
      setState(() {
        _status = "오류: 서버가 응답하지 않습니다 (타임아웃). 백엔드 서버를 확인해주세요.";
      });
    } catch (e) {
      print(">>> [Flutter] 오류: $e");
      setState(() {
        _status = "오류 발생: $e";
      });
    } finally {
      print(">>> [Flutter] 3. 분석 프로세스를 종료합니다.");
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text("Vocalize: AI 음성 분석기")),
      body: Center(
        child: SingleChildScrollView( // 결과가 길어질 수 있으므로 스크롤 추가
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton.icon(
                  icon: Icon(Icons.audio_file_outlined),
                  label: Text("음성 파일 선택"),
                  onPressed: _pickFile,
                  style: ElevatedButton.styleFrom(
                    padding: EdgeInsets.symmetric(horizontal: 30, vertical: 15),
                    textStyle: TextStyle(fontSize: 16),
                  ),
                ),
                SizedBox(height: 20),
                Text(_status, textAlign: TextAlign.center),
                SizedBox(height: 20),
                ElevatedButton.icon(
                  icon: Icon(Icons.analytics_outlined),
                  label: Text("분석 시작하기"),
                  onPressed: _fileBytes == null || _isLoading ? null : _analyzeVoice,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green,
                    padding: EdgeInsets.symmetric(horizontal: 30, vertical: 15),
                    textStyle: TextStyle(fontSize: 16),
                  ),
                ),
                SizedBox(height: 40),
                if (_isLoading)
                  CircularProgressIndicator()
                else if (_analysisResult != null)
                  _buildResultWidget()
              ],
            ),
          ),
        ),
      ),
    );
  }

  // --- 결과 표시 위젯 수정 ---
  Widget _buildResultWidget() {
    // 백엔드에서 보낸 새로운 필드들을 파싱
    String bestMatch = _analysisResult?['best_match'] ?? 'N/A';
    String userVocalRange = _analysisResult?['user_vocal_range'] ?? '분석 불가';
    List<dynamic> recommendedSongs = _analysisResult?['recommended_songs'] ?? [];
    List<dynamic> topKResults = _analysisResult?['top_k_results'] ?? [];
    
    return Card(
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text("📊 나의 목소리 리포트", style: Theme.of(context).textTheme.headlineSmall, textAlign: TextAlign.center),
            Divider(height: 30),
            
            Text("가장 유사한 가수는...", style: TextStyle(fontSize: 16), textAlign: TextAlign.center),
            Text(bestMatch, style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.deepPurple)),
            SizedBox(height: 20),

            Text("🎤 나의 음역대", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            Text(userVocalRange, style: TextStyle(fontSize: 18)),
            SizedBox(height: 20),

            Text("🎶 추천곡 목록", style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            if (recommendedSongs.isNotEmpty)
              ...recommendedSongs.map((song) => Text(" - $song", style: TextStyle(fontSize: 16))).toList()
            else
              Text("추천 가능한 곡이 없습니다.", style: TextStyle(fontSize: 16)),
            
            SizedBox(height: 20),
            Text("--- Top 3 유사도 ---", textAlign: TextAlign.center),
            ...topKResults.map((result) => 
               Text("${result['singer']}: ${result['similarity']}", textAlign: TextAlign.center)
            ).toList(),
          ],
        ),
      ),
    );
  }
}