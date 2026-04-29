class SpikeInput {
  final double currentGlucose;
  final double avgGI;
  final double totalGL;
  final double durationYears;
  final int age;
  final double bmi;
  final double activityLevel;
  final double medicationDose;
  final double hba1c;
  final double bpSystolic;
  final double bpDiastolic;
  final double cholesterol;
  final double fastingGlucose;
  final int timeOfDay;
  final int familyHistory;
  final int alcoholSmoking;

  SpikeInput({
    required this.currentGlucose,
    required this.avgGI,
    required this.totalGL,
    required this.durationYears,
    required this.age,
    required this.bmi,
    required this.activityLevel,
    required this.medicationDose,
    required this.hba1c,
    required this.bpSystolic,
    required this.bpDiastolic,
    required this.cholesterol,
    required this.fastingGlucose,
    required this.timeOfDay,
    required this.familyHistory,
    required this.alcoholSmoking,
  });

  Map<String, dynamic> toJson() => {
        'current_glucose': currentGlucose,
        'avg_GI': avgGI,
        'total_GL': totalGL,
        'duration_years': durationYears,
        'age': age,
        'bmi': bmi,
        'activity_level': activityLevel,
        'medication_dose': medicationDose,
        'hba1c': hba1c,
        'bp_systolic': bpSystolic,
        'bp_diastolic': bpDiastolic,
        'cholesterol': cholesterol,
        'fasting_glucose': fastingGlucose,
        'time_of_day': timeOfDay,
        'family_history': familyHistory,
        'alcohol_smoking': alcoholSmoking,
      };
}

class SpikePredictionResult {
  final Map<String, double> predictions;
  final String spikeRisk;
  final String advice;

  SpikePredictionResult({
    required this.predictions,
    required this.spikeRisk,
    required this.advice,
  });

  factory SpikePredictionResult.fromJson(Map<String, dynamic> json) {
    return SpikePredictionResult(
      predictions: (json['predictions'] as Map<String, dynamic>).map(
        (k, v) => MapEntry(k, v.toDouble()),
      ),
      spikeRisk: json['spike_risk'],
      advice: json['advice'],
    );
  }
}
