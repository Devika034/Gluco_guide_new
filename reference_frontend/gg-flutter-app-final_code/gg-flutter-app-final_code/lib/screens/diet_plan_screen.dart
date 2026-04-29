import 'package:flutter/material.dart';
import '../services/diet_service.dart';
import 'log_meal_screen.dart';

class DietPlanScreen extends StatelessWidget {
  const DietPlanScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title:
            const Text('My Diet Plan', style: TextStyle(color: Colors.white)),
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

            if (diet.isLoading) {
              return const Center(
                  child: CircularProgressIndicator(color: Colors.white));
            }

            if (diet.todaysPlan == null) {
              return Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(32),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.1),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.restaurant_menu_rounded,
                          size: 64, color: Colors.white38),
                    ),
                    const SizedBox(height: 24),
                    const Text('No plan generated for today yet.',
                        style: TextStyle(color: Colors.white70, fontSize: 18)),
                    const SizedBox(height: 32),
                    ElevatedButton(
                      onPressed: () async {
                        try {
                          await diet.fetchTodaysPlan();
                        } catch (e) {
                          if (!context.mounted) return;
                          ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Failed: $e')));
                        }
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white,
                        foregroundColor: Colors.indigo.shade900,
                        padding: const EdgeInsets.symmetric(
                            horizontal: 40, vertical: 16),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(16)),
                      ),
                      child: const Text('Generate Today\'s Plan',
                          style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                  ],
                ),
              );
            }

            return SafeArea(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(20.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildSummaryHeader(context, diet),
                    if (diet.aiAdvice != null) ...[
                      const SizedBox(height: 24),
                      _buildAICoachCard(context, diet.aiAdvice!),
                    ],
                    const SizedBox(height: 32),
                    _buildMealSection(
                        context,
                        'Breakfast',
                        diet.todaysPlan!.breakfast,
                        Icons.wb_sunny_rounded,
                        Colors.orangeAccent,
                        diet),
                    _buildMealSection(context, 'Lunch', diet.todaysPlan!.lunch,
                        Icons.wb_cloudy_rounded, Colors.blueAccent, diet),
                    _buildMealSection(
                        context,
                        'Dinner',
                        diet.todaysPlan!.dinner,
                        Icons.nightlight_round,
                        Colors.indigoAccent,
                        diet),
                    const SizedBox(height: 40),
                    Center(
                      child: ElevatedButton.icon(
                        onPressed: () => Navigator.push(
                            context,
                            MaterialPageRoute(
                                builder: (context) => const LogMealScreen())),
                        icon: const Icon(Icons.add_rounded),
                        label: const Text('Log a Meal',
                            style: TextStyle(
                                fontSize: 18, fontWeight: FontWeight.bold)),
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 48, vertical: 20),
                          backgroundColor: Colors.greenAccent.shade700,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(20)),
                          elevation: 8,
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                  ],
                ),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildSummaryHeader(BuildContext context, DietService diet) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withOpacity(0.2)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildSummaryItem(
              'Daily Glycemic Load',
              diet.consumedGL.toStringAsFixed(1),
              Icons.bolt_rounded,
              Colors.orangeAccent),
          Container(height: 40, width: 1, color: Colors.white24),
          _buildSummaryItem('Active Goal', diet.todaysPlan!.planType,
              Icons.track_changes_rounded, Colors.blueAccent),
        ],
      ),
    );
  }

  Widget _buildAICoachCard(BuildContext context, String advice) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.greenAccent.withOpacity(0.15),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.greenAccent.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.auto_awesome_rounded, color: Colors.greenAccent),
              const SizedBox(width: 8),
              const Text('AI Health Coach',
                  style: TextStyle(
                      color: Colors.greenAccent, fontWeight: FontWeight.bold)),
            ],
          ),
          const SizedBox(height: 12),
          Text(advice,
              style: const TextStyle(color: Colors.white, fontSize: 14)),
        ],
      ),
    );
  }

  Widget _buildSummaryItem(
      String label, String value, IconData icon, Color color) {
    return Column(
      children: [
        Icon(icon, color: color, size: 28),
        const SizedBox(height: 8),
        Text(value,
            style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: Colors.white)),
        Text(label,
            style: const TextStyle(fontSize: 12, color: Colors.white60)),
      ],
    );
  }

  Widget _buildMealSection(BuildContext context, String title, List items,
      IconData icon, Color color, DietService diet) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 16.0),
          child: Row(
            children: [
              Icon(icon, color: color, size: 24),
              const SizedBox(width: 12),
              Text(title,
                  style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: Colors.white)),
            ],
          ),
        ),
        ...items.map((item) => Container(
              margin: const EdgeInsets.only(bottom: 12),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.1),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: Colors.white.withOpacity(0.15)),
              ),
              child: ListTile(
                contentPadding:
                    const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
                title: Text(item.food,
                    style: const TextStyle(
                        color: Colors.white, fontWeight: FontWeight.bold)),
                subtitle: Text('${item.quantity} • ${item.type}',
                    style: const TextStyle(color: Colors.white60)),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text('GL: ${item.gl}',
                            style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                color: Colors.greenAccent)),
                        Text('GI: ${item.gi}',
                            style: const TextStyle(
                                fontSize: 10, color: Colors.white54)),
                      ],
                    ),
                    const SizedBox(width: 16),
                    IconButton(
                        onPressed: () {
                          diet.confirmMeal(title, item.food, item.gl);
                          ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Logged ${item.food}')));
                        },
                        icon: const Icon(Icons.check_circle_outline_rounded,
                            color: Colors.greenAccent)),
                  ],
                ),
              ),
            )),
        const SizedBox(height: 8),
      ],
    );
  }
}
