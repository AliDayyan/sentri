import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class SentriApiException implements Exception {
  final String message;
  final int? statusCode;
  SentriApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

class ApiService {
  static const String baseUrl = 'http://10.0.2.2:8001';

  static Future<Map<String, dynamic>> analyzeMessage(String message) async {
    final response = await _post('/analyze/message', {'content': message});
    return _handleResponse(response);
  }

  static Future<Map<String, dynamic>> analyzeUrl(String url) async {
    final response = await _post('/analyze/url', {'content': url});
    return _handleResponse(response);
  }

  static Future<Map<String, dynamic>> analyzeImage(File imageFile) async {
    try {
      final request = http.MultipartRequest('POST', Uri.parse('$baseUrl/analyze/image'));
      request.files.add(await http.MultipartFile.fromPath('file', imageFile.path));
      final streamedResponse = await request.send().timeout(const Duration(seconds: 20));
      final response = await http.Response.fromStream(streamedResponse);
      return _handleResponse(response);
    } on SocketException {
      throw SentriApiException('No internet connection. Check your network and try again.');
    } on http.ClientException {
      throw SentriApiException('Could not reach the Sentri server.');
    }
  }

  static Future<List<Map<String, dynamic>>> getHistory() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/history')).timeout(const Duration(seconds: 10));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        return List<Map<String, dynamic>>.from(data['scans']);
      } else {
        throw SentriApiException('Failed to load history.', statusCode: response.statusCode);
      }
    } on SocketException {
      throw SentriApiException('No internet connection.');
    }
  }

  static Future<void> clearHistory() async {
    final response = await http.delete(Uri.parse('$baseUrl/history'));
    if (response.statusCode != 200) {
      throw SentriApiException('Failed to clear history.');
    }
  }

  static Future<Map<String, dynamic>> getStats() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/stats')).timeout(const Duration(seconds: 10));
      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        throw SentriApiException('Failed to load stats.', statusCode: response.statusCode);
      }
    } on SocketException {
      throw SentriApiException('No internet connection.');
    }
  }

  static Future<http.Response> _post(String path, Map<String, dynamic> body) async {
    try {
      return await http
          .post(
            Uri.parse('$baseUrl$path'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 20));
    } on SocketException {
      throw SentriApiException('No internet connection. Check your network and try again.');
    } on http.ClientException {
      throw SentriApiException('Could not reach the Sentri server. Is it running?');
    }
  }

  static Map<String, dynamic> _handleResponse(http.Response response) {
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    } else if (response.statusCode == 429) {
      throw SentriApiException(
        'Daily scan limit reached. Upgrade to Pro for unlimited scans.',
        statusCode: 429,
      );
    } else if (response.statusCode >= 500) {
      throw SentriApiException('Sentri server is having trouble. Please try again shortly.', statusCode: response.statusCode);
    } else {
      throw SentriApiException('Something went wrong. Please try again.', statusCode: response.statusCode);
    }
  }
}