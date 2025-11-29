import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:file_picker/file_picker.dart';
import 'package:frontend/screens/searching/searching_screen.dart';
import 'package:frontend/services/result_storage_service.dart';
import 'package:lottie/lottie.dart';
import '/services/voice_service.dart';
import '/services/api_service.dart';
import '/services/preferences_service.dart';
import '/widgets/loading_indicator.dart';
import '/core/theme/colors.dart';

// --- 음성 분석 메인 화면 ---
class AnalysisScreen extends StatefulWidget {
  const AnalysisScreen({Key? key}) : super(key: key); // 추가

  @override
  _AnalysisScreenState createState() => _AnalysisScreenState();
}

class _AnalysisScreenState extends State<AnalysisScreen> {
  // --- 상태 변수 ---
  final VoiceService _voiceService = VoiceService();
  final ApiService _apiService = ApiService();
  final PreferencesService _prefsService = PreferencesService();
  final ResultStorageService _resultStorageService = ResultStorageService();

  bool _isRecorderInitialized = false;
  bool _isRecording = false;

  String? _fileName;
  Uint8List? _fileBytes;

  bool _isLoading = false;
  Map<String, dynamic>? _analysisResult;
  String _statusMessage = "분석할 음성 파일을 선택해주세요.";
  bool _isPickerOpening = false; // 이중 클릭 방지

  // --- 생명주기 함수 ---
  @override
  void initState() {
    super.initState();
    _initServices();
  }

  Future<void> _initServices() async {
    await _voiceService.initRecorder();
    if (mounted) {
      setState(() {
        _isRecorderInitialized = _voiceService.isRecorderInitialized;
        if (!_isRecorderInitialized) {
          _statusMessage = " 마이크 권한이 필요합니다.";
        }
      });
    }
  }

  @override
  void dispose() {
    _voiceService.disposeRecorder();
    super.dispose();
  }

  // --- 핵심 로직 함수 ---

  Future<void> _pickAndAnalyze() async {
    // 이중 클릭 방지
    if (_isLoading || _isPickerOpening) return;
    setState(() => _isPickerOpening = true);

    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.audio,
      );

      if (result != null) {
        final platformFile = result.files.single;
        Uint8List? fileBytes;

        // --- ⭐️ 웹/모바일 호환 로직 ⭐️ ---
        if (kIsWeb) {
          fileBytes = platformFile.bytes;
        } else {
          String? path = platformFile.path;
          if (path != null) {
            fileBytes = await File(path).readAsBytes();
          }
        }
        // ---------------------------------

        if (fileBytes != null) {
          setState(() {
            _fileName = platformFile.name;
            _fileBytes = fileBytes;
            _statusMessage = "파일 선택 완료: $_fileName";
            _analysisResult = null;
          });
          _analyzeVoice();
        } else {
          print("파일 데이터를 확보하지 못했습니다.");
        }
      } else {
        print("파일 선택이 취소되었습니다.");
      }
    } catch (e) {
      print("파일 피커 오류: $e");
    } finally {
      setState(() => _isPickerOpening = false);
    }
  }

  Future<void> _startRecording() async {
    String? status = await _voiceService.startRecording();
    if (status == null) {
      setState(() {
        _isRecording = true;
        _statusMessage = "🎙️ 녹음 중...";
        _fileName = _voiceService.tempRecordingPath.split('/').last;
      });
    } else {
      setState(() => _statusMessage = status);
    }
  }

  Future<void> _stopRecordingAndAnalyze() async {
    Uint8List? fileBytes = await _voiceService.stopRecording();

    setState(() => _isRecording = false);

    if (fileBytes != null) {
      print("✅ 녹음된 파일 크기: ${fileBytes.lengthInBytes} bytes");
      setState(() {
        _fileBytes = fileBytes;
        _fileName = _voiceService.tempRecordingPath.split('/').last;
        _statusMessage = "녹음 완료! 분석을 시작합니다.";
      });
      await _analyzeVoice();
    } else {
      setState(() => _statusMessage = "녹음 중지 실패.");
    }
  }

  Future<void> _analyzeVoice() async {
    if (_fileBytes == null || _fileName == null) return;
    setState(() {
      _isLoading = true;
      // _statusMessage = "음성을 분석 중입니다...";
    });

    try {
      final prefs = await _prefsService.loadPreferences();

      // ApiService를 통해 분석 요청
      final result = await _apiService.analyzeVoice(
        fileBytes: _fileBytes!,
        fileName: _fileName!,
        gender: prefs['gender'] as String,
        genre: prefs['genre'] as String,
        startYear: prefs['startYear'] as int,
        endYear: prefs['endYear'] as int,
      );

      await _resultStorageService.saveAnalysisResult(result); // 추가

      setState(() {
        _analysisResult = result;
        _statusMessage = "분석 완료!";
      });
      // 추가로 새로운 화면으로 세팅
      if (mounted) {
        Navigator.of(context).push(
          MaterialPageRoute(builder: (context) => const SearchingScreen()),
        );
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
      // appBar: AppBar(title: const Text("Vocalize")),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (!_isLoading) _buildUploadWidget(),
              const SizedBox(height: 40),
              if (_isLoading) _buildLoadingWidget(),
              // if (!_isLoading && _analysisResult != null) _buildResultWidget(),
              const SizedBox(height: 20),
              Text(
                _statusMessage,
                style: TextStyle(
                  color: _isLoading
                      ? CustomColors.deepPurple
                      : CustomColors.mediumGrey,
                ),
              ),
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
              Icon(
                Icons.upload_file_outlined,
                size: 100,
                color: CustomColors.lightGrey,
              ),
              const SizedBox(height: 16),
              Text(
                _fileName ?? "노래 업로드하기",
                style: TextStyle(fontSize: 18, color: CustomColors.mediumGrey),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
        const SizedBox(height: 30),
        ElevatedButton.icon(
          onPressed: _isRecording ? _stopRecordingAndAnalyze : _startRecording,
          icon: Icon(_isRecording ? Icons.stop : Icons.mic),
          label: Text(_isRecording ? "녹음 중지" : "음성 녹음하기"),
        ),
        if (_isRecording)
          Padding(
            padding: const EdgeInsets.only(top: 8.0),
            child: Text(
              "🎙️ 녹음 중입니다...",
              style: TextStyle(color: CustomColors.accentRed),
            ),
          ),
      ],
    );
  }

  Widget _buildLoadingWidget() {
    return LoadingIndicator(
      message: "음성 분석 중...",
      progressIndicator: Lottie.asset(
        'assets/Lottie/loading.json',
        width: 250,
        height: 250,
      ),
    );
  }
}
