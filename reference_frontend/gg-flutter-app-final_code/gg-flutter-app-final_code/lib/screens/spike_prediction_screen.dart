import 'package:flutter/material.dart';
import '../services/diet_service.dart';
import '../services/api_service.dart';
import '../models/spike_prediction.dart';
import '../services/profile_service.dart';
import 'explain_ai_screen.dart';

class SpikePredictionScreen extends StatefulWidget {
  const SpikePredictionScreen({super.key});

  @override
  State<SpikePredictionScreen> createState() => _SpikePredictionScreenState();
}

class _SpikePredictionScreenState extends State<SpikePredictionScreen> {
  SpikePredictionResult? _result;
  bool _isLoading = false;
  final TextEditingController _glucoseController =
      TextEditingController(text: "100.0");

  @override
  void dispose() {
    _glucoseController.dispose();
    super.dispose();
  }

  void _getPrediction() async {
    final double userGlucose = double.tryParse(_glucoseController.text) ?? 100.0;
    setState(() => _isLoading = true);
    
    try {
      final result =
          await DietService().predictSpike(userGlucose, 1);
      if (!mounted) return;
      setState(() {
        _result = result;
        _isLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _isLoading = false);
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Spike Prediction')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            const Icon(Icons.show_chart, size: 80, color: Colors.red),
            const SizedBox(height: 16),
            const Text(
              'How will your glucose respond?',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            const Text(
              'Predict potential glucose spikes based on your current glycemic load.',
              style: TextStyle(color: Colors.grey),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 40.0),
              child: TextField(
                controller: _glucoseController,
                keyboardType: TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                  labelText: 'Current Glucose (mg/dL)',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.bloodtype),
                ),
              ),
            ),
            const SizedBox(height: 32),
            if (_result == null)
              ElevatedButton(
                onPressed: _isLoading ? null : _getPrediction,
                style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.all(16),
                    backgroundColor: Colors.red,
                    foregroundColor: Colors.white),
                child: _isLoading
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text('Predict Now'),
              )
            else
              _buildResultCard(),
          ],
        ),
      ),
    );
  }

  Widget _buildResultCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _result!.spikeRisk == "High"
            ? Colors.red.shade50
            : Colors.green.shade50,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
            color: _result!.spikeRisk == "High"
                ? Colors.red.shade200
                : Colors.green.shade200),
      ),
      child: Column(
        children: [
          Text(
            'Risk Level: ${_result!.spikeRisk}',
            style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color:
                    _result!.spikeRisk == "High" ? Colors.red : Colors.green),
          ),
          const SizedBox(height: 24),
          _buildTrendChart(),
          const SizedBox(height: 24),
          _buildPredictionRow(
              '30 min', '${_result!.predictions['30min'] ?? 0} mg/dL'),
          _buildPredictionRow(
              '60 min', '${_result!.predictions['60min'] ?? 0} mg/dL'),
          _buildPredictionRow(
              '90 min', '${_result!.predictions['90min'] ?? 0} mg/dL'),
          _buildPredictionRow(
              '120 min', '${_result!.predictions['120min'] ?? 0} mg/dL'),
          const Divider(height: 32, color: Colors.black26),
          Text(
            'Advice: ${_result!.advice}',
            textAlign: TextAlign.center,
            style: const TextStyle(fontStyle: FontStyle.italic, color: Colors.black87, fontSize: 15),
          ),
          const SizedBox(height: 24),
          OutlinedButton.icon(
            onPressed: () async {
              setState(() => _isLoading = true);
              try {
                final result = await ApiService.explainSpike(
                    ProfileService().profile?.id ?? 1);
                if (!mounted) return;
                setState(() => _isLoading = false);
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) =>
                        ExplainAIScreen(explanationData: result),
                  ),
                );
              } catch (e) {
                if (!mounted) return;
                setState(() => _isLoading = false);
                ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Error: $e')));
              }
            },
            icon: const Icon(Icons.auto_awesome),
            label: const Text('Explain Prediction', style: TextStyle(fontWeight: FontWeight.bold)),
            style: OutlinedButton.styleFrom(
               padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
               shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          )
        ],
      ),
    );
  }

  Widget _buildTrendChart() {
    final values = [
      (_result!.predictions['30min'] ?? 0).toDouble(),
      (_result!.predictions['60min'] ?? 0).toDouble(),
      (_result!.predictions['90min'] ?? 0).toDouble(),
      (_result!.predictions['120min'] ?? 0).toDouble(),
    ];
    final maxVal = values.reduce((a, b) => a > b ? a : b);
    final safeMaxVal = maxVal == 0 ? 1 : maxVal;

    return Container(
      height: 150,
      margin: const EdgeInsets.only(top: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: values.map((v) {
          final barHeight = (v / safeMaxVal) * 90 + 20; // Max ~110
          return Column(
            mainAxisAlignment: MainAxisAlignment.end,
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 35,
                height: barHeight,
                decoration: BoxDecoration(
                  color: _result!.spikeRisk == "High" ? Colors.red.shade400 : Colors.green.shade400,
                  borderRadius: const BorderRadius.vertical(top: Radius.circular(6)),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                '${v.toInt()}', 
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.black87)
              ),
            ],
          );
        }).toList(),
      ),
    );
  }

  Widget _buildPredictionRow(String period, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(period, style: const TextStyle(fontSize: 16, color: Colors.black87, fontWeight: FontWeight.w500)),
          Text(value,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.black87)),
        ],
      ),
    );
  }
}
