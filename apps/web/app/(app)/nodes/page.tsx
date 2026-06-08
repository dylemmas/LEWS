import ComingSoon from '@/components/stub/ComingSoon';

export default function NodesPage() {
  return (
    <ComingSoon
      title="Sensor Nodes"
      description="Full inventory of deployed IoT hardware across all sites."
      bullets={[
        'Searchable and filterable node table (15 nodes across 5 sites)',
        'Per-node status, battery, last-seen, and severity',
        'Bulk operations: reboot, recalibrate, mark for maintenance',
        'Drill-down to per-node sensor detail (24h time-series)',
      ]}
    />
  );
}
