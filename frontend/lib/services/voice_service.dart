// import 'dart:io';
// import 'dart:typed_data';
// import 'package:flutter/foundation.dart';
// import 'package:flutter_sound/flutter_sound.dart';
// import 'package:permission_handler/permission_handler.dart';
// import 'package:path_provider/path_provider.dart';

// class VoiceService {
//   final FlutterSoundRecorder _recorder = FlutterSoundRecorder();
//   bool _isRecorderInitialized = false;
//   String _tempRecordingPath = "";

//   bool get isRecorderInitialized => _isRecorderInitialized;
//   String get tempRecordingPath => _tempRecordingPath;

//   Future<void> initRecorder() async {
//     if (kIsWeb) return; // 웹에서는 녹음기 초기화 불필요

//     await _recorder.openRecorder();
//     var status = await Permission.microphone.request();
//     if (status.isGranted) {
//       _isRecorderInitialized = true;
//     }
//   }

//   Future<String?> startRecording() async {
//     if (!_isRecorderInitialized || kIsWeb) {
//       return kIsWeb ? "웹에서는 녹음을 지원하지 않습니다." : "마이크 권한이 필요합니다.";
//     }

//     try {
//       Directory tempDir = await getTemporaryDirectory();
//       _tempRecordingPath =
//           '${tempDir.path}/voice_${DateTime.now().millisecondsSinceEpoch}.wav';

//       await _recorder.startRecorder(
//         toFile: _tempRecordingPath,
//         codec: Codec.pcm16WAV,
//         sampleRate: 16000, // librosa.pyin과 동일 하게 16KHz
//         numChannels: 1,
//         bitRate: 16000,
//       );
//       return null; // 성공
//     } catch (e) {
//       return "녹음 시작 실패: $e";
//     }
//   }

//   Future<Uint8List?> stopRecording() async {
//     if (!_isRecorderInitialized) return null;

//     try {
//       final path = await _recorder.stopRecorder();
//       if (path != null) {
//         return await File(path).readAsBytes();
//       }
//       return null;
//     } catch (e) {
//       print("녹음 중지 실패: $e");
//       return null;
//     }
//   }

//   void disposeRecorder() {
//     _recorder.closeRecorder();
//   }
// }
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:path_provider/path_provider.dart';

class VoiceService {
  final FlutterSoundRecorder _recorder = FlutterSoundRecorder();
  bool _isRecorderInitialized = false;
  String _tempRecordingPath = "";

  bool get isRecorderInitialized => _isRecorderInitialized;
  String get tempRecordingPath => _tempRecordingPath;

  Future<void> initRecorder() async {
    if (kIsWeb) return;

    await _recorder.openRecorder();
    var status = await Permission.microphone.request();
    if (status.isGranted) {
      _isRecorderInitialized = true;
    }
  }

  Future<String?> startRecording() async {
    if (!_isRecorderInitialized || kIsWeb) {
      return kIsWeb ? "웹에서는 녹음을 지원하지 않습니다." : "마이크 권한이 필요합니다.";
    }

    try {
      Directory tempDir = await getTemporaryDirectory();

      // 플랫폼별 Codec 및 확장자
      Codec recordingCodec;
      String extension;

      if (defaultTargetPlatform == TargetPlatform.android) {
        recordingCodec = Codec.aacADTS; // WAV 대신 안정적인 AAC 사용
        extension = ".aac";
      } else if (defaultTargetPlatform == TargetPlatform.iOS) {
        recordingCodec = Codec.aacMP4;
        extension = ".m4a";
      } else {
        recordingCodec = Codec.aacADTS;
        extension = ".aac";
      }
      _tempRecordingPath =
          '${tempDir.path}/voice_${DateTime.now().millisecondsSinceEpoch}$extension';

      await _recorder.startRecorder(
        toFile: _tempRecordingPath,
        codec: recordingCodec, //
        sampleRate: 16000, // ✅ FastAPI와 일치
        numChannels: 1,
        bitRate: 16000,
      );
      return null;
    } catch (e) {
      return "녹음 시작 실패: $e";
    }
  }

  Future<Uint8List?> stopRecording() async {
    if (!_isRecorderInitialized) return null;

    try {
      final path = await _recorder.stopRecorder();
      if (path == null) return null;

      // ✅ 임시 파일을 영구 디렉토리로 복사
      final docsDir = await getApplicationDocumentsDirectory();
      final fileName = path.split('/').last;
      final permanentPath = '${docsDir.path}/$fileName';
      final recordedFile = await File(path).copy(permanentPath);

      // print("✅ 저장된 음성 경로: ${recordedFile.path}");

      // ✅ 파일 검증: 크기 / 존재 여부 확인
      if (await recordedFile.exists()) {
        print("파일 크기: ${(await recordedFile.length()) / 1024} KB");
      } else {
        print("❌ 파일 저장 실패: ${recordedFile.path}");
      }

      return await recordedFile.readAsBytes();
    } catch (e) {
      print("녹음 중지 실패: $e");
      return null;
    }
  }

  void disposeRecorder() {
    _recorder.closeRecorder();
  }
}
