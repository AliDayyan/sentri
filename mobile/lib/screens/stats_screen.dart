import 'package:flutter/material.dart';
import '../services/api_service.dart';

class StatsScreen extends StatefulWidget {
  const StatsScreen({super.key});

  @override
  State<StatsScreen> createState() => _StatsScreenState();
}

class _StatsScreenState extends State<StatsScreen> {
  Map<String, dynamic>? _stats;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final stats = await ApiService.getStats();
      setState(() {
        _stats = stats;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Failed to load stats.';
        _isLoading = false;
      });
    }
  }

  Color _riskColor(String level) {
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Stats')),
      body: RefreshIndicator(
        onRefresh: _loadStats,
        child: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(child: Text(_error!, style: const TextStyle(color: Colors.grey)));
    }

    final total = _stats!['total_scans'] as int;
    final avgScore = _stats!['average_risk_score'];
    final byRisk = Map<String, dynamic>.from(_stats!['by_risk_level']);
    final byType = Map<String, dynamic>.from(_stats!['by_scan_type']);

    return ListView(
      padding: const EdgeInsets.all(24.0),
      children: [
        Row(
          children: [
            Expanded(child: _buildStatCard('Total Scans', '$total', Colors.blue)),
            const SizedBox(width: 12),
            Expanded(child: _buildStatCard('Avg Risk Score', '$avgScore', Colors.orange)),
          ],
        ),
        const SizedBox(height: 32),
        const Text('Risk Level Breakdown', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        ...byRisk.entries
            .where((e) => e.value > 0)
            .map((e) => _buildBarRow(e.key, e.value, total, _riskColor(e.key))),
        const SizedBox(height: 32),
        const Text('Scans by Type', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
        const SizedBox(height: 12),
        ...byType.entries
            .where((e) => e.value > 0)
            .map((e) => _buildBarRow(e.key, e.value, total, Colors.blueAccent)),
      ],
    );
  }

  Widget _buildStatCard(String label, String value, Color color) {
    return Card(
      color: color.withValues(alpha: 0.1),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: color),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            Text(value, style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: color)),
            const SizedBox(height: 4),
            Text(label, style: const TextStyle(fontSize: 13, color: Colors.grey)),
          ],
        ),
      ),
    );
  }

  Widget _buildBarRow(String label, int value, int total, Color color) {
    final fraction = total > 0 ? value / total : 0.0;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label, style: const TextStyle(fontWeight: FontWeight.w600)),
              Text('$value', style: const TextStyle(color: Colors.grey)),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: fraction,
              minHeight: 10,
              backgroundColor: Colors.grey.shade200,
              valueColor: AlwaysStoppedAnimation<Color>(color),
            ),
          ),
        ],
      ),
    );
  }
}