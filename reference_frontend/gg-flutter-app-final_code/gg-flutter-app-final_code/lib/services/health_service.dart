import 'package:flutter/material.dart';

class HealthService extends ChangeNotifier {
  // Singleton pattern
  static final HealthService _instance = HealthService._internal();
  factory HealthService() => _instance;
  HealthService._internal();

  double _currentGlucose = 120.0;
  double _hbA1c = 6.5;
  double _yearsWithDiabetes = 2.0;
  double _systolicBP = 120.0;
  double _diastolicBP = 80.0;

  double get currentGlucose => _currentGlucose;
  double get hbA1c => _hbA1c;
  double get yearsWithDiabetes => _yearsWithDiabetes;
  double get systolicBP => _systolicBP;
  double get diastolicBP => _diastolicBP;

  void updateMetrics({
    double? currentGlucose,
    double? hbA1c,
    double? yearsWithDiabetes,
    double? systolicBP,
    double? diastolicBP,
  }) {
    if (currentGlucose != null) _currentGlucose = currentGlucose;
    if (hbA1c != null) _hbA1c = hbA1c;
    if (yearsWithDiabetes != null) _yearsWithDiabetes = yearsWithDiabetes;
    if (systolicBP != null) _systolicBP = systolicBP;
    if (diastolicBP != null) _diastolicBP = diastolicBP;
    notifyListeners();
  }

  // Simplified risk assessment logic for educational purposes
  String get overallRisk {
    if (_hbA1c > 8.0 || _currentGlucose > 200) return "High";
    if (_hbA1c > 7.0 || _currentGlucose > 150) return "Moderate";
    return "Low";
  }
}
