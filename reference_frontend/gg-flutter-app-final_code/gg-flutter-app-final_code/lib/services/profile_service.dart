import 'package:flutter/material.dart';
import '../models/user_profile.dart';
import 'api_service.dart';

class ProfileService extends ChangeNotifier {
  // Singleton pattern
  static final ProfileService _instance = ProfileService._internal();
  factory ProfileService() => _instance;
  ProfileService._internal();

  UserProfile? _profile;

  UserProfile? get profile => _profile;

  bool get isUserLoggedIn => _profile != null;

  void setProfile(UserProfile profile) {
    _profile = profile;
    notifyListeners();
  }

  Future<void> updateProfile({
    String? name,
    int? age,
    double? weight,
    double? height,
    String? dietPreference,
    String? medication,
    bool? hasFamilyHistory,
    double? sleepingHours,
    String? alcoholConsumption,
    String? smokingStatus,
    double? lastHbA1c,
    double? lastFastingGlucose,
    double? lastSystolicBP,
    double? lastDiastolicBP,
    double? cholesterol,
    double? uacr,
    double? egfr,
    double? medicationDose,
    String? medicalNotes,
  }) async {
    if (_profile != null) {
      if (name != null) _profile!.name = name;
      if (age != null) _profile!.age = age;
      if (weight != null) _profile!.weight = weight;
      if (height != null) _profile!.height = height;
      if (dietPreference != null) _profile!.dietPreference = dietPreference;
      if (medication != null) _profile!.medication = medication;
      if (hasFamilyHistory != null)
        _profile!.hasFamilyHistory = hasFamilyHistory;
      if (sleepingHours != null) _profile!.sleepingHours = sleepingHours;
      if (alcoholConsumption != null)
        _profile!.alcoholConsumption = alcoholConsumption;
      if (smokingStatus != null) _profile!.smokingStatus = smokingStatus;
      if (lastHbA1c != null) _profile!.lastHbA1c = lastHbA1c;
      if (lastFastingGlucose != null)
        _profile!.lastFastingGlucose = lastFastingGlucose;
      if (lastSystolicBP != null) _profile!.lastSystolicBP = lastSystolicBP;
      if (lastDiastolicBP != null) _profile!.lastDiastolicBP = lastDiastolicBP;
      if (cholesterol != null) _profile!.cholesterol = cholesterol;
      if (uacr != null) _profile!.uacr = uacr;
      if (egfr != null) _profile!.egfr = egfr;
      if (medicationDose != null) _profile!.medicationDose = medicationDose;
      if (medicalNotes != null) _profile!.medicalNotes = medicalNotes;

      // Sync with backend - disabled in unified flow
      // await ApiService.updateProfile(_profile!);

      notifyListeners();
    }
  }

  void logout() {
    _profile = null;
    notifyListeners();
  }
}
