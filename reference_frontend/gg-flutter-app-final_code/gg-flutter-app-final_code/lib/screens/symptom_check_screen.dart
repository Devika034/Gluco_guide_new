import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/symptom_tracker_service.dart';
import '../services/profile_service.dart';
import '../models/disease_tracker.dart';

class SymptomCheckScreen extends StatefulWidget {
  const SymptomCheckScreen({super.key});

  @override
  State<SymptomCheckScreen> createState() => _SymptomCheckScreenState();
}

class _SymptomCheckScreenState extends State<SymptomCheckScreen> {
  String _selectedDisease = 'retinopathy';
  Map<String, dynamic>? _questions;
  Map<String, int> _answers = {};
  bool _isLoading = false;
  DiseaseResult? _analysisResult;

  @override
  void initState() {
    super.initState();
    _fetchQuestions();
  }

  void _fetchQuestions() async {
    setState(() {
      _isLoading = true;
      _analysisResult = null;
      _answers = {};
    });
    try {
      final q = await ApiService.getQuestions(_selectedDisease);
      setState(() => _questions = q);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error fetching questions: $e')));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  void _submitAssessment() async {
    if (_questions == null || _answers.length < _questions!.length) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please answer all questions')));
      return;
    }

    setState(() => _isLoading = true);
    final profileId = ProfileService().profile?.id ?? 1;
    final result = await SymptomTrackerService()
        .performAssessment(profileId, _selectedDisease, _answers);
    setState(() {
      _analysisResult = result;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: const Text('Symptom Checker',
            style: TextStyle(color: Colors.white)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              Colors.indigo.shade900,
              Colors.indigo.shade700,
              Colors.blue.shade900,
            ],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              _buildDiseaseSelector(),
              Expanded(
                child: _isLoading
                    ? const Center(
                        child: CircularProgressIndicator(color: Colors.white))
                    : _analysisResult != null
                        ? _buildResultView()
                        : _buildQuestionList(),
              ),
              if (_analysisResult == null && _questions != null)
                Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: ElevatedButton(
                    onPressed: _submitAssessment,
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 18),
                      backgroundColor: Colors.white,
                      foregroundColor: Colors.indigo.shade900,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(16)),
                      minimumSize: const Size(double.infinity, 50),
                      elevation: 8,
                    ),
                    child: const Text('Analyze Symptoms',
                        style: TextStyle(
                            fontSize: 18, fontWeight: FontWeight.bold)),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDiseaseSelector() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
      child: Container(
        padding: const EdgeInsets.all(4),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.1),
          borderRadius: BorderRadius.circular(20),
        ),
        child: SegmentedButton<String>(
          style: SegmentedButton.styleFrom(
            backgroundColor: Colors.transparent,
            selectedBackgroundColor: Colors.white,
            selectedForegroundColor: Colors.indigo.shade900,
            foregroundColor: Colors.white70,
            side: BorderSide.none,
          ),
          segments: const [
            ButtonSegment(
                value: 'retinopathy',
                label: Text('Eyes'),
                icon: Icon(Icons.visibility)),
            ButtonSegment(
                value: 'nephropathy',
                label: Text('Kidneys'),
                icon: Icon(Icons.water_drop)),
            ButtonSegment(
                value: 'neuropathy',
                label: Text('Nerves'),
                icon: Icon(Icons.bolt)),
          ],
          selected: {_selectedDisease},
          onSelectionChanged: (set) {
            setState(() => _selectedDisease = set.first);
            _fetchQuestions();
          },
        ),
      ),
    );
  }

  Widget _buildQuestionList() {
    if (_questions == null) {
      return const Center(
          child: Text('Select an area to assess',
              style: TextStyle(color: Colors.white70)));
    }

    return ListView(
      padding: const EdgeInsets.all(20),
      children: _questions!.entries.map((entry) {
        final qId = entry.key;
        final data = entry.value;
        return Container(
          margin: const EdgeInsets.only(bottom: 16),
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.1),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: Colors.white.withOpacity(0.2)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(data['question'],
                  style: const TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                      color: Colors.white)),
              const SizedBox(height: 16),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: (data['options'] as Map<String, dynamic>)
                    .entries
                    .map((opt) {
                  final isSelected = _answers[qId] == opt.value;
                  return ChoiceChip(
                    label: Text(opt.key),
                    selected: isSelected,
                    selectedColor: Colors.white,
                    labelStyle: TextStyle(
                      color:
                          isSelected ? Colors.indigo.shade900 : Colors.white70,
                      fontWeight:
                          isSelected ? FontWeight.bold : FontWeight.normal,
                    ),
                    backgroundColor: Colors.white.withOpacity(0.1),
                    onSelected: (selected) {
                      setState(() {
                        if (selected) {
                          _answers[qId] = opt.value;
                        }
                      });
                    },
                  );
                }).toList(),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildResultView() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.1),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.analytics_rounded,
                size: 48, color: Colors.white),
          ),
          const SizedBox(height: 24),
          Text(_analysisResult!.status,
              style: const TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                  color: Colors.white)),
          Text('Trend: ${_analysisResult!.trend}',
              style: TextStyle(
                  color: Colors.white.withOpacity(0.6), fontSize: 16)),
          const SizedBox(height: 32),
          _buildScoreGauge(_analysisResult!.score),
          const SizedBox(height: 40),
          if (_analysisResult!.forecast != null || _analysisResult!.explanation != null) ...[
            _buildForecastCard(_analysisResult!.forecast, _analysisResult!.explanation),
            const SizedBox(height: 32),
          ],
          _buildSection('Interpretation', _analysisResult!.interpretation),
          const SizedBox(height: 32),
          _buildSection('Recommendations', _analysisResult!.recommendations),
          const SizedBox(height: 48),
          TextButton.icon(
              onPressed: _fetchQuestions,
              icon: const Icon(Icons.refresh, color: Colors.white),
              label: const Text('Start New Assessment',
                  style: TextStyle(color: Colors.white))),
        ],
      ),
    );
  }

  Widget _buildForecastCard(Map<String, dynamic>? forecast, String? explanation) {
    if (forecast == null && explanation == null) return const SizedBox.shrink();

    String prediction = forecast?['prediction']?.toString() ?? 'No prediction available';
    String daysToRisk = forecast?['days_to_critical_risk']?.toString() ?? 'N/A';

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.orangeAccent.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.orangeAccent.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.timeline_rounded, color: Colors.orangeAccent),
              const SizedBox(width: 8),
              const Expanded(
                child: Text('AI Predictive Forecast',
                    style: TextStyle(
                        color: Colors.orangeAccent, fontWeight: FontWeight.bold, fontSize: 18)),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text('Trend Prediction: $prediction',
              style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Text('Estimated Days to Critical Risk: $daysToRisk',
              style: const TextStyle(color: Colors.white70, fontSize: 14)),
          if (explanation != null && explanation.trim().isNotEmpty && explanation != "No explanation") ...[
            const SizedBox(height: 16),
            const Divider(color: Colors.white24),
            const SizedBox(height: 12),
            const Text('AI Context / SHAP Reasoning:',
                style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14)),
            const SizedBox(height: 4),
            Text(explanation,
                style: const TextStyle(color: Colors.white70, fontSize: 14, height: 1.4, fontStyle: FontStyle.italic)),
          ],
        ],
      ),
    );
  }

  Widget _buildScoreGauge(double score) {
    Color color = score < 0.3
        ? Colors.greenAccent
        : (score < 0.6 ? Colors.orangeAccent : Colors.redAccent);
    return Column(
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(10),
          child: LinearProgressIndicator(
              value: score,
              minHeight: 16,
              backgroundColor: Colors.white.withOpacity(0.1),
              color: color),
        ),
        const SizedBox(height: 12),
        Text('Impact Score: ${(score * 100).toInt()}%',
            style: TextStyle(
                fontSize: 18, fontWeight: FontWeight.bold, color: color)),
      ],
    );
  }

  Widget _buildSection(String title, List<String> items) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title,
            style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Colors.white)),
        const SizedBox(height: 16),
        ...items.map((item) => Container(
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.05),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(children: [
                const Icon(Icons.check_circle_outline,
                    size: 20, color: Colors.greenAccent),
                const SizedBox(width: 12),
                Expanded(
                    child: Text(item,
                        style: const TextStyle(
                            color: Colors.white, fontSize: 15))),
              ]),
            )),
      ],
    );
  }
}
