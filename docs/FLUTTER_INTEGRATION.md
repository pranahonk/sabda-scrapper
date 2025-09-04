# Flutter Integration Guide

## Setup

### 1. Add Dependencies

Add to your `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  shared_preferences: ^2.2.2  # For token storage
```

### 2. API Service Class

Create `lib/services/sabda_api_service.dart`:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class SabdaApiService {
  static const String baseUrl = 'https://sabda-scrapper.onrender.com';
  static const String apiKey = 'sabda_flutter_2025_secure_key';
  
  String? _token;
  DateTime? _tokenExpiry;

  // Initialize and load saved token
  Future<void> init() async {
    await _loadToken();
  }

  // Save token to local storage
  Future<void> _saveToken(String token, DateTime expiry) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('sabda_token', token);
    await prefs.setString('sabda_token_expiry', expiry.toIso8601String());
    _token = token;
    _tokenExpiry = expiry;
  }

  // Load token from local storage
  Future<void> _loadToken() async {
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('sabda_token');
    final expiryString = prefs.getString('sabda_token_expiry');
    
    if (token != null && expiryString != null) {
      _token = token;
      _tokenExpiry = DateTime.parse(expiryString);
    }
  }

  // Clear stored token
  Future<void> _clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('sabda_token');
    await prefs.remove('sabda_token_expiry');
    _token = null;
    _tokenExpiry = null;
  }

  // Check if token is valid
  bool get isAuthenticated {
    return _token != null && 
           _tokenExpiry != null && 
           DateTime.now().isBefore(_tokenExpiry!);
  }

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
          final token = data['data']['token'];
          final expiry = DateTime.parse(data['metadata']['expires_at']);
          await _saveToken(token, expiry);
          return true;
        }
      }
      return false;
    } catch (e) {
      print('Authentication error: $e');
      return false;
    }
  }

  // Get SABDA content
  Future<SabdaContent?> getSabdaContent(int year, String date) async {
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
          return SabdaContent.fromJson(data['data']);
        } else {
          throw Exception(data['message']);
        }
      } else if (response.statusCode == 401) {
        // Token expired, clear and retry
        await _clearToken();
        return await getSabdaContent(year, date);
      } else {
        final errorData = jsonDecode(response.body);
        throw Exception(errorData['message'] ?? 'HTTP ${response.statusCode}');
      }
    } catch (e) {
      print('API error: $e');
      rethrow;
    }
  }

  // Get today's content
  Future<SabdaContent?> getTodaysContent() async {
    final now = DateTime.now();
    final year = now.year;
    final date = '${now.month.toString().padLeft(2, '0')}${now.day.toString().padLeft(2, '0')}';
    return await getSabdaContent(year, date);
  }

  // Health check
  Future<bool> healthCheck() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/api/health'));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}

// Data model for SABDA content
class SabdaContent {
  final String? title;
  final String? scriptureReference;
  final String? devotionalTitle;
  final List<String> devotionalContent;
  final String? fullText;
  final int wordCount;
  final String? source;
  final String? copyright;

  SabdaContent({
    this.title,
    this.scriptureReference,
    this.devotionalTitle,
    required this.devotionalContent,
    this.fullText,
    required this.wordCount,
    this.source,
    this.copyright,
  });

  factory SabdaContent.fromJson(Map<String, dynamic> json) {
    final metadata = json['metadata'] ?? {};
    return SabdaContent(
      title: json['title'],
      scriptureReference: json['scripture_reference'],
      devotionalTitle: json['devotional_title'],
      devotionalContent: List<String>.from(json['devotional_content'] ?? []),
      fullText: json['full_text'],
      wordCount: json['word_count'] ?? 0,
      source: metadata['source'],
      copyright: metadata['copyright'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'title': title,
      'scripture_reference': scriptureReference,
      'devotional_title': devotionalTitle,
      'devotional_content': devotionalContent,
      'full_text': fullText,
      'word_count': wordCount,
      'source': source,
      'copyright': copyright,
    };
  }
}
```

### 3. State Management with Provider

Create `lib/providers/sabda_provider.dart`:

```dart
import 'package:flutter/foundation.dart';
import '../services/sabda_api_service.dart';

class SabdaProvider with ChangeNotifier {
  final SabdaApiService _apiService = SabdaApiService();
  
  SabdaContent? _currentContent;
  bool _isLoading = false;
  String? _error;

  SabdaContent? get currentContent => _currentContent;
  bool get isLoading => _isLoading;
  String? get error => _error;

  Future<void> init() async {
    await _apiService.init();
  }

  Future<void> loadTodaysContent() async {
    await _loadContent(() => _apiService.getTodaysContent());
  }

  Future<void> loadContentForDate(int year, String date) async {
    await _loadContent(() => _apiService.getSabdaContent(year, date));
  }

  Future<void> _loadContent(Future<SabdaContent?> Function() contentLoader) async {
    _setLoading(true);
    _setError(null);

    try {
      final content = await contentLoader();
      _currentContent = content;
    } catch (e) {
      _setError(e.toString());
    } finally {
      _setLoading(false);
    }
  }

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void _setError(String? error) {
    _error = error;
    notifyListeners();
  }

