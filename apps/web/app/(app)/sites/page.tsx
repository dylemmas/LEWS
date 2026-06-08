import ComingSoon from '@/components/stub/ComingSoon';

export default function SitesPage() {
  return (
    <ComingSoon
      title="Sites"
      description="Geographic deployments of sensor hardware."
      bullets={[
        '5 sites around the Bandung highlands',
        'Per-site node count, average severity, and 24h alert count',
        'Region / geohazard metadata (slope, soil type, rainfall regime)',
        'Drill-down to per-site node list',
      ]}
    />
  );
}
