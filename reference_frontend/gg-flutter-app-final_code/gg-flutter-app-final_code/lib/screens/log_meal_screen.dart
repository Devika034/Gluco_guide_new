import 'package:flutter/material.dart';
import '../services/diet_service.dart';

class LogMealScreen extends StatefulWidget {
  const LogMealScreen({super.key});

  @override
  State<LogMealScreen> createState() => _LogMealScreenState();
}

class _LogMealScreenState extends State<LogMealScreen> {
  final List<FoodEntry> _foods = [FoodEntry()];
  bool _isLoading = false;

  void _addFoodRow() {
    setState(() {
      _foods.add(FoodEntry());
    });
  }

  void _removeFoodRow(int index) {
    if (_foods.length > 1) {
      setState(() {
        _foods.removeAt(index);
      });
    }
  }

  void _logMeal() async {
    // Standard serving weights in grams for common items
    final Map<String, double> standardServings = {
      "rice": 150.0,
      "idli": 50.0,
      "dosa": 80.0,
      "chapati": 40.0,
      "roti": 40.0,
      "appam": 50.0,
      "bread": 25.0
    };

    // Collect valid foods
    final List<Map<String, dynamic>> payload = [];
    for (var entry in _foods) {
      if (entry.controller.text.trim().isNotEmpty) {
        
        // Parse the quantity from the text field directly, default to 100 if invalid
        double parsedQuantity = 100.0;
        try {
          if (entry.quantityController.text.trim().isNotEmpty) {
            parsedQuantity = double.parse(entry.quantityController.text.trim());
          }
        } catch (e) {
          // If parsing fails (e.g., they typed in words instead of numbers), we just stick with 100.0
          // or you could optionally show an error message.
        }

        if (entry.unit == 'Pieces' || entry.unit == 'Bowls') {
          String foodNameLower = entry.controller.text.trim().toLowerCase();
          double multiplier = 100.0; // Default to 100g per piece if not found in list
          
          for (var key in standardServings.keys) {
            if (foodNameLower.contains(key)) {
              multiplier = standardServings[key]!;
              break;
            }
          }
          parsedQuantity = parsedQuantity * multiplier;
        }

        payload.add({
          "food_name": entry.controller.text.trim(),
          "quantity_g": parsedQuantity // Send exact grams to backend
        });
      }
    }

    if (payload.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter at least one food item.')),
      );
      return;
    }

    setState(() => _isLoading = true);
    final response = await DietService().logMeal(payload);
    if (!mounted) return;
    setState(() => _isLoading = false);

    if (response != null) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Meal Logged successfully'),
          content: Text(
              'Average GI: ${response["avg_gi"]?.toStringAsFixed(1) ?? "0.0"}\nTotal GL: ${response["total_gl"]?.toStringAsFixed(1) ?? "0.0"}'),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(ctx);
                Navigator.pop(context);
              },
              child: const Text('OK'),
            )
          ],
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to log meal. Please check food items.')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Log a Meal', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.indigo,
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.indigo.shade50, Colors.white],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'What did you eat?',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'Enter the food items and quantities to calculate the meal\'s impact.',
              style: TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: ListView.builder(
                itemCount: _foods.length,
                itemBuilder: (context, index) {
                  return _buildFoodRow(index);
                },
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _addFoodRow,
              icon: const Icon(Icons.add_circle_outline),
              label: const Text('Add Another Food Item'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
                backgroundColor: Colors.indigo.shade100,
                foregroundColor: Colors.indigo.shade900,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
            const SizedBox(height: 32),
            Container(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(16),
                boxShadow: [
                  BoxShadow(
                    color: Colors.indigo.withOpacity(0.3),
                    blurRadius: 12,
                    offset: const Offset(0, 6),
                  ),
                ],
              ),
              child: ElevatedButton(
                onPressed: _isLoading ? null : _logMeal,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  backgroundColor: Colors.indigo,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                  ),
                ),
                child: _isLoading
                    ? const CircularProgressIndicator(color: Colors.white)
                    : const Text('Log and Analyze',
                        style: TextStyle(fontSize: 18)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFoodRow(int index) {
    final entry = _foods[index];
    return Card(
      margin: const EdgeInsets.only(bottom: 20),
      elevation: 4,
      shadowColor: Colors.black12,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Food ${index + 1}',
                  style: const TextStyle(fontWeight: FontWeight.bold)),
              if (_foods.length > 1)
                IconButton(
                  icon: const Icon(Icons.close, color: Colors.red),
                  onPressed: () => _removeFoodRow(index),
                  tooltip: 'Remove',
                ),
            ],
          ),
          const SizedBox(height: 8),
          TextField(
            controller: entry.controller,
            decoration: InputDecoration(
              labelText: 'Food Item (e.g., Puttu, Appam)',
              labelStyle: TextStyle(color: Colors.indigo.shade300),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: Colors.indigo.shade100),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: BorderSide(color: Colors.indigo.shade100),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
                borderSide: const BorderSide(color: Colors.indigo, width: 2),
              ),
              prefixIcon: const Icon(Icons.fastfood, color: Colors.indigo),
              filled: true,
              fillColor: Colors.indigo.shade50.withOpacity(0.5),
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              const Text('Quantity: ', style: TextStyle(fontSize: 14)),
              const SizedBox(width: 8),
              Expanded(
                flex: 2,
                child: TextField(
                  controller: entry.quantityController,
                  keyboardType: TextInputType.number,
                  decoration: InputDecoration(
                    hintText: 'e.g., 150',
                    hintStyle: TextStyle(color: Colors.indigo.shade200),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: BorderSide(color: Colors.indigo.shade100),
                    ),
                    enabledBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: BorderSide(color: Colors.indigo.shade100),
                    ),
                    focusedBorder: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                      borderSide: const BorderSide(color: Colors.indigo, width: 2),
                    ),
                    filled: true,
                    fillColor: Colors.white,
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                flex: 1,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  decoration: BoxDecoration(
                    color: Colors.indigo.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.indigo.shade100),
                  ),
                  child: DropdownButtonHideUnderline(
                    child: DropdownButton<String>(
                      value: entry.unit,
                      isExpanded: true,
                      icon: const Icon(Icons.arrow_drop_down, color: Colors.indigo),
                      style: const TextStyle(color: Colors.indigo, fontSize: 13, fontWeight: FontWeight.bold),
                      items: <String>['Grams', 'Pieces', 'Bowls'].map((String value) {
                        return DropdownMenuItem<String>(
                          value: value,
                          child: Text(value),
                        );
                      }).toList(),
                      onChanged: (String? newValue) {
                        if (newValue != null) {
                          setState(() {
                            entry.unit = newValue;
                            // Smart toggle logic to help the user
                            if ((newValue == 'Pieces' || newValue == 'Bowls') && entry.quantityController.text == "100") {
                              entry.quantityController.text = "1";
                            } else if (newValue == 'Grams' && (entry.quantityController.text == "1" || entry.quantityController.text == "2")) {
                              entry.quantityController.text = "100";
                            }
                          });
                        }
                      },
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    ),
  );
}
}

class FoodEntry {
  final TextEditingController controller = TextEditingController();
  final TextEditingController quantityController = TextEditingController(text: "100"); // Default 100g
  String unit = 'Grams';
}
