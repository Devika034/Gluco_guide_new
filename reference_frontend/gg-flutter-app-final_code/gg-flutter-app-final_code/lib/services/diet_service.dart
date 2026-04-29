import 'dart:convert';
import 'package:flutter/material.dart';
import '../models/food_model.dart';
import '../models/food_analysis.dart';
import '../models/spike_prediction.dart';
import 'api_service.dart';
import 'profile_service.dart';
import 'health_service.dart';

class DietService extends ChangeNotifier {
  static final DietService _instance = DietService._internal();
  factory DietService() => _instance;
  DietService._internal();

  bool _isLoading = false;
  DietPlan? _todaysPlan;
  String? _aiAdvice;
  final List<MealLog> _logs = [];
  double _consumedGL = 0.0;

  bool get isLoading => _isLoading;
  DietPlan? get todaysPlan => _todaysPlan;
  String? get aiAdvice => _aiAdvice;
  List<MealLog> get logs => _logs;
  double get consumedGL => _consumedGL;

  Future<void> fetchTodaysPlan() async {
    final profile = ProfileService().profile;
    final health = HealthService();

    if (profile == null) return;

    _isLoading = true;
    notifyListeners();

    try {
      final planData = await ApiService.generateMealPlan(
        profile.id ?? 1, 
        profile.dietPreference, 
        true // Using strict diabetic meal mode as default
      );

      _todaysPlan = DietPlan.fromJson(planData);
      _consumedGL = planData['total_GL']?.toDouble() ?? 0.0;
    } catch (e) {
      debugPrint("Error fetching plan: $e");
      throw Exception("Failed to generate diet plan. Please try again. ($e)");
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<Map<String, dynamic>?> logMeal(List<Map<String, dynamic>> foods) async {
    final profile = ProfileService().profile;
    if (profile == null || foods.isEmpty) return null;

    _isLoading = true;
    notifyListeners();

    try {
      final response = await ApiService.logMeal(
          profile.id ?? 1,
          foods
      );

      final double currentGL = response['total_gl']?.toDouble() ?? 0.0;
      final double currentGI = response['avg_gi']?.toDouble() ?? 0.0;
      
      final items = foods.map((f) => MealItem(
          food: f['food_name'] as String,
          quantity: (f['quantity_g'] as double).toString(),
          gi: currentGI,
          gl: currentGL,
          type: "Veg / Non-Veg",
          explanation: "Logged via dashboard",
      )).toList();

      final newLog = MealLog(
        timestamp: DateTime.now(),
        items: items,
        totalGL: currentGL,
        riskLevel: "Low",
        alternatives: [],
      );

      _logs.add(newLog);
      _consumedGL += newLog.totalGL;

      return response;
    } catch (e) {
      debugPrint("Error logging meal: $e");
      return null;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<SpikePredictionResult?> predictSpike(
      double currentGlucose, int timeOfDay) async {
    final profile = ProfileService().profile;
    if (profile == null) return null;

    try {
      final rawResponse = await ApiService.predictSpike(
        profile.id ?? 1,
        currentGlucose,
        timeOfDay
      );
      
      return SpikePredictionResult.fromJson(rawResponse);
    } catch (e) {
      debugPrint("Error predicting spike: $e");
      rethrow;
    }
  }

  Future<void> confirmMeal(String mealType, String food, double gl) async {
    final profile = ProfileService().profile;
    if (profile == null) return;

    try {
      _consumedGL += gl;
      notifyListeners();
    } catch (e) {
      debugPrint("Error confirming meal: $e");
    }
  }

  Future<void> fetchAdaptivePlan() async {
    final profile = ProfileService().profile;
    if (profile == null) return;

    try {
      _aiAdvice = "No analysis available.";
      notifyListeners();
    } catch (e) {
      debugPrint("Error fetching adaptive plan: $e");
    }
  }
}
