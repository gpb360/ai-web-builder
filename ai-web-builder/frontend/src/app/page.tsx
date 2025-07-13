import { ComponentGenerator } from '@/components/ComponentGenerator';
import { Navigation } from '@/components/Navigation';

export default function Home() {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <main className="pt-16">
        <ComponentGenerator />
      </main>
    </div>
  );
}
