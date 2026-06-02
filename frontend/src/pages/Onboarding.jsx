import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { profileApi } from "../lib/api";
import { CheckCircle2, ChevronRight, ChevronLeft } from "lucide-react";
import clsx from "clsx";

const CONDITIONS = [
  { id: "diabetes_type2", label: "Type 2 Diabetes", emoji: "🩸" },
  { id: "hypertension", label: "Hypertension", emoji: "❤️" },
  { id: "chronic_kidney_disease", label: "Kidney Disease", emoji: "🫘" },
  { id: "pcos", label: "PCOS", emoji: "🌸" },
  { id: "celiac", label: "Celiac Disease", emoji: "🌾" },
  { id: "lactose_intolerant", label: "Lactose Intolerant", emoji: "🥛" },
  { id: "heart_disease", label: "Heart Disease", emoji: "💙" },
  { id: "obesity", label: "Obesity", emoji: "⚖️" },
];

const CUISINES = [
  "Ethiopian",
  "Mediterranean",
  "Italian",
  "Asian",
  "Mexican",
  "Indian",
  "American",
  "Japanese",
];
const GOALS = [
  { id: "manage_condition", label: "Manage my condition" },
  { id: "weight_loss", label: "Lose weight" },
  { id: "muscle_gain", label: "Build muscle" },
  { id: "healthy_eating", label: "Eat healthier" },
  { id: "maintenance", label: "Maintain my weight" },
];

const BG =
  "https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=1400&q=80";

function Toggle({
  selected,
  onToggle,
  items,
  idKey = "id",
  labelKey = "label",
  emojiKey,
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => {
        const id = typeof item === "string" ? item : item[idKey];
        const label = typeof item === "string" ? item : item[labelKey];
        const emoji = emojiKey ? item[emojiKey] : null;
        const active = selected.includes(id);
        return (
          <button
            key={id}
            type="button"
            onClick={() => onToggle(id)}
            className={clsx(
              "flex items-center gap-2 px-4 py-2.5 rounded-2xl text-sm font-medium transition-all duration-200",
              active
                ? "bg-terra text-cream shadow-warm"
                : "glass text-warmGray-dark hover:border-terra/30 hover:text-terra",
            )}
          >
            {emoji && <span>{emoji}</span>}
            {label}
            {active && <CheckCircle2 size={14} className="ml-1" />}
          </button>
        );
      })}
    </div>
  );
}

