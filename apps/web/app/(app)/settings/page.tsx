import ComingSoon from '@/components/stub/ComingSoon';

export default function SettingsPage() {
  return (
    <ComingSoon
      title="Settings"
      description="User profile, tenant configuration, and notification preferences."
      bullets={[
        'User profile and role display',
        'Tenant information and plan',
        'Notification routing (SMS, email, webhook) configuration',
        'Sign out',
      ]}
    />
  );
}
