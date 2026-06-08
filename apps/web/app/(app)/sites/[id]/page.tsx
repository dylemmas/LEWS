import ComingSoon from '@/components/stub/ComingSoon';

export default function SiteDetailPage() {
  return (
    <ComingSoon
      title="Site Detail"
      description="Per-site node inventory and region context."
      bullets={[
        'Deployed nodes with live status and battery',
        'Site-level 24h alert rollup',
        'Geohazard profile (slope, soil, rainfall regime)',
        'Operator notes and historical incident log',
      ]}
    />
  );
}
