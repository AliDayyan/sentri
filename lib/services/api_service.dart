static Future<List<Map<String, dynamic>>> getHistory() async {
    final response = await http.get(Uri.parse('$baseUrl/history'));
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      return List<Map<String, dynamic>>.from(data['scans']);
    } else {
      throw Exception('Failed to load history');
    }
  }
  