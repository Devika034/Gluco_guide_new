class RiskPredictionResult {
  final String patientId;
  final String extractedReportText;
  final Map<String, dynamic> parsedHealthValues;
  final Map<String, double> riskProbabilities;
  final String note;

  RiskPredictionResult({
    required this.patientId,
    required this.extractedReportText,
    required this.parsedHealthValues,
    required this.riskProbabilities,
    required this.note,
  });

  factory RiskPredictionResult.fromJson(Map<String, dynamic> json) {
    return RiskPredictionResult(
      patientId: json['patient_id'],
      extractedReportText: json['extracted_report_text'],
      parsedHealthValues: json['parsed_health_values'],
      riskProbabilities:
          (json['risk_probabilities'] as Map<String, dynamic>).map(
        (k, v) => MapEntry(k, v.toDouble()),
      ),
      note: json['note'],
    );
  }
}
