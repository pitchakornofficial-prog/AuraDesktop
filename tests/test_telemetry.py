import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from auradesktop.core.telemetry import format_rate, network_rates, bounded_percent, parse_gpu_output

class TelemetryTests(unittest.TestCase):
    def test_rate_format_uses_binary_units(self):
        self.assertEqual(format_rate(0), '0.0 B/s')
        self.assertEqual(format_rate(1024), '1.0 KB/s')
        self.assertEqual(format_rate(1024**2), '1.0 MB/s')

    def test_invalid_rates_are_unavailable(self):
        self.assertEqual(format_rate(-1), 'Unavailable')
        self.assertEqual(format_rate('bad'), 'Unavailable')
        self.assertEqual(format_rate(float('nan')), 'Unavailable')

    def test_first_network_sample_has_zero_rate(self):
        rx, tx, snapshot = network_rates(1000, 2000, 10.0, None)
        self.assertEqual((rx, tx), (0.0, 0.0))
        self.assertEqual(snapshot, (1000, 2000, 10.0))

    def test_network_rate_calculation(self):
        rx, tx, snapshot = network_rates(3000, 5000, 12.0, (1000, 1000, 10.0))
        self.assertEqual(rx, 1000.0)
        self.assertEqual(tx, 2000.0)
        self.assertEqual(snapshot, (3000, 5000, 12.0))

    def test_network_counter_reset_does_not_create_negative_rate(self):
        rx, tx, _ = network_rates(10, 20, 12.0, (1000, 2000, 10.0))
        self.assertEqual((rx, tx), (0.0, 0.0))


    def test_invalid_network_sample_does_not_poison_baseline(self):
        previous = (1000, 2000, 10.0)
        rx, tx, snapshot = network_rates('bad', 3000, 12.0, previous)
        self.assertEqual((rx, tx), (0.0, 0.0))
        self.assertEqual(snapshot, previous)

    def test_network_clock_regression_yields_zero_rates(self):
        rx, tx, snapshot = network_rates(2000, 3000, 9.0, (1000, 1000, 10.0))
        self.assertEqual((rx, tx), (0.0, 0.0))
        self.assertEqual(snapshot, (2000, 3000, 9.0))

    def test_gpu_output_parses_valid_values(self):
        self.assertEqual(parse_gpu_output('42, 67\n'), ('42% · 67 °C', 42))

    def test_gpu_output_rejects_unavailable_and_invalid_values(self):
        self.assertTrue(parse_gpu_output('N/A, N/A')[0].startswith('Unavailable'))
        self.assertTrue(parse_gpu_output('101, 55')[0].startswith('Unavailable'))
        self.assertTrue(parse_gpu_output(None)[0].startswith('Unavailable'))

    def test_percent_is_bounded_and_safe(self):
        self.assertEqual(bounded_percent(120), 100)
        self.assertEqual(bounded_percent(-2), 0)
        self.assertEqual(bounded_percent('invalid'), 0)
        self.assertEqual(bounded_percent(float('nan')), 0)

if __name__ == '__main__':
    unittest.main()
