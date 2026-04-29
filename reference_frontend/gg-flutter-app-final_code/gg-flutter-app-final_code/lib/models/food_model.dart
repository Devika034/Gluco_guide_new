class MealItem {
  final String food;
  final String quantity;
  final double gi;
  final double gl;
  final String type; // "Veg" or "Non-Veg"
  final String explanation;

  MealItem({
    required this.food,
    required this.quantity,
    required this.gi,
    required this.gl,
    required this.type,
    this.explanation = "",
  });

  Map<String, dynamic> toJson() => {
        'food': food,
        'quantity': quantity,
        'GI': gi,
        'GL': gl,
        'veg_nonveg': type,
        'explanation': explanation,
      };

  factory MealItem.fromJson(Map<String, dynamic> json) {
    return MealItem(
      food: json['food']?.toString() ?? "",
      quantity: json['quantity']?.toString() ?? "",
      gi: double.tryParse(json['GI']?.toString() ?? '0') ?? 0.0,
      gl: double.tryParse(json['GL']?.toString() ?? '0') ?? 0.0,
      type: json['veg_nonveg']?.toString() ?? "Veg",
      explanation: json['explanation']?.toString() ?? json['Reasoning']?.toString() ?? "",
    );
  }
}

class DietPlan {
  final List<MealItem> breakfast;
  final List<MealItem> lunch;
  final List<MealItem> dinner;
  final String planType; // "Strict" or "Normal"

  DietPlan({
    required this.breakfast,
    required this.lunch,
    required this.dinner,
    required this.planType,
  });

  factory DietPlan.fromJson(Map<String, dynamic> json) {
    var meals = json['meal_plan'] ?? {};
    return DietPlan(
      breakfast: (meals['breakfast'] as List? ?? [])
          .map((e) => MealItem.fromJson(e))
          .toList(),
      lunch: (meals['lunch'] as List? ?? [])
          .map((e) => MealItem.fromJson(e))
          .toList(),
      dinner: (meals['dinner'] as List? ?? [])
          .map((e) => MealItem.fromJson(e))
          .toList(),
      planType: json['plan_type'] ?? "Normal",
    );
  }
}

class MealLog {
  final DateTime timestamp;
  final List<MealItem> items;
  final double totalGL;
  final String riskLevel;

  final List<MealItem> alternatives;

  MealLog({
    required this.timestamp,
    required this.items,
    required this.totalGL,
    required this.riskLevel,
    this.alternatives = const [],
  });
}
