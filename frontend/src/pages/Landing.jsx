import { Link } from "react-router-dom";
import { ArrowRight, Shield, Brain, Calendar, Salad } from "lucide-react";

// Curated Unsplash food photos (free to use, no attribution required)
const HERO_IMAGES = [
  "https://images.unsplash.com/photo-1543339308-43e59d6b73a6?w=1600&q=80", // colorful bowls
  "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=1600&q=80", // healthy spread
  "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1600&q=80", // salad bowl
];

const CONDITIONS = [
  "Diabetes",
  "Hypertension",
  "PCOS",
  "Kidney Disease",
  "Celiac",
  "Heart Disease",
];

const FEATURES = [
  {
    icon: Brain,
    title: "RAG-powered intelligence",
    desc: "Semantic search across our food database, then Llama 3.1 crafts a response tailored to your health profile.",
  },
  {
    icon: Shield,
    title: "Clinically-aware filtering",
    desc: "Every recommendation is re-ranked by clinical safety rules for your conditions — not just relevance.",
  },
  {
    icon: Calendar,
    title: "7-day meal planner",
    desc: "Generate a complete week of meals with zero repetition, balanced macros, and condition-safe choices.",
  },
];

export default function Landing() {
  return (
    <div className="min-h-screen font-body overflow-x-hidden">
      {/* ── Hero ──────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col">
        {/* Background image collage */}
        <div className="absolute inset-0 grid grid-cols-3 gap-0">
          {HERO_IMAGES.map((src, i) => (
            <div key={i} className="relative overflow-hidden">
              <img
                src={src}
                alt=""
                className="w-full h-full object-cover scale-105"
                style={{ animationDelay: `${i * 0.3}s` }}
              />
            </div>
          ))}
          {/* Gradient overlay — warm cream wash */}
          <div className="absolute inset-0 bg-gradient-to-b from-cream/95 via-cream/80 to-cream/95" />
          <div className="absolute inset-0 bg-gradient-to-r from-cream/90 via-transparent to-cream/90" />
        </div>

        {/* Nav */}
        <nav className="relative z-10 flex items-center justify-between px-8 py-6">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-terra rounded-xl flex items-center justify-center shadow-warm">
              <Salad size={18} className="text-cream" />
            </div>
            <span className="font-display text-xl text-forest">NutriGuide</span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              to="/login"
              className="text-sm font-medium text-warmGray-dark hover:text-terra transition-colors"
            >
              Sign in
            </Link>
            <Link to="/register" className="btn-primary text-sm py-2 px-5">
              Get started free
            </Link>
          </div>
        </nav>

        {/* Hero copy */}
        <div className="relative z-10 flex-1 flex flex-col items-center justify-center text-center px-6 pb-20">
          <div className="animate-fade-up">
            <p className="tag bg-terra/10 text-terra mb-6 mx-auto">
              🌿 Clinical Nutrition Intelligence
            </p>
            <h1 className="font-display text-5xl md:text-7xl text-forest leading-tight mb-6 max-w-3xl">
              Food that <em className="text-terra not-italic">understands</em>
              <br />
              your health
            </h1>
            <p className="text-lg text-warmGray-dark max-w-xl mx-auto mb-10 leading-relaxed">
              Personalized recommendations powered by AI — designed for people
              living with diabetes, hypertension, PCOS, and other conditions.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/register"
                className="btn-primary flex items-center gap-2 justify-center"
              >
                Start for free <ArrowRight size={18} />
              </Link>
              <Link
                to="/login"
                className="btn-ghost flex items-center gap-2 justify-center"
              >
                I already have an account
              </Link>
            </div>

            {/* Quick OAuth on landing */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center mt-4">
              <a
                href={`${import.meta.env.VITE_API_URL || "http://localhost:8002"}/auth/google/login`}
                className="flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-white/80 border border-warmGray/20 text-sm font-medium text-warmGray-dark hover:border-warmGray/40 hover:shadow-card transition-all"
              >
                <svg width="16" height="16" viewBox="0 0 24 24">
                  <path
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    fill="#4285F4"
                  />
                  <path
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    fill="#34A853"
                  />
                  <path
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    fill="#FBBC05"
                  />
                  <path
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    fill="#EA4335"
                  />
                </svg>
                Continue with Google
              </a>
              <a
                href={`${import.meta.env.VITE_API_URL || "http://localhost:8002"}/auth/facebook/login`}
                className="flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-[#1877F2] text-sm font-medium text-white hover:bg-[#166FE5] hover:shadow-card transition-all"
              >
                <svg width="16" height="16" viewBox="0 0 24 24">
                  <path
                    d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"
                    fill="white"
                  />
                </svg>
                Continue with Facebook
              </a>
            </div>
          </div>

          {/* Condition pills */}
          <div
            className="mt-14 animate-fade-up"
            style={{ animationDelay: "0.3s", opacity: 0 }}
          >
            <p className="text-xs text-warmGray mb-3 uppercase tracking-widest">
              Supports
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {CONDITIONS.map((c) => (
                <span
                  key={c}
                  className="tag bg-white/70 text-warmGray-dark border border-warmGray/20 shadow-card"
                >
                  {c}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ──────────────────────────────────── */}
      <section className="relative py-24 px-6">
        {/* Subtle food image strip */}
        <div className="absolute inset-0 overflow-hidden opacity-10">
          <img
            src="https://images.unsplash.com/photo-1506368249639-73a05d6f6488?w=1600&q=60"
            alt=""
            className="w-full h-full object-cover"
          />
        </div>
        <div className="relative max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display text-4xl text-forest mb-4">
              Not just recommendations.
              <br />
              <em className="text-terra">Clinical intelligence.</em>
            </h2>
            <p className="text-warmGray max-w-lg mx-auto">
              We combine vector similarity search, clinical safety rules, and a
              large language model so every answer is both relevant and safe.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 stagger">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="card group">
                <div className="w-12 h-12 bg-terra/10 rounded-2xl flex items-center justify-center mb-5 group-hover:bg-terra/20 transition-colors">
                  <Icon size={22} className="text-terra" />
                </div>
                <h3 className="font-display text-xl text-forest mb-3">
                  {title}
                </h3>
                <p className="text-sm text-warmGray leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────── */}
      <section className="relative py-24 px-6 overflow-hidden">
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=1600&q=80"
            alt=""
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-forest/85" />
        </div>
        <div className="relative text-center max-w-2xl mx-auto">
          <h2 className="font-display text-4xl text-cream mb-4">
            Ready to eat with purpose?
          </h2>
          <p className="text-cream/70 mb-10">
            Free to use. No card required. Start with your health profile in
            under 2 minutes.
          </p>
          <Link
            to="/register"
            className="inline-flex items-center gap-2 bg-terra text-cream px-8 py-4 rounded-2xl font-medium shadow-glow hover:bg-terra-light transition-all hover:-translate-y-0.5"
          >
            Create your profile <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 text-center text-xs text-warmGray border-t border-warmGray/20">
        © 2026 NutriGuide — Built with FastAPI · ChromaDB · Groq Llama 3.1
      </footer>
    </div>
  );
}
