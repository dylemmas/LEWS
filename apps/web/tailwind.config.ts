import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './lib/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: 'hsl(220 20% 5%)',
        foreground: 'hsl(220 10% 95%)',
        card: 'hsl(220 18% 9%)',
        'card-foreground': 'hsl(220 10% 95%)',
        border: 'hsl(220 15% 18%)',
        primary: 'hsl(170 90% 45%)',
        'primary-foreground': 'hsl(220 20% 5%)',
        accent: 'hsl(170 60% 30%)',
        muted: 'hsl(220 10% 30%)',
        'muted-foreground': 'hsl(220 10% 65%)',
        destructive: 'hsl(0 80% 55%)',
      },
      fontFamily: {
        sans: ['ui-sans-serif', 'system-ui', 'Inter', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};

export default config;
