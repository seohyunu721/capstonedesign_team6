import 'package:flutter/material.dart';
import '/widgets/custom_curved_nav_bar.dart';

import '/screens/analysis/analysis_screen.dart';
import '/screens/settings/setting_screen.dart';
import '/screens/searching/searching_screen.dart';

class MainNavigatorScreen extends StatefulWidget {
  final int initialIndex; // 추가

  const MainNavigatorScreen({
    super.key,
    this.initialIndex = 0,
  }); // initialIndex = 0 선언

  @override
  State<MainNavigatorScreen> createState() => _MainNavigatorScreenState();
}

class _MainNavigatorScreenState extends State<MainNavigatorScreen> {
  late int _selectedIndex; // 현재 선택된 탭의 인덱스

  /////////// 추가 ///////////////////
  late PageController _pageController;
  ////////////////////////////////////

  // 내비게이션 바에 표시될 아이콘 목록
  final List<Widget> _navItems = const [
    Icon(Icons.home, size: 30, color: Colors.white),
    Icon(Icons.analytics, size: 30, color: Colors.white),
    Icon(Icons.settings, size: 30, color: Colors.white),
  ];

  // 내비게이션 탭 클릭 시 표시될 실제 스크린 목록
  final List<Widget> _screens = [
    const SettingScreen(),
    AnalysisScreen(), // lib/screens/analysis/analysis_screen.dart
    const SearchingScreen(),
  ];

  ////////////////////////////////추가 ////////////////////////
  // initState 에 PageController 초기화
  @override
  void initState() {
    super.initState();
    _selectedIndex = widget.initialIndex; // 추가
    _pageController = PageController(initialPage: _selectedIndex);
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }
  ////////////////////////////////////////////

  // 탭이 선택되었을 때 실행되는 함수 (상태 관리 로직)
  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
    ///////////////// 추가 ////////////////////////
    _pageController.animateToPage(
      index,
      duration: const Duration(microseconds: 400),
      curve: Curves.easeInOut,
    );
    ////////////////////////////////////
  }

  ///////// 추가 ////////////
  ///// pageView의 페이지 변경시 실행
  void _onPageChanged(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }
  ////////////////////////////////

  // swipe 기능 추가

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: PageView(
        // ⭐️ PageView로 변경
        controller: _pageController, // ⭐️ 컨트롤러 연결
        onPageChanged: _onPageChanged, // ⭐️ 페이지 변경 콜백 연결
        // 1. 선택된 인덱스에 따라 body의 내용을 바꿉니다. (이제 PageView가 담당)
        children: _screens,
      ),

      // 2. 위젯으로 분리한 커스텀 내비게이션 바를 사용합니다.
      bottomNavigationBar: CustomCurvedNavBar(
        selectedIndex: _selectedIndex, // 현재 인덱스 전달
        onItemSelected: _onItemTapped, // 콜백 함수 전달
        items: _navItems, // 아이템 목록 전달
      ),
    );
  }
}
