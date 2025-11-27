import 'package:flutter/material.dart';

class CustomAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;

  const CustomAppBar({super.key, required this.title});

  @override
  Widget build(BuildContext context) {
    return AppBar(
      title: Text(title),
      // AppTheme에서 설정한 스타일을 따릅니다.
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}
