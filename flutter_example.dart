import 'dart:convert';
import 'package:http/http.dart' as http;

class SabdaApiService {
  static const String baseUrl = 'https://your-api-domain.com'; // Replace with your deployed URL
  static const String apiKey = 'sabda_flutter_2025_secure_key';
  
  String? _token;
  DateTime? _tokenExpiry;

  // Get authentication token
  Future<bool> authenticate() async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/auth/token'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'api_key': apiKey,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['status'] == 'success') {
          _token = data['data']['token'];
          _tokenExpiry = DateTime.parse(data['metadata']['expires_at']);
          return true;
        }
      }
      return false;
    } catch (e) {
      print('Authentication error: $e');
      return false;
    }
  }

  // Check if token is valid
  bool get isAuthenticated {
    return _token != null && 
           _tokenExpiry != null && 
           DateTime.now().isBefore(_tokenExpiry!);
  }

  // Get SABDA content
  Future<Map<String, dynamic>?> getSabdaContent(int year, String date) async {
    // Authenticate if needed
    if (!isAuthenticated) {
      bool authSuccess = await authenticate();
      if (!authSuccess) {
        throw Exception('Authentication failed');
      }
    }

    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/sabda?year=$year&date=$date'),
        headers: {
          'Authorization': 'Bearer $_token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['status'] == 'success') {
          return data['data'];
        } else {
          throw Exception(data['message']);
        }
      } else if (response.statusCode == 401) {
        // Token expired, re-authenticate
        _token = null;
        _tokenExpiry = null;
        return await getSabdaContent(year, date);
      } else {
        throw Exception('HTTP ${response.statusCode}: ${response.body}');
      }
    } catch (e) {
      print('API error: $e');
      rethrow;
    }
  }
}

// Usage example in Flutter widget
class SabdaWidget extends StatefulWidget {
  @override
  _SabdaWidgetState createState() => _SabdaWidgetState();
}

class _SabdaWidgetState extends State<SabdaWidget> {
  final SabdaApiService _apiService = SabdaApiService();
  Map<String, dynamic>? _devotionalData;
  bool _isLoading = false;
  String? _error;

  Future<void> _loadDevotional() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final data = await _apiService.getSabdaContent(2025, '0902');
      setState(() {
        _devotionalData = data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('SABDA Devotional')),
      body: Column(
        children: [
          ElevatedButton(
            onPressed: _isLoading ? null : _loadDevotional,
            child: Text('Load Today\'s Devotional'),
          ),
          if (_isLoading) CircularProgressIndicator(),
          if (_error != null) Text('Error: $_error'),
          if (_devotionalData != null) ...[
            Text(_devotionalData!['title'] ?? ''),
            Text(_devotionalData!['scripture_reference'] ?? ''),
            Text(_devotionalData!['devotional_title'] ?? ''),
            // Add more UI elements as needed
          ],
        ],
      ),
    );
  }
}
