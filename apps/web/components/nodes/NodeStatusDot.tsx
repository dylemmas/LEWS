import { NodeStatus } from '@lews/shared-types';
import { cn } from '@/lib/cn';

export function NodeStatusDot({ status }: { status: NodeStatus }) {
  const color = {
    online: 'bg-green-500',
    offline: 'bg-muted',
    degraded: 'bg-yellow-500',
    maintenance: 'bg-blue-500',
  }[status];

  return (
    <div className="flex items-center gap-1.5">
      <span className={cn('h-2 w-2 rounded-full', color)} />
      <span className="text-xs text-muted-foreground capitalize">{status}</span>
    </div>
  );
}
