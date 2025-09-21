import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() => runApp(MyApp());

class MyApp extends StatelessWidget {
  final String apiUrl = "http://localhost:8000";

  Future<String> fetchMessage() async {
    try {
      print("GET 요청 시작: $apiUrl/");
      final response = await http.get(
        Uri.parse("$apiUrl/"),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      );
      
      print("GET 응답 상태: ${response.statusCode}");
      print("GET 응답 헤더: ${response.headers}");
      print("GET 응답 내용: ${response.body}");
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body)['message'];
      } else {
        throw Exception("GET 요청 실패: ${response.statusCode} - ${response.body}");
      }
    } catch (e) {
      print("GET 에러: $e");
      throw Exception("네트워크 오류: $e");
    }
  }
//////////////////////////////////////////////////////////////////////////////////
  Future<Map<String, dynamic>> sendItem() async {
    try {
      print("POST 요청 시작: $apiUrl/items/");
      final response = await http.post(
        Uri.parse("$apiUrl/items/"),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode({"name": "Apple", "price": 3.5}),
      );
      
      print("POST 응답 상태: ${response.statusCode}");
      print("POST 응답 헤더: ${response.headers}");
      print("POST 응답 내용: ${response.body}");

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception("POST 요청 실패: ${response.statusCode} - ${response.body}");
      }
    } catch (e) {
      print("POST 에러: $e");
      throw Exception("네트워크 오류: $e");
    }
  }
///////////////////////////////////////////////////////////////////////////////////////////
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: Text("Flutter ↔ FastAPI Test")),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text("API URL: $apiUrl", style: TextStyle(fontSize: 12)),
              SizedBox(height: 20),
              FutureBuilder<String>(
                future: fetchMessage(),
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return CircularProgressIndicator();
                  } else if (snapshot.hasError) {
                    return Text("GET Error: ${snapshot.error}", 
                               style: TextStyle(color: Colors.red));
                  } else {
                    return Text("GET 응답: ${snapshot.data}");
                  }
                },
              ),
              SizedBox(height: 20),
              FutureBuilder<Map<String, dynamic>>(
                future: sendItem(),
                builder: (context, snapshot) {
                  if (snapshot.connectionState == ConnectionState.waiting) {
                    return CircularProgressIndicator();
                  } else if (snapshot.hasError) {
                    return Text("POST Error: ${snapshot.error}", 
                               style: TextStyle(color: Colors.red));
                  } else {
                    return Text("POST 응답: ${snapshot.data}");
                  }
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}