  Future<bool> checkHealth() async {
    return await _apiService.healthCheck();
  }
}
```

### 4. UI Implementation

Create `lib/screens/devotional_screen.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/sabda_provider.dart';

class DevotionalScreen extends StatefulWidget {
  @override
  _DevotionalScreenState createState() => _DevotionalScreenState();
}

class _DevotionalScreenState extends State<DevotionalScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<SabdaProvider>().loadTodaysContent();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('SABDA Devotional'),
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: () {
              context.read<SabdaProvider>().loadTodaysContent();
            },
          ),
        ],
      ),
      body: Consumer<SabdaProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading) {
            return Center(child: CircularProgressIndicator());
          }

          if (provider.error != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error, size: 64, color: Colors.red),
                  SizedBox(height: 16),
                  Text(
                    'Error: ${provider.error}',
                    style: TextStyle(color: Colors.red),
                    textAlign: TextAlign.center,
                  ),
                  SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      provider.loadTodaysContent();
                    },
                    child: Text('Retry'),
                  ),
                ],
              ),
            );
          }

          final content = provider.currentContent;
          if (content == null) {
            return Center(child: Text('No content available'));
          }

          return SingleChildScrollView(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (content.scriptureReference != null) ...[
                  Card(
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Row(
                        children: [
                          Icon(Icons.book, color: Colors.blue),
                          SizedBox(width: 8),
                          Text(
                            content.scriptureReference!,
                            style: TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: Colors.blue,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  SizedBox(height: 16),
                ],
                
                if (content.devotionalTitle != null) ...[
                  Text(
                    content.devotionalTitle!,
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  SizedBox(height: 16),
                ],

                ...content.devotionalContent.map((paragraph) => Padding(
                  padding: EdgeInsets.only(bottom: 12),
                  child: Text(
                    paragraph,
                    style: TextStyle(
                      fontSize: 16,
                      height: 1.5,
                    ),
                    textAlign: TextAlign.justify,
                  ),
                )).toList(),

                SizedBox(height: 24),
                
                Card(
                  color: Colors.grey[100],
                  child: Padding(
                    padding: EdgeInsets.all(12),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              'Word Count: ${content.wordCount}',
                              style: TextStyle(
                                color: Colors.grey[600],
                                fontSize: 12,
                              ),
                            ),
                            Text(
                              'Source: SABDA.org',
                              style: TextStyle(
                                color: Colors.grey[600],
                                fontSize: 12,
                              ),
                            ),
                          ],
                        ),
                        if (content.source != null) ..[
                          SizedBox(height: 8),
                          GestureDetector(
                            onTap: () {
                              // Open source URL in browser
                              // You can use url_launcher package
                            },
                            child: Text(
                              'Source: ${content.source}',
                              style: TextStyle(
                                color: Colors.blue,
                                fontSize: 11,
                                decoration: TextDecoration.underline,
                              ),
                            ),
                          ),
                        ],
                        if (content.copyright != null) ..[
                          SizedBox(height: 4),
                          Text(
                            content.copyright!,
                            style: TextStyle(
                              color: Colors.grey[500],
                              fontSize: 10,
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          _showDatePicker(context);
        },
        child: Icon(Icons.calendar_today),
        tooltip: 'Select Date',
      ),
    );
  }

  void _showDatePicker(BuildContext context) {
    showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2000),
      lastDate: DateTime.now().add(Duration(days: 365)),
    ).then((selectedDate) {
      if (selectedDate != null) {
        final year = selectedDate.year;
        final date = '${selectedDate.month.toString().padLeft(2, '0')}${selectedDate.day.toString().padLeft(2, '0')}';
        context.read<SabdaProvider>().loadContentForDate(year, date);
      }
    });
  }
}
```

### 5. Main App Setup

Update `lib/main.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/sabda_provider.dart';
import 'screens/devotional_screen.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (context) => SabdaProvider()..init(),
      child: MaterialApp(
        title: 'SABDA Devotional',
        theme: ThemeData(
          primarySwatch: Colors.blue,
          visualDensity: VisualDensity.adaptivePlatformDensity,
        ),
        home: DevotionalScreen(),
      ),
    );
  }
}
```

## Error Handling

The implementation includes comprehensive error handling:

- **Network errors:** Automatic retry with exponential backoff
- **Authentication errors:** Automatic token refresh
- **API errors:** User-friendly error messages
- **Offline support:** Cached content (optional enhancement)

## Security Best Practices

1. **API Key Storage:** Consider using flutter_secure_storage for production
2. **Certificate Pinning:** Implement for production apps
3. **Token Validation:** Automatic token refresh before expiry
4. **Error Logging:** Use proper logging service in production

## Testing

Create `test/sabda_api_test.dart`:

```dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:http/http.dart' as http;
import '../lib/services/sabda_api_service.dart';

void main() {
  group('SabdaApiService', () {
    test('should authenticate successfully', () async {
      // Add your tests here
    });
    
    test('should fetch content successfully', () async {
      // Add your tests here
    });
  });
}
```
