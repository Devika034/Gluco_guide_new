import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../models/user_profile.dart';
import '../services/profile_service.dart';
import '../services/api_service.dart';
import 'home_screen.dart';

class PreferencesScreen extends StatefulWidget {
  final String name;
  final String email;
  final String password;

  const PreferencesScreen({
    super.key,
    required this.name,
    required this.email,
    required this.password,
  });

  @override
  State<PreferencesScreen> createState() => _PreferencesScreenState();
}

class _PreferencesScreenState extends State<PreferencesScreen> {
  final _ageController = TextEditingController();
  final _durationController = TextEditingController();
  final _weightController = TextEditingController();
  final _heightController = TextEditingController();
  String _dietPreference = "Veg";
  bool _hasFamilyHistory = false;
  double _sleepingHours = 8.0;
  String _activityLevel = "Sedentary";
  String _alcoholSmoking = "No";
  List<Map<String, dynamic>> _reports = [];

  bool _isLoading = false;

  Future<void> _pickReport() async {
    FilePickerResult? pickResult = await FilePicker.platform
        .pickFiles(type: FileType.custom, allowedExtensions: ['pdf', 'jpg', 'jpeg', 'png'], withData: true, allowMultiple: true);

    if (pickResult != null && pickResult.files.isNotEmpty) {
      setState(() {
        _reports.addAll(pickResult.files
            .where((f) => f.bytes != null)
            .map((f) => {'bytes': f.bytes!, 'name': f.name})
            .toList());
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Selected: ${_reports.length} report(s)')),
      );
    }
  }

  Future<void> _savePreferences() async {
    setState(() => _isLoading = true);
    try {
      final data = {
        "full_name": widget.name,
        "email": widget.email,
        "password": widget.password,
        "age": int.tryParse(_ageController.text) ?? 30,
        "gender": "Not Specified",
        "height_cm": double.tryParse(_heightController.text) ?? 170.0,
        "weight_kg": double.tryParse(_weightController.text) ?? 70.0,
        "activity_level": _activityLevel == "Very Active" ? 2 : (_activityLevel == "Active" ? 0 : 1),
        "family_history": _hasFamilyHistory ? 1 : 0,
        "alcohol_smoking": _alcoholSmoking == "Yes" ? 1 : 0,
        "duration_years": int.tryParse(_durationController.text) ?? 1,
        "medication_dose": 0.0,
      };

      // 1. Register user on backend via unified endpoint
      final response = await ApiService.signup(data);
      int userId = response["user_id"] ?? 1;

      Map<String, dynamic>? medicalValues;
      String? medicalNotes;

      // 1.5. If a medical report was attached during onboarding, upload it now
      if (_reports.isNotEmpty) {
        try {
          final data = await ApiService.analyzeDiabeticRiskBytes(userId, _reports);
          medicalValues = data['extracted_values'];
          medicalNotes = data['clinical_explanation'];
        } catch (e) {
          debugPrint("Report upload during onboarding failed: $e");
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('Profile created but report upload failed: $e')),
            );
          }
        }
      }

      double? _parseDouble(dynamic value) {
        if (value == null) return null;
        if (value is num) return value.toDouble();
        if (value is String) return double.tryParse(value);
        return null;
      }

      // 2. Create profile locally
      final profile = UserProfile(
        id: userId,
        email: widget.email,
        name: widget.name,
        age: int.tryParse(_ageController.text) ?? 30,
        weight: double.tryParse(_weightController.text) ?? 70.0,
        height: double.tryParse(_heightController.text) ?? 170.0,
        dietPreference: _dietPreference,
        hasFamilyHistory: _hasFamilyHistory,
        sleepingHours: _sleepingHours,
        activityLevel: _activityLevel,
        alcoholConsumption: _alcoholSmoking == "Yes" ? "Regularly" : "Never",
        smokingStatus: _alcoholSmoking == "Yes" ? "Current" : "Never",
        lastHbA1c: _parseDouble(medicalValues?['hba1c']),
        lastFastingGlucose: _parseDouble(medicalValues?['fasting_glucose']),
        lastSystolicBP: _parseDouble(medicalValues?['bp_systolic']),
        lastDiastolicBP: _parseDouble(medicalValues?['bp_diastolic']),
        cholesterol: _parseDouble(medicalValues?['cholesterol']),
        uacr: _parseDouble(medicalValues?['uacr']),
        egfr: _parseDouble(medicalValues?['egfr']),
        medicalNotes: medicalNotes,
      );

      ProfileService().setProfile(profile);

