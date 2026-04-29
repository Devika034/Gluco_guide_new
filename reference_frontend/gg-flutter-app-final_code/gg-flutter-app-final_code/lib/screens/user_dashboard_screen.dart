import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../services/profile_service.dart';
import '../services/theme_service.dart';
import '../services/api_service.dart';

class UserDashboardScreen extends StatefulWidget {
  const UserDashboardScreen({super.key});

  @override
  State<UserDashboardScreen> createState() => _UserDashboardScreenState();
}

class _UserDashboardScreenState extends State<UserDashboardScreen> {
  bool _isEditing = false;
  bool _isLoading = false;

  final _nameController = TextEditingController();
  final _ageController = TextEditingController();
  final _weightController = TextEditingController();
  final _heightController = TextEditingController();
  final _medicationController = TextEditingController();

  double? _parseDouble(dynamic value) {
    if (value == null) return null;
    if (value is num) return value.toDouble();
    if (value is String) return double.tryParse(value);
    return null;
  }

  @override
  void initState() {
    super.initState();
    final profile = ProfileService().profile;
    if (profile != null) {
      _nameController.text = profile.name;
      _ageController.text = profile.age.toString();
      _weightController.text = profile.weight.toString();
      _heightController.text = profile.height.toString();
      _medicationController.text = profile.medication;
    }
  }

