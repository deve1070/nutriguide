import { useAuth } from "../../lib/auth";
import { useQuery } from "@tanstack/react-query";
import { authApi } from "../../lib/api";

// Google SVG logo
const GoogleIcon = () => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
  >
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
);

// Facebook SVG logo
const FacebookIcon = () => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"
      fill="#1877F2"
    />
  </svg>
);

export default function SocialAuth({ mode = "login" }) {
  const { loginWithGoogle, loginWithFacebook } = useAuth();

  // Check which providers are configured
  const { data: providers } = useQuery({
    queryKey: ["auth-providers"],
    queryFn: authApi.providers,
    staleTime: Infinity,
    retry: false,
  });

  const googleEnabled = providers?.providers?.find(
    (p) => p.name === "google",
  )?.enabled;
  const facebookEnabled = providers?.providers?.find(
    (p) => p.name === "facebook",
  )?.enabled;

  // Don't render if no providers configured
  if (!googleEnabled && !facebookEnabled) return null;

  const verb = mode === "login" ? "Sign in" : "Sign up";

  return (
    <div className="w-full">
      {/* Divider */}
      <div className="flex items-center gap-3 my-6">
        <div className="flex-1 h-px bg-warmGray/20" />
        <span className="text-xs text-warmGray">or continue with</span>
        <div className="flex-1 h-px bg-warmGray/20" />
      </div>

      {/* Social buttons */}
      <div className="flex flex-col gap-3">
        {googleEnabled && (
          <button
            type="button"
            onClick={loginWithGoogle}
            className="
              flex items-center justify-center gap-3 w-full
              bg-white border border-warmGray/30 rounded-2xl
              px-5 py-3 text-sm font-medium text-warmGray-dark
              shadow-card transition-all duration-200
              hover:border-warmGray/50 hover:shadow-warm hover:-translate-y-0.5
              active:translate-y-0
            "
          >
            <GoogleIcon />
            {verb} with Google
          </button>
        )}

        {facebookEnabled && (
          <button
            type="button"
            onClick={loginWithFacebook}
            className="
              flex items-center justify-center gap-3 w-full
              bg-[#1877F2] rounded-2xl
              px-5 py-3 text-sm font-medium text-white
              shadow-card transition-all duration-200
              hover:bg-[#166FE5] hover:shadow-warm hover:-translate-y-0.5
              active:translate-y-0
            "
          >
            <FacebookIcon />
            {verb} with Facebook
          </button>
        )}
      </div>
    </div>
  );
}
