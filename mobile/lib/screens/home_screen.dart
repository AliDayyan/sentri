import 'package:flutter/material.dart';
import 'scan_screen.dart';
import '../services/api_service.dart';

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
            const Text(
              'Recent Scans',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
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
        _loadHistory(); // refresh history after returning from a scan
      },
      icon: Icon(icon),
      label: Text(label),
      style: ElevatedButton.styleFrom(
        padding: const EdgeInsets.symmetric(vertical: 16.0),
      ),
    );
  }
}