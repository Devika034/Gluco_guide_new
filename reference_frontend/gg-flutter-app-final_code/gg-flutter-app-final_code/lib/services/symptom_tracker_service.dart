import 'package:flutter/material.dart';
import '../models/disease_tracker.dart';
import 'api_service.dart';
import 'profile_service.dart';

class AssessmentResult {
  final DateTime timestamp;
  final String disease;
  final DiseaseResult result;

  AssessmentResult({
    required this.timestamp,
    required this.disease,
    required this.result,
  });
}

class SymptomTrackerService extends ChangeNotifier {
  static final SymptomTrackerService _instance =
      SymptomTrackerService._internal();
  factory SymptomTrackerService() => _instance;
  SymptomTrackerService._internal();

  final Map<String, List<AssessmentResult>> _history = {
    "retinopathy": [],
    "nephropathy": [],
    "neuropathy": [],
  };

  Map<String, List<AssessmentResult>> get history => _history;

  Future<DiseaseResult?> performAssessment(
      int patientId, String disease, Map<String, int> answers) async {
    try {
      final rawResult =
          await ApiService.analyzeTracker(patientId, disease, answers);
      final result = DiseaseResult.fromJson(rawResult);

      final assessment = AssessmentResult(
        timestamp: DateTime.now(),
        disease: disease,
        result: result,
      );

      _history[disease]?.add(assessment);
      notifyListeners();
      return result;
    } catch (e) {
      debugPrint("Error performing assessment: $e");
      return null;
    }
  }

  List<AssessmentResult> getHistoryFor(String disease) {
    return _history[disease] ?? [];
  }
}
