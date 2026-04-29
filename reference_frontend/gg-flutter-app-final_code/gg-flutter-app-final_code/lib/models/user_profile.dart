class UserProfile {
  int? id;
  String email;
  String name;
  int age;
  double weight; // in kg
  double height; // in cm
  String dietPreference; // "Veg" or "Non-Veg"
  String medication;
  bool hasFamilyHistory;
  double sleepingHours;
  String activityLevel; // "Sedentary", "Active", "Very Active"
  String alcoholConsumption; // "Never", "Occasionally", "Regularly"
  String smokingStatus; // "Never", "Former", "Current"

  // Extracted Medical Data
  double? lastHbA1c;
  double? lastFastingGlucose;
  double? lastSystolicBP;
  double? lastDiastolicBP;
  double? cholesterol;
  double? uacr;
  double? egfr;
  double? medicationDose;
  String? medicalNotes;

  UserProfile({
    this.id,
    required this.email,
    required this.name,
    required this.age,
    required this.weight,
    required this.height,
    required this.dietPreference,
    this.medication = "",
    this.hasFamilyHistory = false,
    this.sleepingHours = 8.0,
    this.activityLevel = "Sedentary",
    this.alcoholConsumption = "Never",
    this.smokingStatus = "Never",
    this.lastHbA1c,
    this.lastFastingGlucose,
    this.lastSystolicBP,
    this.lastDiastolicBP,
    this.cholesterol,
    this.uacr,
    this.egfr,
    this.medicationDose,
    this.medicalNotes,
  });

  double get bmi {
    if (height == 0) return 0;
    double heightInMeters = height / 100;
    return weight / (heightInMeters * heightInMeters);
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'name': name,
        'age': age,
        'weight': weight,
        'height': height,
        'dietPreference': dietPreference,
        'medication': medication,
        'hasFamilyHistory': hasFamilyHistory,
        'sleepingHours': sleepingHours,
        'activityLevel': activityLevel,
        'alcoholConsumption': alcoholConsumption,
        'smokingStatus': smokingStatus,
        'lastHbA1c': lastHbA1c,
        'lastFastingGlucose': lastFastingGlucose,
        'lastSystolicBP': lastSystolicBP,
        'lastDiastolicBP': lastDiastolicBP,
        'cholesterol': cholesterol,
        'uacr': uacr,
        'egfr': egfr,
        'medicationDose': medicationDose,
        'medicalNotes': medicalNotes,
      };

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
        id: json['id'],
        email: json['email'] ?? "",
        name: json['name'],
        age: json['age'],
        weight: json['weight'],
        height: json['height'],
        dietPreference: json['dietPreference'],
        medication: json['medication'] ?? "",
        hasFamilyHistory: json['hasFamilyHistory'] ?? false,
        sleepingHours: (json['sleepingHours'] ?? 8.0).toDouble(),
        activityLevel: json['activityLevel'] ?? "Sedentary",
        alcoholConsumption: json['alcoholConsumption'] ?? "Never",
        smokingStatus: json['smokingStatus'] ?? "Never",
        lastHbA1c: json['lastHbA1c']?.toDouble(),
        lastFastingGlucose: json['lastFastingGlucose']?.toDouble(),
        lastSystolicBP: json['lastSystolicBP']?.toDouble(),
        lastDiastolicBP: json['lastDiastolicBP']?.toDouble(),
        cholesterol: json['cholesterol']?.toDouble(),
        uacr: json['uacr']?.toDouble(),
        egfr: json['egfr']?.toDouble(),
        medicationDose: json['medicationDose']?.toDouble(),
        medicalNotes: json['medicalNotes'],
      );
}
