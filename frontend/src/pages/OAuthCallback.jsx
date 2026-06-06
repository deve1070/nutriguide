import { useEffect, useState } from "react";
import { useAuth } from "../lib/auth.jsx";
import { Salad } from "lucide-react";

export default function OAuthCallback() {
  const { loginWithToken } = useAuth();
  const [status, setStatus] = useState("Completing sign in…");
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const accessToken = params.get("access_token");

    if (!accessToken) {
      setError("No token received. Please try signing in again.");
      setTimeout(() => window.location.replace("/login"), 3000);
      return;
    }

    setStatus("Loading your profile…");

    loginWithToken(accessToken).then((result) => {
      if (result.ok) {
        setStatus("Welcome! Taking you in…");
        setTimeout(() => window.location.replace("/app/chat"), 600);
      } else {
        setError(result.error || "Something went wrong. Please try again.");
        setTimeout(() => window.location.replace("/login"), 3000);
      }
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen bg-cream flex items-center justify-center">
      <div className="text-center animate-fade-up max-w-sm px-6">
        {/* Logo */}
        <div className="w-16 h-16 bg-terra rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-glow">
          <Salad size={32} className="text-cream" />
        </div>

        {error ? (
          <>
            <p className="font-display text-xl text-forest mb-2">
              Something went wrong
            </p>
            <p className="text-warmGray text-sm mb-4">{error}</p>
            <p className="text-warmGray text-xs">Redirecting to login…</p>
          </>
        ) : (
          <>
            <p className="font-display text-xl text-forest mb-4">{status}</p>
            {/* Loading dots */}
            <div className="flex justify-center gap-1.5">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-2 h-2 rounded-full bg-terra animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