export default function Onboarding() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState({
    conditions: [],
    dietary_restrictions: [],
    allergies: [],
    preferred_cuisines: [],
    primary_goal: "",
    daily_calorie_target: "",
  });

  const toggle = (field) => (id) =>
    setProfile((p) => ({
      ...p,
      [field]: p[field].includes(id)
        ? p[field].filter((x) => x !== id)
        : [...p[field], id],
    }));

  const STEPS = [
    {
      title: "Do you have any health conditions?",
      subtitle:
        "Select all that apply — we'll personalise every recommendation.",
      content: (
        <Toggle
          selected={profile.conditions}
          onToggle={toggle("conditions")}
          items={CONDITIONS}
          emojiKey="emoji"
        />
      ),
    },
    {
      title: "Any dietary restrictions?",
      subtitle: "We'll make sure every suggestion respects these.",
      content: (
        <Toggle
          selected={profile.dietary_restrictions}
          onToggle={toggle("dietary_restrictions")}
          items={[
            "vegan",
            "vegetarian",
            "pescatarian",
            "halal",
            "kosher",
            "gluten_free",
            "dairy_free",
            "nut_free",
          ]}
        />
      ),
    },
    {
      title: "Favourite cuisine styles?",
      subtitle: "We'll lean towards these when generating meal plans.",
      content: (
        <Toggle
          selected={profile.preferred_cuisines}
          onToggle={toggle("preferred_cuisines")}
          items={CUISINES}
        />
      ),
    },
    {
      title: "What's your primary goal?",
      subtitle: "This helps us prioritise the right kind of foods.",
      content: (
        <div className="flex flex-col gap-2">
          {GOALS.map((g) => (
            <button
              key={g.id}
              type="button"
              onClick={() => setProfile((p) => ({ ...p, primary_goal: g.id }))}
              className={clsx(
                "flex items-center justify-between px-5 py-4 rounded-2xl text-sm font-medium transition-all duration-200 text-left",
                profile.primary_goal === g.id
                  ? "bg-terra text-cream shadow-warm"
                  : "glass text-warmGray-dark hover:text-terra",
              )}
            >
              {g.label}
              {profile.primary_goal === g.id && <CheckCircle2 size={18} />}
            </button>
          ))}
        </div>
      ),
    },
    {
      title: "Daily calorie target?",
      subtitle:
        "Optional — leave blank and we'll use condition-based defaults.",
      content: (
        <div className="max-w-xs">
          <input
            type="number"
            className="input-field text-2xl font-display text-center"
            placeholder="e.g. 1800"
            value={profile.daily_calorie_target}
            onChange={(e) =>
              setProfile((p) => ({
                ...p,
                daily_calorie_target: e.target.value,
              }))
            }
            min={800}
            max={4000}
          />
          <p className="text-xs text-warmGray mt-2 text-center">
            calories per day
          </p>
        </div>
      ),
    },
  ];

  const isLast = step === STEPS.length - 1;

  const handleNext = async () => {
    if (!isLast) {
      setStep((s) => s + 1);
      return;
    }

    setSaving(true);
    try {
      await profileApi.update({
        conditions: profile.conditions,
        dietary_restrictions: profile.dietary_restrictions,
        preferred_cuisines: profile.preferred_cuisines,
        primary_goal: profile.primary_goal || undefined,
        daily_calorie_target: profile.daily_calorie_target
          ? parseInt(profile.daily_calorie_target)
          : undefined,
      });
      navigate("/app/chat");
    } catch (e) {
      navigate("/app/chat"); // allow skipping errors
    } finally {
      setSaving(false);
    }
  };

  const progress = ((step + 1) / STEPS.length) * 100;

  return (
    <div className="min-h-screen flex">
      {/* Food image panel */}
      <div className="hidden lg:flex lg:w-2/5 relative flex-col justify-end">
        <img
          src={BG}
          alt=""
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-forest/90 via-forest/40 to-transparent" />
        <div className="relative p-12 text-cream">
          <p className="font-display text-3xl mb-3">
            Built for your body,
            <br />
            not the average body.
          </p>
          <p className="text-cream/60 text-sm leading-relaxed">
            NutriGuide learns your conditions and preferences, then applies
            clinical nutrition science to every recommendation — automatically.
          </p>
        </div>
      </div>

      {/* Form panel */}
      <div className="flex-1 flex flex-col justify-center px-8 py-12 max-w-2xl mx-auto w-full">
        {/* Progress */}
        <div className="mb-10">
          <div className="flex justify-between text-xs text-warmGray mb-2">
            <span>
              Step {step + 1} of {STEPS.length}
            </span>
            <button
              onClick={() => navigate("/app/chat")}
              className="hover:text-terra transition-colors"
            >
              Skip setup →
            </button>
          </div>
          <div className="h-1.5 bg-warmGray/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-terra rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Step content */}
        <div key={step} className="animate-fade-up">
          <h2 className="font-display text-3xl text-forest mb-2">
            {STEPS[step].title}
          </h2>
          <p className="text-warmGray mb-8">{STEPS[step].subtitle}</p>
          {STEPS[step].content}
        </div>

        {/* Navigation */}
        <div className="flex gap-3 mt-10">
          {step > 0 && (
            <button
              onClick={() => setStep((s) => s - 1)}
              className="btn-ghost flex items-center gap-2"
            >
              <ChevronLeft size={16} /> Back
            </button>
          )}
          <button
            onClick={handleNext}
            disabled={saving}
            className="btn-primary flex items-center gap-2 ml-auto"
          >
            {saving ? "Saving…" : isLast ? "Go to NutriGuide →" : "Next"}
            {!saving && !isLast && <ChevronRight size={16} />}
          </button>
        </div>
      </div>
    </div>
  );
}
