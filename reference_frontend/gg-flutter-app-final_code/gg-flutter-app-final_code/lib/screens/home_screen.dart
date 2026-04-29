import 'package:flutter/material.dart';
import '../services/profile_service.dart';
import '../services/health_service.dart';
import 'user_dashboard_screen.dart';
import 'diet_plan_screen.dart';
import 'spike_prediction_screen.dart';
import 'complications_screen.dart';
import 'symptom_check_screen.dart';
import 'stats_screen.dart';
import '../services/api_service.dart';
import 'debug_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: const Text('GlucoGuide',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.person, color: Colors.white),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(
                  builder: (context) => const UserDashboardScreen()),
            ),
          ),
        ],
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Colors.indigo.shade900,
              Colors.indigo.shade700,
              Colors.blue.shade900,
            ],
          ),
        ),
        child: ListenableBuilder(
          listenable: ProfileService(),
          builder: (context, child) {
            final profile = ProfileService().profile;
            if (profile == null) {
              return const Center(
                  child: Text("Please complete onboarding",
                      style: TextStyle(color: Colors.white)));
            }

            return SafeArea(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildWelcomeHeader(profile.name),
                    const SizedBox(height: 32),
                    const Text('Health Intelligence',
                        style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: Colors.white)),
                    const SizedBox(height: 16),
                    _buildFeatureGrid(context),
                    const SizedBox(height: 32),
                    _buildAINudge(profile.email),
                  ],
                ),
              ),
            );
          },
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => Navigator.push(
          context,
          MaterialPageRoute(builder: (context) => const DebugScreen()),
        ),
        backgroundColor: Colors.deepOrangeAccent,
        child: const Icon(Icons.bug_report_rounded, color: Colors.white),
      ),
    );
  }

  Widget _buildWelcomeHeader(String name) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Welcome back,',
            style:
                TextStyle(fontSize: 18, color: Colors.white.withOpacity(0.7))),
        Text(name,
            style: const TextStyle(
                fontSize: 34,
                fontWeight: FontWeight.bold,
                color: Colors.white,
                letterSpacing: -0.5)),
      ],
    );
  }

  Widget _buildQuickMetrics() {
    return ListenableBuilder(
      listenable: HealthService(),
      builder: (context, child) {
        final health = HealthService();
        return Row(
          children: [
            _buildMetricCard('Glucose', '${health.currentGlucose.toInt()}',
                'mg/dL', Colors.orange),
            const SizedBox(width: 12),
            _buildMetricCard(
                'HbA1c', '${health.hbA1c}%', 'Average', Colors.blue),
          ],
        );
      },
    );
  }

  Widget _buildMetricCard(
      String label, String value, String unit, Color color) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withOpacity(0.2)),
      ),
      child: Column(
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(label,
                    style: const TextStyle(
                        color: Colors.white70, fontWeight: FontWeight.w500)),
                Icon(Icons.monitor_heart, color: color, size: 20),
              ],
            ),
            const SizedBox(height: 12),
            Text(value,
                style: const TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Colors.white)),
            Text(unit,
                style: const TextStyle(fontSize: 14, color: Colors.white54)),
          ],
        ),
    );
  }

  Widget _buildFeatureGrid(BuildContext context) {
    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      childAspectRatio: 1.5,
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      children: [
        _buildFeatureItem(context, 'Diet Plan', Icons.restaurant, Colors.green,
            const DietPlanScreen()),
        _buildFeatureItem(context, 'Spike Prediction', Icons.trending_up,
            Colors.red, const SpikePredictionScreen()),
        _buildFeatureItem(context, 'Complications', Icons.biotech,
            Colors.purple, const ComplicationsScreen()),
        _buildFeatureItem(context, 'Symptom Check', Icons.edit_note,
            Colors.orange, const SymptomCheckScreen()),
      ],
    );
  }

  Widget _buildFeatureItem(BuildContext context, String title, IconData icon,
      Color color, Widget destination) {
    return InkWell(
      onTap: () => Navigator.push(
          context, MaterialPageRoute(builder: (context) => destination)),
      borderRadius: BorderRadius.circular(16),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 10,
                offset: const Offset(0, 4))
          ],
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(height: 8),
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  Widget _buildAINudge(String email) {
    return const SizedBox.shrink();
  }
}
