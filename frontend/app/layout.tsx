import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import './globals.css'
import AppLayout from '../components/layout/AppLayout'

export const metadata: Metadata = {
  title: 'Orchard OS — Apple Operations Intelligence',
  description: 'Track apple batches, detect quality, predict shelf life, and route every harvest to the right buyer.',
  generator: 'v0.app',
  icons: {
    icon: '/major-project.png',
    shortcut: '/major-project.png',
    apple: '/major-project.png',
  },
}

export const viewport: Viewport = {
  colorScheme: 'light',
  themeColor: '#f5f2eb',
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="bg-background">
      <body className="antialiased">
        <AppLayout>{children}</AppLayout>
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}

