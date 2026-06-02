import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { Salad } from "lucide-react";
import SocialAuth from "../components/ui/SocialAuth";

export default function Register() {
  const { register, loading } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ fullName: "", email: "", password: "" });
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    const result = await register(form.email, form.fullName, form.password);
    if (result.ok) navigate("/app/onboarding");
    else setError(result.error);
  };

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  return (
    <div className="min-h-screen flex">
      {/* ── Left: food image ──────────────────────────── */}
      <div className="hidden lg:block lg:w-1/2 relative overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1200&q=85"
          alt="Healthy food spread"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-forest/70 to-terra-dark/50" />
        <div className="absolute inset-0 flex flex-col justify-center p-12">
          <div className="glass rounded-3xl p-8 max-w-sm">
            <p className="font-display text-2xl text-forest mb-3">
              Personalized to <em className="text-terra">you</em>
            </p>
            <p className="text-sm text-warmGray-dark leading-relaxed">
              Tell us about your health conditions once. Every recommendation
              and meal plan will account for them automatically.
            </p>

            {/* Trust indicators */}
            <div className="mt-6 flex flex-col gap-2">
              {[
                "🔒 Your health data is private",
                "✅ No credit card required",
                "🌿 Free forever on basic plan",
              ].map((t) => (
                <p key={t} className="text-xs text-warmGray-dark">
                  {t}
                </p>
              ))}
            </div>
          </div>
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
            Create your account
          </h1>
          <p className="text-warmGray mb-2">Free — no credit card needed</p>

          {/* Social auth — fastest path to signup */}
          <SocialAuth mode="register" />

          {/* Email form */}
          <form onSubmit={handleSubmit} className="flex flex-col gap-4 mt-2">
            {[
              {
                label: "Full name",
                key: "fullName",
                type: "text",
                placeholder: "Amara Tadesse",
              },
              {
                label: "Email",
                key: "email",
                type: "email",
                placeholder: "you@example.com",
              },
              {
                label: "Password",
                key: "password",
                type: "password",
                placeholder: "Min 8 characters",
              },
            ].map(({ label, key, type, placeholder }) => (
              <div key={key}>
                <label className="text-sm font-medium text-warmGray-dark block mb-1.5">
                  {label}
                </label>
                <input
                  type={type}
                  className="input-field"
                  placeholder={placeholder}
                  value={form[key]}
                  onChange={set(key)}
                  required
                  minLength={key === "password" ? 8 : undefined}
                />
              </div>
            ))}

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
              {loading ? "Creating account…" : "Create account with email"}
            </button>
          </form>

          <p className="text-xs text-warmGray text-center mt-4 leading-relaxed">
            By creating an account you agree to our{" "}
            <span className="text-terra cursor-pointer hover:underline">
              Terms
            </span>{" "}
            and{" "}
            <span className="text-terra cursor-pointer hover:underline">
              Privacy Policy
            </span>
            .
          </p>

          <p className="text-center text-sm text-warmGray mt-6">
            Already have an account?{" "}
            <Link
              to="/login"
              className="text-terra font-medium hover:underline"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