  Future<void> _pickAndExtractReport() async {
    final result = await FilePicker.platform
        .pickFiles(type: FileType.custom, allowedExtensions: ['pdf', 'jpg', 'jpeg', 'png'], withData: true, allowMultiple: true);
    if (result == null || result.files.isEmpty) return;

    setState(() => _isLoading = true);
    try {
      final userId = ProfileService().profile?.id ?? 1;
      final reports = result.files
          .where((f) => f.bytes != null)
          .map((f) => {'bytes': f.bytes!, 'name': f.name})
          .toList();

      if (reports.isEmpty) return;
      
      final data = await ApiService.analyzeDiabeticRiskBytes(userId, reports);
      final values = data['extracted_values'];

      if (values != null) {
        await ProfileService().updateProfile(
          lastHbA1c: _parseDouble(values['hba1c']),
          lastFastingGlucose: _parseDouble(values['fasting_glucose']),
          lastSystolicBP: _parseDouble(values['bp_systolic']),
          lastDiastolicBP: _parseDouble(values['bp_diastolic']),
          cholesterol: _parseDouble(values['cholesterol']),
          uacr: _parseDouble(values['uacr']),
          egfr: _parseDouble(values['egfr']),
          medicalNotes: data['clinical_explanation'] as String?,
        );
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
                content: Text('Medical data extracted and updated!')),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Extraction failed: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _saveChanges() async {
    setState(() => _isLoading = true);
    try {
      await ProfileService().updateProfile(
        name: _nameController.text,
        age: int.tryParse(_ageController.text),
        weight: double.tryParse(_weightController.text),
        height: double.tryParse(_heightController.text),
        medication: _medicationController.text,
      );
      setState(() => _isEditing = false);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Save failed: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Profile'),
        actions: [
          IconButton(
            icon: Icon(_isEditing ? Icons.save : Icons.edit),
            onPressed: _isLoading
                ? null
                : (_isEditing
                    ? _saveChanges
                    : () => setState(() => _isEditing = true)),
          )
        ],
      ),
      body: ListenableBuilder(
        listenable: ProfileService(),
        builder: (context, child) {
          final profile = ProfileService().profile;
          if (profile == null) {
            return const Center(child: Text("No Profile Found"));
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              children: [
                _buildProfileHeader(profile.name),
                const SizedBox(height: 24),
                if (_isLoading) const LinearProgressIndicator(),
                _buildSectionTitle('Physical Metrics'),
                _buildEditableMetric('Name', _nameController, _isEditing),
                _buildEditableMetric('Age', _ageController, _isEditing,
                    keyboardType: TextInputType.number),
                _buildEditableMetric(
                    'Weight (kg)', _weightController, _isEditing,
                    keyboardType: TextInputType.number),
                _buildEditableMetric(
                    'Height (cm)', _heightController, _isEditing,
                    keyboardType: TextInputType.number),
                _buildMetricRow('BMI', profile.bmi.toStringAsFixed(1)),
                _buildSectionTitle('Behavioral Data'),
                _buildMetricRow(
                    'Sleeping Hours', '${profile.sleepingHours.toInt()}h'),
                _buildMetricRow('Alcohol', profile.alcoholConsumption),
                _buildMetricRow('Smoking', profile.smokingStatus),
                _buildSectionTitle('Clinical Summary'),
                _buildMetricRow(
                    'HbA1c',
                    profile.lastHbA1c != null
                        ? '${profile.lastHbA1c}%'
                        : 'N/A'),
                _buildMetricRow(
                    'Fasting Glucose',
                    profile.lastFastingGlucose != null
                        ? '${profile.lastFastingGlucose} mg/dL'
                        : 'N/A'),
                _buildMetricRow(
                    'Blood Pressure',
                    (profile.lastSystolicBP != null && profile.lastDiastolicBP != null)
                        ? '${profile.lastSystolicBP?.toInt()}/${profile.lastDiastolicBP?.toInt()} mmHg'
                        : (profile.lastSystolicBP != null ? '${profile.lastSystolicBP?.toInt()} mmHg' : 'N/A')),
                _buildMetricRow(
                    'Cholesterol',
                    profile.cholesterol != null
                        ? '${profile.cholesterol} mg/dL'
                        : 'N/A'),
                _buildMetricRow(
                    'UACR',
                    profile.uacr != null
                        ? '${profile.uacr} mg/g'
                        : 'N/A'),
                _buildMetricRow(
                    'eGFR',
                    profile.egfr != null
                        ? '${profile.egfr} mL/min/1.73m²'
                        : 'N/A'),
                _buildMetricRow(
                    'Daily Medication',
                    profile.medicationDose != null
                        ? '${profile.medicationDose} mg'
                        : 'N/A'),
                if (profile.medicalNotes != null && profile.medicalNotes!.isNotEmpty)
                   Padding(
                     padding: const EdgeInsets.symmetric(vertical: 8.0),
                     child: Column(
                       crossAxisAlignment: CrossAxisAlignment.start,
                       children: [
                         const Text('Medical Notes', style: TextStyle(fontSize: 16)),
                         const SizedBox(height: 4),
                         Text(profile.medicalNotes!,
                             style: const TextStyle(fontSize: 14, color: Colors.black54)),
                       ],
                     ),
                   ),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: _isLoading ? null : _pickAndExtractReport,
                  icon: const Icon(Icons.upload_file),
                  label: const Text('Update via Medical Report'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.indigo.shade50,
                    foregroundColor: Colors.indigo,
                  ),
                ),
                const SizedBox(height: 16),
                ElevatedButton.icon(
                  onPressed: _isLoading
                      ? null
                      : () async {
                          final userId = ProfileService().profile?.id ?? 1;
                          try {
                            await ApiService.downloadHealthSummary(userId);
                          } catch (e) {
                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(content: Text('Download failed: $e')),
                              );
                            }
                          }
                        },
                  icon: const Icon(Icons.download),
                  label: const Text('Download Health Summary'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.green.shade50,
                    foregroundColor: Colors.green,
                  ),
                ),
                _buildSectionTitle('App Settings'),
                ListenableBuilder(
                  listenable: ThemeService(),
                  builder: (context, _) {
                    return SwitchListTile(
                      title: const Text('Dark Mode'),
                      secondary: Icon(ThemeService().isDarkMode
                          ? Icons.dark_mode
                          : Icons.light_mode),
                      value: ThemeService().isDarkMode,
                      onChanged: (val) => ThemeService().toggleTheme(val),
                    );
                  },
                ),
                const SizedBox(height: 40),
                ElevatedButton(
                  onPressed: () {
                    ProfileService().logout();
                    Navigator.of(context).popUntil((route) => route.isFirst);
                  },
                  style: ElevatedButton.styleFrom(
                      minimumSize: const Size(double.infinity, 50),
                      backgroundColor: Colors.red.shade50,
                      foregroundColor: Colors.red),
                  child: const Text('Logout'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildProfileHeader(String name) {
    return Center(
      child: Column(
        children: [
          const CircleAvatar(radius: 50, child: Icon(Icons.person, size: 50)),
          const SizedBox(height: 12),
          Text(name,
              style:
                  const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(top: 24, bottom: 8),
      child: Align(
        alignment: Alignment.centerLeft,
        child: Text(title,
            style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.indigo)),
      ),
    );
  }

  Widget _buildMetricRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 16)),
          Text(value,
              style:
                  const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Widget _buildEditableMetric(
      String label, TextEditingController controller, bool isEditing,
      {TextInputType keyboardType = TextInputType.text}) {
    if (!isEditing) return _buildMetricRow(label, controller.text);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: TextField(
        controller: controller,
        keyboardType: keyboardType,
        decoration: InputDecoration(
          labelText: label,
          border: const UnderlineInputBorder(),
          contentPadding: EdgeInsets.zero,
        ),
      ),
    );
  }
}
