import 'package:flutter/material.dart';

enum ScanType { message, url, screenshot }

class ScanScreen extends StatefulWidget {
  final ScanType scanType;

  const ScanScreen({super.key, required this.scanType});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  final TextEditingController _controller = TextEditingController();
  bool _isLoading = false;
  Map<String, dynamic>? _result;

  String get _title {
    switch (widget.scanType) {
      case ScanType.message:
        return 'Scan Message';
      case ScanType.url:
        return 'Scan URL';
      case ScanType.screenshot:
        return 'Scan Screenshot';
    }
  }

  String get _hint {
    switch (widget.scanType) {
      case ScanType.message:
        return 'Paste the suspicious message here...';
      case ScanType.url:
        return 'Paste the URL here...';
      case ScanType.screenshot:
        return '';
    }
  }

  Future<void> _runScan() async {
    setState(() {
      _isLoading = true;
      _result = null;
    });

    // Mock scan delay — will be replaced with real API call in Phase 4/5
    await Future.delayed(const Duration(seconds: 2));

    setState(() {
      _isLoading = false;
      _result = {
        'risk_level': 'LOW',
        'risk_score': 12,
        'summary': 'No significant threats detected in this content.',
      };
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_title)),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (widget.scanType == ScanType.screenshot)
              _buildScreenshotPicker()
            else
              TextField(
                controller: _controller,
                maxLines: 6,
                decoration: InputDecoration(
                  hintText: _hint,
                  border: const OutlineInputBorder(),
                ),
              ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _isLoading ? null : _runScan,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16.0),
              ),
              child: _isLoading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Text('Scan Now'),
            ),
            const SizedBox(height: 32),
            if (_result != null) _buildResultCard(),
          ],
        ),
      ),
    );
  }

  Widget _buildScreenshotPicker() {
    return Container(
      height: 200,
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade400),
        borderRadius: BorderRadius.circular(8),
      ),
      child: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.upload_file, size: 48, color: Colors.grey),
            SizedBox(height: 8),
            Text('Tap to upload a screenshot', style: TextStyle(color: Colors.grey)),
          ],
        ),
      ),
    );
  }

  Widget _buildResultCard() {
    final riskLevel = _result!['risk_level'];
    final riskScore = _result!['risk_score'];
    final summary = _result!['summary'];

    Color riskColor;
    switch (riskLevel) {
      case 'CRITICAL':
        riskColor = Colors.red;
        break;
      case 'HIGH':
        riskColor = Colors.deepOrange;
        break;
      case 'MEDIUM':
        riskColor = Colors.amber;
        break;
      default:
        riskColor = Colors.green;
    }

    return Card(
      color: riskColor.withValues(alpha: 0.1),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: riskColor),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.shield, color: riskColor),
                const SizedBox(width: 8),
                Text(
                  '$riskLevel — $riskScore/100',
                  style: TextStyle(fontWeight: FontWeight.bold, color: riskColor, fontSize: 16),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(summary),
          ],
        ),
      ),
    );
  }
}