class FoodItem {
  final String food;
  final double quantity;

  FoodItem({required this.food, this.quantity = 1.0});

  Map<String, dynamic> toJson() => {
        'food': food,
        'quantity': quantity,
      };
}

class MealInput {
  final String patientName;
  final String preference;
  final List<FoodItem> meals;

  MealInput({
    required this.patientName,
    required this.preference,
    required this.meals,
  });

  Map<String, dynamic> toJson() => {
        'patient_name': patientName,
        'preference': preference,
        'meals': meals.map((m) => m.toJson()).toList(),
      };
}

class MealRecommendation {
  final String food;
  final String quantity;
  final double gi;
  final double gl;
  final String vegNonVeg;
  final String explanation;

  MealRecommendation({
    required this.food,
    required this.quantity,
    required this.gi,
    required this.gl,
    required this.vegNonVeg,
    required this.explanation,
  });

  factory MealRecommendation.fromJson(Map<String, dynamic> json) {
    return MealRecommendation(
      food: json['food'],
      quantity: json['quantity'],
      gi: json['GI'].toDouble(),
      gl: json['GL'].toDouble(),
      vegNonVeg: json['veg_nonveg'],
      explanation: json['explanation'],
    );
  }
}

class PatientProfile {
  final String patientName;
  final double fastingGlucose;
  final double hba1c;
  final double currentGlucose;
  final String preference;

  PatientProfile({
    required this.patientName,
    required this.fastingGlucose,
    required this.hba1c,
    required this.currentGlucose,
    required this.preference,
  });

  Map<String, dynamic> toJson() => {
        'patient_name': patientName,
        'fasting_glucose': fastingGlucose,
        'hba1c': hba1c,
        'current_glucose': currentGlucose,
        'preference': preference,
      };
}
