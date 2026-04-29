import '../services/profile_service.dart';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import 'explain_ai_screen.dart';

class ComplicationsScreen extends StatefulWidget {
  const ComplicationsScreen({super.key});

  @override
  State<ComplicationsScreen> createState() => _ComplicationsScreenState();
}

class _ComplicationsScreenState extends State<ComplicationsScreen> {
  Map<String, dynamic>? _result;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _loadRiskData();
  }

  void _loadRiskData() async {
    setState(() {
      _isLoading = true;
    });
    try {
      final result = await ApiService.predictRiskFromDb(
          ProfileService().profile?.id ?? 1);
      setState(() => _result = result);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error analyzing risk: $e')));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: const Text('Complications Risk',
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
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.1),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.biotech_rounded,
                      size: 64, color: Colors.white),
                ),
                const SizedBox(height: 24),
                const Text(
                  'Diabetic Complications Assessment',
                  style: TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                      letterSpacing: -0.5),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 12),
                Text(
                  'Analysis of your long-term risks for Neuropathy, Retinopathy, and Nephropathy based on your medical profile.',
                  style: TextStyle(
                      color: Colors.white.withOpacity(0.7), fontSize: 16),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 40),
                if (_isLoading) ...[
                  const CircularProgressIndicator(color: Colors.white),
                  const SizedBox(height: 16),
                  const Text('Calculating risks...',
                      style: TextStyle(color: Colors.white70)),
                ] else if (_result != null)
                  _buildRiskResults(),
              ],
            ),
          ),
        ),
      ),
    );
  }

  double _parseRisk(dynamic val) {
    if (val == null) return 0.0;
    String s = val.toString().replaceAll('%', '');
    return (double.tryParse(s) ?? 0.0) / 100.0;
  }

  Widget _buildRiskResults() {
    return Column(
      children: [
        _buildRiskCard(
            'Neuropathy',
            _parseRisk(_result!['neuropathy']?['5_years']),
            _parseRisk(_result!['neuropathy']?['10_years'])),
        const SizedBox(height: 16),
        _buildRiskCard(
            'Retinopathy',
            _parseRisk(_result!['retinopathy']?['5_years']),
            _parseRisk(_result!['retinopathy']?['10_years'])),
        const SizedBox(height: 16),
        _buildRiskCard(
            'Nephropathy',
            _parseRisk(_result!['nephropathy']?['5_years']),
            _parseRisk(_result!['nephropathy']?['10_years'])),
            
        const SizedBox(height: 32),
        if (!_isLoading && _result != null)
          OutlinedButton.icon(
            onPressed: () async {
              setState(() => _isLoading = true);
              try {
                final result = await ApiService.explainRisk(
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
            icon: const Icon(Icons.psychology_outlined),
            label: const Text('Why? (Explain AI)', style: TextStyle(fontWeight: FontWeight.bold)),
            style: OutlinedButton.styleFrom(
               padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
               shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
               foregroundColor: Colors.white,
               side: BorderSide(color: Colors.white.withOpacity(0.5))
            ),
          )
      ],
    );
  }

  Widget _buildRiskCard(String title, double risk5, double risk10) {
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withOpacity(0.2)),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 10,
              offset: const Offset(0, 4))
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title,
                  style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: Colors.white)),
              Icon(Icons.warning_amber_rounded,
                  color: risk10 > 0.5 ? Colors.redAccent : Colors.orangeAccent,
                  size: 24),
            ],
          ),
          const SizedBox(height: 16),
          _buildRiskBar('5 Year Likelihood', risk5),
          const SizedBox(height: 12),
          _buildRiskBar('10 Year Likelihood', risk10),
        ],
      ),
    );
  }

  Widget _buildRiskBar(String label, double value) {
    Color barColor = value < 0.3
        ? Colors.greenAccent
        : (value < 0.6 ? Colors.orangeAccent : Colors.redAccent);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label,
                style: const TextStyle(fontSize: 13, color: Colors.white70)),
            Text('${(value * 100).toInt()}%',
                style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: barColor)),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(10),
          child: LinearProgressIndicator(
              value: value,
              minHeight: 10,
              backgroundColor: Colors.white.withOpacity(0.05),
              color: barColor),
        ),
      ],
    );
  }
}
