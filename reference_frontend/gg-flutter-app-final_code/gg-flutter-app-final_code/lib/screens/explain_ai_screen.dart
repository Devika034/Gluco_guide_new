import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

class ExplainAIScreen extends StatelessWidget {
  final Map<String, dynamic> explanationData;

  const ExplainAIScreen({super.key, required this.explanationData});

  @override
  Widget build(BuildContext context) {
    final bool isSpike = explanationData['prediction_type'] == 'spike';
    final Map<String, dynamic> features = explanationData['feature_importance'] ?? {};
    final List<dynamic> recommendations = explanationData['recommendation'] ?? [];

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: const Text('Explainable AI Insights', style: TextStyle(color: Colors.white)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Colors.indigo.shade900, Colors.blue.shade900],
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _buildPredictionSummary(isSpike),
                const SizedBox(height: 24),
                _buildFeatureContribution(features),
                const SizedBox(height: 24),
                if (recommendations.isNotEmpty) _buildRecommendations(recommendations),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPredictionSummary(bool isSpike) {
    String title = isSpike ? "Glucose Spike Risk" : "Long-Term Complication Risk";
    String probabilityText = "";
    Color riskColor = Colors.greenAccent;

    if (isSpike) {
      double prob = (explanationData['spike_probability'] ?? 0.0) * 100;
       probabilityText = "${prob.toStringAsFixed(1)}% probability";
       riskColor = prob > 50 ? Colors.redAccent : Colors.greenAccent;
    } else {
       probabilityText = "Analysis Complete";
       riskColor = Colors.orangeAccent;
    }

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withOpacity(0.2)),
      ),
      child: Column(
        children: [
          const Icon(Icons.analytics_rounded, color: Colors.white, size: 48),
          const SizedBox(height: 12),
          Text(title, style: const TextStyle(color: Colors.white70, fontSize: 18)),
          const SizedBox(height: 8),
          Text(
            probabilityText,
            style: TextStyle(color: riskColor, fontSize: 32, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildFeatureContribution(Map<String, dynamic> features) {
    if (features.isEmpty) return const SizedBox();

    // Sort features by importance
    var sortedEntries = features.entries.toList()
      ..sort((a, b) => (b.value as num).compareTo(a.value as num));

    // Calculate total for percentages
    double totalVal = sortedEntries.fold(0.0, (sum, item) => sum + (item.value as num).toDouble());
    if (totalVal == 0.0) totalVal = 1.0;

    final List<Color> colors = [
      Colors.indigoAccent.shade100,
      Colors.tealAccent.shade100,
      Colors.orangeAccent.shade100,
      Colors.pinkAccent.shade100,
      Colors.greenAccent.shade100,
      Colors.cyanAccent.shade100,
      Colors.purpleAccent.shade100,
    ];

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Feature Contribution',
            style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          const Text(
            'These factors had the biggest impact on the AI prediction.',
            style: TextStyle(color: Colors.white70, fontSize: 14),
          ),
          const SizedBox(height: 32),
          SizedBox(
            height: 250,
            child: PieChart(
              PieChartData(
                sectionsSpace: 2,
                centerSpaceRadius: 40,
                sections: sortedEntries.asMap().entries.map((e) {
                  int index = e.key;
                  var entry = e.value;
                  double value = (entry.value as num).toDouble();
                  double percentage = (value / totalVal) * 100;
                  
                  return PieChartSectionData(
                    color: colors[index % colors.length],
                    value: value,
                    title: '${percentage.toStringAsFixed(1)}%',
                    radius: 70,
                    titleStyle: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: Colors.black87,
                    ),
                  );
                }).toList(),
              ),
            ),
          ),
          const SizedBox(height: 32),
          Wrap(
            spacing: 16,
            runSpacing: 12,
            children: sortedEntries.asMap().entries.map((e) {
              int index = e.key;
              var entry = e.value;
              String text = entry.key;
              if (text.length > 20) text = "${text.substring(0, 19)}.";
              return Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    width: 14,
                    height: 14,
                    decoration: BoxDecoration(
                      color: colors[index % colors.length],
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(text, style: const TextStyle(color: Colors.white70, fontSize: 13, fontWeight: FontWeight.w500)),
                ],
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildRecommendations(List<dynamic> recommendations) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'AI Suggestions',
          style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 16),
        ...recommendations.map((rec) => Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 10,
                offset: const Offset(0, 4),
              )
            ]
          ),
          child: Row(
            children: [
              Icon(Icons.lightbulb_circle, color: Colors.amber.shade600, size: 32),
              const SizedBox(width: 16),
              Expanded(
                child: Text(
                  rec.toString(),
                  style: TextStyle(color: Colors.indigo.shade900, fontSize: 15, fontWeight: FontWeight.w500),
                ),
              ),
            ],
          ),
        )).toList(),
      ],
    );
  }
}
