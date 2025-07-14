import { Navigation } from '@/components/Navigation';

export default function Home() {
  return (
    <div className="min-h-screen bg-black">
      <Navigation />
      <main className="pt-16">
        <div className="max-w-7xl mx-auto px-4 py-20">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-white mb-4">
              Build production-ready components with AI precision
            </h1>
            <p className="text-xl text-gray-400 mb-8">
              Describe your vision and watch as our AI crafts pixel-perfect components.
            </p>
            <button className="btn btn-primary">
              Get Started
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
