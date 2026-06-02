import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { Salad, Eye, EyeOff } from "lucide-react";
import SocialAuth from "../components/ui/SocialAuth";

export default function Login() {
  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    const result = await login(form.email, form.password);
    if (result.ok) navigate("/app/chat");
    else setError(result.error);
  };

  return (
    <div className="min-h-screen flex">
      {/* ── Left: food image ──────────────────────────── */}
      <div className="hidden lg:block lg:w-1/2 relative overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1547592180-85f173990554?w=1200&q=85"
          alt="Fresh vegetables"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-forest/60" />
        <div className="absolute inset-0 flex flex-col justify-end p-12">
          <blockquote className="font-display text-2xl text-cream/90 italic leading-relaxed">
            "Let food be thy medicine and medicine be thy food."
          </blockquote>
          <p className="text-cream/50 text-sm mt-3">— Hippocrates</p>
        </div>
      </div>

      {/* ── Right: form ───────────────────────────────── */}
      <div className="flex-1 flex items-center justify-center px-8 py-12 bg-cream overflow-y-auto">
        <div className="w-full max-w-md animate-fade-up">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 mb-10">
            <div className="w-8 h-8 bg-terra rounded-xl flex items-center justify-center shadow-warm">
              <Salad size={16} className="text-cream" />
            </div>
            <span className="font-display text-lg text-forest">NutriGuide</span>
          </Link>

          <h1 className="font-display text-3xl text-forest mb-1">
            Welcome back
          </h1>
          <p className="text-warmGray mb-8">Sign in to your account</p>

          {/* Social auth — shown first for faster flow */}
          <SocialAuth mode="login" />

          {/* Email / password form */}
          <form onSubmit={handleSubmit} className="flex flex-col gap-4 mt-2">
            <div>
              <label className="text-sm font-medium text-warmGray-dark block mb-1.5">
                Email
              </label>
              <input
                type="email"
                className="input-field"
                placeholder="you@example.com"
                value={form.email}
                onChange={(e) =>
                  setForm((f) => ({ ...f, email: e.target.value }))
                }
                required
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-sm font-medium text-warmGray-dark">
                  Password
                </label>
              </div>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  className="input-field pr-12"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, password: e.target.value }))
                  }
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPw((p) => !p)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-warmGray hover:text-terra transition-colors"
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-4 py-3 rounded-xl">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="btn-primary mt-1"
              disabled={loading}
            >
              {loading ? "Signing in…" : "Sign in with email"}
            </button>
          </form>

          <p className="text-center text-sm text-warmGray mt-8">
            No account?{" "}
            <Link
              to="/register"
              className="text-terra font-medium hover:underline"
            >
              Create one free
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
