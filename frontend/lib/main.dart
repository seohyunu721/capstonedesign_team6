import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';
import 'dart:convert';
import 'dart:typed_data'; // 웹에서 파일 데이터를 다루기 위해 필요

void main() => runApp(MyApp());

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '음성 분석 앱',
      theme: ThemeData(
        primarySwatch: Colors.blue,
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
  final String apiUrl = "http://127.0.0.1:8000";
  
  // --- 상태 변수 수정 ---
  String? _fileName;
  Uint8List? _fileBytes; // File 객체 대신 파일의 데이터(bytes)를 저장

  String _status = "분석할 음성 파일을 선택해주세요.";
  bool _isLoading = false;
  Map<String, dynamic>? _analysisResult;

  // --- 파일 선택 함수 수정 ---
  Future<void> _pickFile() async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.audio,
    );

    if (result != null && result.files.single.bytes != null) {
      setState(() {
        _fileName = result.files.single.name;
        _fileBytes = result.files.single.bytes; // 파일 경로 대신 파일 데이터를 저장
        _status = "파일 선택 완료: $_fileName";
        _analysisResult = null;
      });
    } else {
      print("파일 선택이 취소되었거나 파일 데이터를 읽을 수 없습니다.");
    }
  }

  // --- 음성 분석 요청 함수 수정 ---
  Future<void> _analyzeVoice() async {
    if (_fileBytes == null) return;

    setState(() {
      _isLoading = true;
      _status = "음성을 분석 중입니다...";
      _analysisResult = null;
    });

    try {
      var uri = Uri.parse("$apiUrl/analyze-voice");
      var request = http.MultipartRequest('POST', uri);
      
      // 경로 대신 파일 데이터(bytes)를 직접 전송
      request.files.add(
        http.MultipartFile.fromBytes(
          'voice_file', 
          _fileBytes!, 
          filename: _fileName!
        ),
      );

      var response = await request.send();
      
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
    } catch (e) {
      setState(() {
        _status = "오류 발생: $e";
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
      appBar: AppBar(title: Text("가수 목소리 분석기")),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              ElevatedButton.icon(
                icon: Icon(Icons.audio_file),
                label: Text("음성 파일 선택"),
                onPressed: _pickFile,
              ),
              SizedBox(height: 20),
              Text(_status),
              SizedBox(height: 20),
              ElevatedButton.icon(
                icon: Icon(Icons.analytics),
                label: Text("분석 시작하기"),
                onPressed: _fileBytes == null || _isLoading ? null : _analyzeVoice,
                style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
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
    );
  }

  Widget _buildResultWidget() {
    // ... (이 부분은 수정할 필요 없음)
    String bestMatch = _analysisResult?['best_match'] ?? 'N/A';
    Map<String, dynamic> scores = _analysisResult?['similarity_scores'] ?? {};
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Text("분석 결과", style: Theme.of(context).textTheme.headlineSmall),
            SizedBox(height: 10),
            Text("가장 유사한 가수는...", style: TextStyle(fontSize: 16)),
            Text(bestMatch, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Colors.blue)),
            SizedBox(height: 20),
            Text("--- 상세 점수 ---"),
            ...scores.entries.map((entry) => 
               Text("${entry.key}: ${entry.value}")
            ).toList(),
          ],
        ),
      ),
    );
  }
}