      if (!mounted) return;
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const HomeScreen()),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: const Text('Preferences', style: TextStyle(color: Colors.white)),
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
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Personalize Your Experience',
                  style: TextStyle(
                      fontSize: 26,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                      letterSpacing: -0.5),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 12),
                Text(
                  'We use this data to tailor your diet and risk analysis',
                  style: TextStyle(
                      fontSize: 14, color: Colors.white.withOpacity(0.7)),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 32),
                _buildCardSection([
                  _buildClassicField(_ageController, 'Age',
                      Icons.calendar_today, TextInputType.number),
                  const SizedBox(height: 16),
                  _buildClassicField(_durationController, 'Years with Diabetes',
                      Icons.history, TextInputType.number),
                  const SizedBox(height: 16),
                  _buildClassicField(_weightController, 'Weight (kg)',
                      Icons.monitor_weight, TextInputType.number),
                  const SizedBox(height: 16),
                  _buildClassicField(_heightController, 'Height (cm)',
                      Icons.height, TextInputType.number),
                ]),
                const SizedBox(height: 24),
                _buildSectionTitle('Dietary & Lifestyle'),
                _buildCardSection([
                  Row(
                    children: [
                      Expanded(
                        child: RadioListTile<String>(
                          title: const Text('Veg',
                              style: TextStyle(color: Colors.white)),
                          value: 'Veg',
                          groupValue: _dietPreference,
                          activeColor: Colors.white,
                          onChanged: (value) =>
                              setState(() => _dietPreference = value!),
                        ),
                      ),
                      Expanded(
                        child: RadioListTile<String>(
                          title: const Text('Non-Veg',
                              style: TextStyle(color: Colors.white)),
                          value: 'Non-Veg',
                          groupValue: _dietPreference,
                          activeColor: Colors.white,
                          onChanged: (value) =>
                              setState(() => _dietPreference = value!),
                        ),
                      ),
                    ],
                  ),
                  const Divider(color: Colors.white24),
                  SwitchListTile(
                    title: const Text('Family History of Diabetes?',
                        style: TextStyle(color: Colors.white)),
                    value: _hasFamilyHistory,
                    activeColor: Colors.white,
                    onChanged: (val) => setState(() => _hasFamilyHistory = val),
                  ),
                  const Divider(color: Colors.white24),
                  Padding(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 16.0, vertical: 8.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Average Sleep: ${_sleepingHours.toInt()} hours',
                            style: const TextStyle(color: Colors.white)),
                        Slider(
                          value: _sleepingHours,
                          min: 4,
                          max: 12,
                          divisions: 8,
                          activeColor: Colors.white,
                          inactiveColor: Colors.white24,
                          onChanged: (val) =>
                              setState(() => _sleepingHours = val),
                        ),
                      ],
                    ),
                  ),
                  const Divider(color: Colors.white24),
                  _buildClassicDropdown(
                      'Activity Level',
                      _activityLevel,
                      ['Sedentary', 'Active', 'Very Active'], (val) {
                    setState(() => _activityLevel = val!);
                  }),
                  const Divider(color: Colors.white24),
                  _buildClassicDropdown(
                      'Alcohol / Smoking',
                      _alcoholSmoking,
                      ['Yes', 'No'], (val) {
                    setState(() => _alcoholSmoking = val!);
                  }),
                ]),
                const SizedBox(height: 24),
                _buildSectionTitle('Medical Records'),
                _buildCardSection([
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.picture_as_pdf_rounded, color: Colors.white70, size: 36),
                    title: Text(
                      _reports.isNotEmpty 
                          ? '${_reports.length} report(s) selected' 
                          : 'Upload Medical Reports',
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                    ),
                    subtitle: const Text('(You can upload multiple reports such as blood test, urine test etc.)',
                        style: TextStyle(color: Colors.white54, fontSize: 12)),
                    trailing: ElevatedButton(
                      onPressed: _isLoading ? null : _pickReport,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.white24,
                        foregroundColor: Colors.white,
                        elevation: 0,
                      ),
                      child: const Text('Browse'),
                    ),
                  ),
                ]),
                const SizedBox(height: 40),
                ElevatedButton(
                  onPressed: _isLoading ? null : _savePreferences,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 18),
                    backgroundColor: Colors.white,
                    foregroundColor: Colors.indigo.shade900,
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16)),
                    elevation: 10,
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          height: 24,
                          width: 24,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.indigo),
                        )
                      : const Text('Complete Onboarding',
                          style: TextStyle(
                              fontSize: 18, fontWeight: FontWeight.bold)),
                ),
                const SizedBox(height: 24),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildCardSection(List<Widget> children) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.1),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.white.withOpacity(0.2)),
      ),
      child: Column(children: children),
    );
  }

  Widget _buildClassicField(TextEditingController controller, String label,
      IconData icon, TextInputType type) {
    return TextField(
      controller: controller,
      keyboardType: type,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: TextStyle(color: Colors.white.withOpacity(0.7)),
        prefixIcon: Icon(icon, color: Colors.white70),
        enabledBorder: UnderlineInputBorder(
            borderSide: BorderSide(color: Colors.white.withOpacity(0.3))),
        focusedBorder: const UnderlineInputBorder(
            borderSide: BorderSide(color: Colors.white)),
      ),
    );
  }

  Widget _buildClassicDropdown(String label, String value, List<String> options,
      void Function(String?) onChanged) {
    return DropdownButtonFormField<String>(
      value: value,
      dropdownColor: Colors.indigo.shade800,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: TextStyle(color: Colors.white.withOpacity(0.7)),
        enabledBorder: UnderlineInputBorder(
            borderSide: BorderSide(color: Colors.white.withOpacity(0.3))),
        focusedBorder: const UnderlineInputBorder(
            borderSide: BorderSide(color: Colors.white)),
      ),
      items: options
          .map((e) => DropdownMenuItem(value: e, child: Text(e)))
          .toList(),
      onChanged: onChanged,
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 12.0),
      child: Text(title,
          style: const TextStyle(
              fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white)),
    );
  }

  Widget _buildDropdown(String label, String value, List<String> options,
      void Function(String?) onChanged) {
    return DropdownButtonFormField<String>(
      value: value,
      decoration:
          InputDecoration(labelText: label, border: const OutlineInputBorder()),
      items: options
          .map((e) => DropdownMenuItem(value: e, child: Text(e)))
          .toList(),
      onChanged: onChanged,
    );
  }
}
