import ComingSoon from '@/components/stub/ComingSoon';

export default function NodeDetailPage() {
  return (
    <ComingSoon
      title="Node Detail"
      description="Per-node time-series charts and sensor diagnostics."
      bullets={[
        '24h multi-channel chart (rain tips, accel RMS, tilt delta, crack delta)',
        'Battery and signal strength trends',
        'ML prediction probability over time',
        'Acknowledge / resolve alert action from node context',
      ]}
    />
  );
}
