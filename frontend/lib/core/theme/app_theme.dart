import 'package:flutter/material.dart';
import './colors.dart';
import '../constants/text_styles.dart';

class AppTheme {
  static ThemeData get lightTheme {
    return ThemeData(
      // Scaffolds
      scaffoldBackgroundColor: CustomColors.background,

      // Colors
      primarySwatch: CustomColors.primaryPurple,
      primaryColor: CustomColors.deepPurple,

      // Fonts
      fontFamily: 'Pretendard',

      // App Bar Theme
      appBarTheme: const AppBarTheme(
        backgroundColor: CustomColors.white,
        elevation: 1,
        centerTitle: true,
        titleTextStyle: AppTextStyles
            .appBarTitle, // (AppTextStyles.appBarTitle이 const라고 가정)
      ),

      // Button Theme (ElevatedButton)
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          foregroundColor: CustomColors.white,
          backgroundColor: CustomColors.deepPurple, // 버튼 배경색
          // ⭐️ FIX: BorderRadius.circular()는 const가 아니므로, const 제거
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10), // 버튼 모서리 둥글게
          ),
        ),
      ),

      // Card Theme
      cardTheme: CardThemeData(
        elevation: 6,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),

      // Slider/RangeSlider Theme
      sliderTheme: SliderThemeData(
        activeTrackColor: CustomColors.deepPurple,
        inactiveTrackColor: CustomColors.deepPurple.withOpacity(0.3),
        thumbColor: CustomColors.deepPurple,
        overlayColor: CustomColors.deepPurple.withOpacity(0.2),
      ),

      // navigationBarTheme: NavigationBarThemeData(
      //   backgroundColor: CustomColors.darkGrey

      // )
    );
  }
}
