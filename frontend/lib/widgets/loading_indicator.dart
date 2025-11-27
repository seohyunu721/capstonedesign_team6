import 'package:flutter/material.dart';
import '/core/theme/colors.dart';

class LoadingIndicator extends StatelessWidget {
  final String message;
  final Widget progressIndicator;

  const LoadingIndicator({
    Key? key,
    required this.message,
    required this.progressIndicator,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(message, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 20),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 40.0),
          child: progressIndicator,
        ),
      ],
    );
  }
}
