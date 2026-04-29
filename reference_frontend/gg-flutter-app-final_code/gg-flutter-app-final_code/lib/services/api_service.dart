import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/food_analysis.dart';
import '../models/spike_prediction.dart';
import '../models/risk_prediction.dart';
import '../models/disease_tracker.dart';
import '../models/user_profile.dart';
import 'package:url_launcher/url_launcher.dart';

class ApiService {
  // Configured for running on Chrome/Web Browser directly via IP to bypass localhost resolution bugs
  static const String baseUrl = "http://127.0.0.1:8000";

  static dynamic _safeDecode(http.Response response) {
    if (response.statusCode == 200) {
      try {
        return jsonDecode(response.body);
      } catch (e) {
        throw Exception("Invalid JSON formatting: ${response.body}");
      }
    } else {
      try {
        final error = jsonDecode(response.body)['detail'] ?? "API Error";
        throw Exception(error);
      } catch (e) {
        throw Exception("HTTP ${response.statusCode}: ${response.body}");
      }
    }
  }

  // === 1. User System ===
  static Future<Map<String, dynamic>> signup(Map<String, dynamic> data) async {
    final response = await http.post(
      Uri.parse("$baseUrl/auth/signup"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(data),
    );
    return _safeDecode(response);
  }

  static Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse("$baseUrl/auth/login"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "email": email,
        "password": password
      }),
    );
    return _safeDecode(response);
  }

  // === 2. Report Upload (Module 3) ===
  static Future<Map<String, dynamic>> analyzeDiabeticRiskBytes(int userId, List<Map<String, dynamic>> filesData) async {
    var request = http.MultipartRequest(
      'POST',
      Uri.parse("$baseUrl/analyze-diabetic-risk/$userId"),
    );
    for (var fileData in filesData) {
      request.files.add(http.MultipartFile.fromBytes(
        'reports',
        fileData['bytes'] as List<int>,
        filename: fileData['name'] as String,
      ));
    }

    var streamedResponse = await request.send();
    var response = await http.Response.fromStream(streamedResponse);
    return _safeDecode(response);
  }

  static Future<Map<String, dynamic>> predictRiskFromDb(int userId) async {
    final response = await http.post(
      Uri.parse("$baseUrl/risk/predict/$userId"),
      headers: {"Content-Type": "application/json"},
    );
    return _safeDecode(response);
  }

  // === 3. Meal Recommendation (Module 1) ===
  static Future<Map<String, dynamic>> generateMealPlan(int userId, String preference, bool isStrict) async {
    final response = await http.post(
      Uri.parse("$baseUrl/meal/generate-meal-plan/$userId"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "preference": preference,
        "is_strict": isStrict
      }),
    );
    return _safeDecode(response);
  }

  static Future<Map<String, dynamic>> logMeal(int userId, List<Map<String, dynamic>> foods) async {
    final response = await http.post(
      Uri.parse("$baseUrl/meal/log-meal/$userId"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"foods": foods}),
    );
    return _safeDecode(response);
  }

  // === 4. Spike Prediction (Module 2) ===
  static Future<Map<String, dynamic>> predictSpike(int userId, double currentGlucose, int timeOfDay) async {
    final response = await http.post(
      Uri.parse("$baseUrl/spike/predict-spike/$userId"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "current_glucose": currentGlucose,
        "time_of_day": timeOfDay
      }),
    );
    return _safeDecode(response);
  }

  // === 5. Questionnaire (Module 4) ===
  static Future<Map<String, dynamic>> analyzeTracker(int userId, String disease, Map<String, int> answers) async {
    final response = await http.post(
      Uri.parse("$baseUrl/tracker/analyze/$userId/$disease"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "answers": answers
      }),
    );
    return _safeDecode(response);
  }

  static Future<Map<String, dynamic>> getQuestions(String disease) async {
    final response = await http.get(Uri.parse("$baseUrl/tracker/questions/$disease"));
    return _safeDecode(response);
  }

  // === 6. Debug Data ===
  static Future<Map<String, dynamic>> getUserDebugData(int userId) async {
    final response = await http.get(Uri.parse("$baseUrl/debug/user/$userId"));
    return _safeDecode(response);
  }

  static Future<void> downloadHealthSummary(int userId) async {
    final url = Uri.parse("$baseUrl/report/health-summary/$userId");
    if (!await launchUrl(url, mode: LaunchMode.externalApplication)) {
      throw Exception('Could not launch $url');
    }
  }

  // === 7. Module 5 Global Explanation ===
  static Future<Map<String, dynamic>> explainGlobal(int userId, Map<String, dynamic>? spikeData) async {
    final response = await http.post(
      Uri.parse("$baseUrl/explain/global"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({
        "user_id": userId,
        "spike_data": spikeData
      }),
    );
    return _safeDecode(response);
  }

  static Future<Map<String, dynamic>> explainSpike(int userId) async {
    final response = await http.get(Uri.parse("$baseUrl/explain/spike/$userId"));
    return _safeDecode(response);
  }

  static Future<Map<String, dynamic>> explainRisk(int userId) async {
    final response = await http.get(Uri.parse("$baseUrl/explain/risk/$userId"));
    return _safeDecode(response);
  }
}
