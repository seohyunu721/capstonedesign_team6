import 'package:flutter/material.dart';

class AppTextStyles {
  // AppBar 제목 스타일
  static const TextStyle appBarTitle = TextStyle(
    color: Colors.black,
    fontSize: 18,
    fontWeight: FontWeight.w600,
  );

  // 헤드라인 (SetupScreen의 제목 등)
  static TextStyle headlineSmallBold(BuildContext context) {
    return Theme.of(
      context,
    ).textTheme.headlineSmall!.copyWith(fontWeight: FontWeight.bold);
  }

  // 제목 (SetupScreen의 각 항목 제목 등)
  static TextStyle titleLarge(BuildContext context) {
    return Theme.of(context).textTheme.titleLarge!;
  }
}
