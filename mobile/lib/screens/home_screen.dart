import 'package:flutter/material.dart';
import 'scan_screen.dart';
import 'stats_screen.dart';
import 'auth_screen.dart';
import '../services/api_service.dart';
import '../main.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Map<String, dynamic>> _scans = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final scans = await ApiService.getHistory();
      setState(() {
        _scans = scans;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load history';
        _isLoading = false;
      });
    }
  }

  Future<void> _confirmClearHistory() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Clear Scan History?'),
        content: const Text(
          'This will permanently delete all your saved scan results. This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await ApiService.clearHistory();
        _loadHistory();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('History cleared.')),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Failed to clear history.')),
          );
        }
      }
    }
  }

  void _showPrivacyInfo() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Your Privacy'),
        content: const Text(
          'Sentri analyzes the content you scan to detect scams and threats. '
          'Scan results (risk level, score, and a short preview) are stored locally '
          'in this app\'s history so you can review past scans. You can delete this '
          'history at any time using the "Clear History" option.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }

  Future<void> _logout() async {
    await ApiService.logout();
    if (mounted) {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (context) => const AuthScreen()),
      );
    }
  }

  void _toggleTheme() {
    final appState = SentriApp.of(context);
    if (appState == null) return;

    final current = appState.themeMode;
    ThemeMode next;
    if (current == ThemeMode.light) {
      next = ThemeMode.dark;
    } else if (current == ThemeMode.dark) {
      next = ThemeMode.system;
    } else {
      next = ThemeMode.light;
    }
    setState(() {
      appState.setThemeMode(next);
    });
  }

  IconData _themeIcon() {
    final mode = SentriApp.of(context)?.themeMode ?? ThemeMode.system;
    switch (mode) {
      case ThemeMode.light:
        return Icons.light_mode;
      case ThemeMode.dark:
        return Icons.dark_mode;
      case ThemeMode.system:
        return Icons.brightness_auto;
    }
  }

  Color _riskColor(String? level) {
    switch (level) {
      case 'CRITICAL':
        return Colors.red;
      case 'HIGH':
        return Colors.deepOrange;
      case 'MEDIUM':
        return Colors.amber;
      case 'LOW':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }

  IconData _scanTypeIcon(String? type) {
    switch (type) {
      case 'message':
        return Icons.message_outlined;
      case 'url':
        return Icons.link;
      case 'image':
        return Icons.image_outlined;
      default:
        return Icons.shield_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('SENTRI'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: Icon(_themeIcon()),
            tooltip: 'Toggle Theme',
            onPressed: _toggleTheme,
          ),
          IconButton(
            icon: const Icon(Icons.bar_chart),
            tooltip: 'Stats',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => const StatsScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.privacy_tip_outlined),
            tooltip: 'Privacy Info',
            onPressed: _showPrivacyInfo,
          ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Log Out',
            onPressed: _logout,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadHistory,
        child: ListView(
          padding: const EdgeInsets.all(24.0),
          children: [
            const SizedBox(height: 8),
            const Text(
              'Is something suspicious happening?',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            _buildScanButton(context, 'Scan Message', Icons.message_outlined, ScanType.message),
            const SizedBox(height: 12),
            _buildScanButton(context, 'Scan URL', Icons.link, ScanType.url),
            const SizedBox(height: 12),
            _buildScanButton(context, 'Scan Screenshot', Icons.image_outlined, ScanType.screenshot),
            const SizedBox(height: 32),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Recent Scans',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                if (_scans.isNotEmpty)
                  TextButton.icon(
                    onPressed: _confirmClearHistory,
                    icon: const Icon(Icons.delete_outline, size: 18, color: Colors.red),
                    label: const Text('Clear', style: TextStyle(color: Colors.red)),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            _buildHistorySection(),
          ],
        ),
      ),
    );
  }

  Widget _buildHistorySection() {
    if (_isLoading) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 24),
        child: Center(child: CircularProgressIndicator()),
      );
    }

    if (_error != null) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 24),
        child: Center(
          child: Text(_error!, style: const TextStyle(color: Colors.grey)),
        ),
      );
    }

    if (_scans.isEmpty) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 24),
        child: Center(
          child: Text('No scans yet.', style: TextStyle(color: Colors.grey)),
        ),
      );
    }

    return Column(
      children: _scans.map((scan) {
        final color = _riskColor(scan['risk_level']);
        return Card(
          margin: const EdgeInsets.only(bottom: 8),
          child: ListTile(
            leading: Icon(_scanTypeIcon(scan['scan_type']), color: color),
            title: Text(
              scan['content_preview'] ?? '',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            subtitle: Text(scan['summary'] ?? '', maxLines: 1, overflow: TextOverflow.ellipsis),
            trailing: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: color.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: color),
              ),
              child: Text(
                '${scan['risk_level']}',
                style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 12),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildScanButton(BuildContext context, String label, IconData icon, ScanType type) {
    return ElevatedButton.icon(
      onPressed: () async {
        await Navigator.push(
          context,
          MaterialPageRoute(builder: (context) => ScanScreen(scanType: type)),
        );
        _loadHistory();
      },
      icon: Icon(icon),
      label: Text(label),
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 16.0),
      ),
    );
  }
}