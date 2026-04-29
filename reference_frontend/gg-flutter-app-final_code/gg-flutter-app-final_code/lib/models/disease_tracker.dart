class AnswerSet {
  final Map<String, int> answers;

  AnswerSet({required this.answers});

  Map<String, dynamic> toJson() => {
        'answers': answers,
      };
}

class DiseaseResult {
  final String status;
  final String trend;
  final double score;
  final List<String> interpretation;
  final List<String> recommendations;
  final Map<String, dynamic>? forecast;
  final String? explanation;
  final DateTime timestamp;

  DiseaseResult({
    required this.status,
    required this.trend,
    required this.score,
    required this.interpretation,
    required this.recommendations,
    this.forecast,
    this.explanation,
    required this.timestamp,
  });

  factory DiseaseResult.fromJson(Map<String, dynamic> json) {
    return DiseaseResult(
      status: json['status'],
      trend: json['trend'],
      score: json['score'].toDouble(),
      interpretation: List<String>.from(json['interpretation']),
      recommendations: List<String>.from(json['recommendations']),
      forecast: json['forecast'] as Map<String, dynamic>?,
      explanation: json['explanation'] as String?,
      timestamp: DateTime.parse(json['timestamp']),
    );
  }
}
