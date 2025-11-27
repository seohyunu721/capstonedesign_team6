import 'package:flutter/material.dart';
import 'package:curved_navigation_bar/curved_navigation_bar.dart';
import '/core/theme/colors.dart';

class CustomCurvedNavBar extends StatelessWidget {
  final int selectedIndex;
  final ValueChanged<int> onItemSelected;
  final List<Widget> items;

  const CustomCurvedNavBar({
    super.key, // 뭔지 모르겠는데 key? key, 쓰고 싶은데 오류 뜸
    required this.selectedIndex,
    required this.onItemSelected,
    required this.items,
  }); // : super(key: key);

  @override
  Widget build(BuildContext context) {
    return CurvedNavigationBar(
      backgroundColor: CustomColors.deepPurple,
      color: CustomColors.white,
      buttonBackgroundColor: CustomColors.primaryBlue,
      height: 60,
      index: selectedIndex,
      items: items,
      onTap: onItemSelected,
      animationCurve: Curves.easeInOut,
      animationDuration: const Duration(milliseconds: 300),
    );
  }
}
