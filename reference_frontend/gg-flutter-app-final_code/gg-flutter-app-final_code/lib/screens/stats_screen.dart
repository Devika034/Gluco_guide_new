import 'package:flutter/material.dart';
import '../services/diet_service.dart';

class StatsScreen extends StatelessWidget {
  const StatsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: const Text('Historical Trends',
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
        child: ListenableBuilder(
          listenable: DietService(),
          builder: (context, child) {
            final diet = DietService();
            return SafeArea(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildStatsOverview(diet),
                    const SizedBox(height: 40),
                    const Text('Glucose History (Simulated)',
                        style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: Colors.white)),
                    const SizedBox(height: 16),
                    _buildDummyChart(context),
                    const SizedBox(height: 40),
                    const Text('Recent Meal Impact',
                        style: TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: Colors.white)),
                    const SizedBox(height: 16),
                    if (diet.logs.isEmpty)
                      Center(
                        child: Padding(
                          padding: const EdgeInsets.all(48.0),
                          child: Text('No meal logs yet.',
                              style: TextStyle(
                                  color: Colors.white.withOpacity(0.5))),
                        ),
                      )
                    else
                      ...diet.logs.reversed
                          .take(5)
                          .map((log) => _buildLogItem(log)),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildStatsOverview(DietService diet) {
    return Row(
      children: [
        _buildStatCard('Cumulative GL', diet.consumedGL.toStringAsFixed(1),
            Icons.show_chart, Colors.orange),
        const SizedBox(width: 12),
        _buildStatCard('Logs Count', diet.logs.length.toString(), Icons.history,
            Colors.blue),
      ],
    );
  }

  Widget _buildStatCard(
      String label, String value, IconData icon, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.1),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: Colors.white.withOpacity(0.2)),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 28),
            const SizedBox(height: 12),
            Text(value,
                style: const TextStyle(
                    fontSize: 26,
                    fontWeight: FontWeight.bold,
                    color: Colors.white)),
            Text(label,
                style: TextStyle(
                    fontSize: 13, color: Colors.white.withOpacity(0.6))),
          ],
        ),
      ),
    );
  }

  Widget _buildDummyChart(BuildContext context) {
    return Container(
      height: 220,
      width: double.infinity,
      decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.05),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: Colors.white.withOpacity(0.1))),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: CustomPaint(
          painter: ChartPainter(
            color: Colors.greenAccent,
            gridColor: Colors.white.withOpacity(0.1),
          ),
        ),
      ),
    );
  }

  Widget _buildLogItem(dynamic log) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Theme(
        data: ThemeData.dark().copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          shape: const RoundedRectangleBorder(side: BorderSide.none),
          collapsedShape: const RoundedRectangleBorder(side: BorderSide.none),
          leading: CircleAvatar(
              backgroundColor: _getRiskColor(log.riskLevel).withOpacity(0.8),
              radius: 8),
          title: Text(log.items.map((e) => e.food).join(', '),
              style: const TextStyle(
                  fontWeight: FontWeight.bold, color: Colors.white)),
          subtitle: Text(
              'Impact: ${log.totalGL} GL • ${log.timestamp.toString().substring(11, 16)}',
              style: TextStyle(color: Colors.white.withOpacity(0.6))),
          trailing: Text(log.riskLevel,
              style: TextStyle(
                  color: _getRiskColor(log.riskLevel),
                  fontWeight: FontWeight.bold)),
          children: [
            if (log.alternatives.isNotEmpty)
              Padding(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('AI Suggestions (Lower GL):',
                        style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: Colors.greenAccent)),
                    const SizedBox(height: 12),
                    ...log.alternatives.map((alt) => Container(
                          margin: const EdgeInsets.only(bottom: 8),
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.05),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: ListTile(
                            dense: true,
                            title: Text(alt.food,
                                style: const TextStyle(color: Colors.white)),
                            subtitle: Text('GI: ${alt.gi} • GL: ${alt.gl}',
                                style: const TextStyle(color: Colors.white60)),
                            leading: const Icon(Icons.check_circle_outline,
                                color: Colors.greenAccent, size: 20),
                          ),
                        )),
                  ],
                ),
              )
            else
              const Padding(
                padding: EdgeInsets.all(20.0),
                child: Text('No alternatives suggested for this meal.',
                    style: TextStyle(
                        fontStyle: FontStyle.italic,
                        fontSize: 13,
                        color: Colors.white38)),
              ),
          ],
        ),
      ),
    );
  }

  Color _getRiskColor(String risk) {
    switch (risk) {
      case 'High':
        return Colors.red;
      case 'Moderate':
        return Colors.orange;
      default:
        return Colors.green;
    }
  }
}

class ChartPainter extends CustomPainter {
  final Color color;
  final Color gridColor;

  ChartPainter({required this.color, required this.gridColor});

  @override
  void paint(Canvas canvas, Size size) {
    final gridPaint = Paint()
      ..color = gridColor
      ..strokeWidth = 0.5;

    // Draw horizontal grid lines
    for (int i = 1; i <= 5; i++) {
      double y = size.height * (i / 6);
      canvas.drawLine(Offset(0, y), Offset(size.width, y), gridPaint);
    }

    final paint = Paint()
      ..color = color
      ..strokeWidth = 3.0
      ..style = PaintingStyle.stroke;
    final path = Path();
    path.moveTo(0, size.height * 0.7);
    path.quadraticBezierTo(size.width * 0.2, size.height * 0.4,
        size.width * 0.4, size.height * 0.6);
    path.quadraticBezierTo(size.width * 0.6, size.height * 0.8,
        size.width * 0.8, size.height * 0.3);
    path.lineTo(size.width, size.height * 0.5);
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => false;
}
