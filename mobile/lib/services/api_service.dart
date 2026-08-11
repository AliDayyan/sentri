import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // 10.0.2.2 is the special alias Android emulators use to reach the host machine's localhost
  static const String baseUrl = 'http://10.0.2.2:8001';
  
  static Future<Map<String, dynamic>> analyzeMessage(String message) async {
    final response = await http.post(
      Uri.parse('$baseUrl/analyze/message'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'content': message}),
    );
    return _handleResponse(response);
  }

  static Future<Map<String, dynamic>> analyzeUrl(String url) async {
    final response = await http.post(
      Uri.parse('$baseUrl/analyze/url'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'content': url}),
    );
    return _handleResponse(response);
  }

  static Future<Map<String, dynamic>> analyzeImage() async {
    final response = await http.post(
      Uri.parse('$baseUrl/analyze/image'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({}),
    );
    return _handleResponse(response);
  }

  static Map<String, dynamic> _handleResponse(http.Response response) {
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else {
      throw Exception('API error: ${response.statusCode} ${response.body}');
    }
  }
}