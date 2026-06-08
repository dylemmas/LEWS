import ComingSoon from '@/components/stub/ComingSoon';

export default function AlertsPage() {
  return (
    <ComingSoon
      title="Alerts"
      description="Operator alert feed and acknowledge / resolve workflow."
      bullets={[
        'Open alerts list with severity-sorted ordering',
        'Acknowledge and resolve actions (writes back to API)',
        'Filter by severity, site, and time range',
        'Live updates via Socket.IO when new alerts arrive',
      ]}
    />
  );
}
