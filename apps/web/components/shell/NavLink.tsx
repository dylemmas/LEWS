'use client';

import { type LucideIcon } from 'lucide-react';
import Link from 'next/link';

export function NavLink({
  href,
  icon: Icon,
  label,
  active,
}: {
  href: string;
  icon: LucideIcon;
  label: string;
  active: boolean;
}) {
  const base = 'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors';
  const activeClass = active
    ? 'bg-blue-600 text-white'
    : 'text-slate-400 hover:text-white hover:bg-slate-800';

  return (
    <Link href={href} className={`${base} ${activeClass}`}>
      <Icon size={18} />
      {label}
    </Link>
  );
}
