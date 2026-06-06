import { useState, useEffect } from "react";
import { mealPlanApi } from "../lib/api";
import {
  Calendar,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Flame,
  Utensils,
  RefreshCw,
} from "lucide-react";
import clsx from "clsx";

const BG =
  "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=1400&q=75";

const MEAL_ICONS = { breakfast: "🌅", lunch: "☀️", dinner: "🌙", snack: "🍎" };

function MealCard({ meal }) {
  return (
    <div className="flex gap-4 items-start py-3 border-b border-warmGray/10 last:border-0">
      <div className="w-10 h-10 bg-cream rounded-xl flex items-center justify-center text-lg shrink-0 shadow-card">
        {MEAL_ICONS[meal.meal_type] || "🍽️"}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className="font-display text-sm text-forest leading-tight">
            {meal.food_name}
          </p>
          <span className="tag bg-amber/10 text-amber-dark text-xs shrink-0">
            <Flame size={10} /> {meal.calories}
          </span>
        </div>
        <p className="text-xs text-warmGray mt-0.5 line-clamp-1">
          {meal.food_description}
        </p>
        <div className="flex gap-1.5 mt-1.5">
          <span
            className="tag bg-terra/8 text-terra"
            style={{ fontSize: "10px" }}
          >
            {meal.cuisine_type}
          </span>
          <span
            className="capitalize tag bg-warmGray/10 text-warmGray"
            style={{ fontSize: "10px" }}
          >
            {meal.meal_type}
          </span>
        </div>
      </div>
    </div>
  );
}

function DayCard({ day, defaultOpen, isCurrentDay }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={`card overflow-hidden ${isCurrentDay ? "ring-2 ring-terra/30" : ""}`}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between gap-4"
      >
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isCurrentDay ? "bg-terra text-cream" : "bg-terra/10"}`}>
            <Calendar size={18} className={isCurrentDay ? "text-cream" : "text-terra"} />
          </div>
          <div className="text-left">
            <p className="font-display text-lg text-forest leading-tight">
              {day.day_name} {isCurrentDay && <span className="text-xs text-terra ml-2">(Today)</span>}
            </p>
            <p className="text-xs text-warmGray">
              Day {day.day} · {day.total_calories} cal
            </p>
          </div>
        </div>
        {open ? (
          <ChevronUp size={18} className="text-warmGray" />
        ) : (
          <ChevronDown size={18} className="text-warmGray" />
        )}
      </button>

      {open && (
        <div className="mt-4 animate-fade-up">
          {day.meals.map((meal, i) => (
            <MealCard key={i} meal={meal} />
          ))}
          {day.daily_notes && (
            <div className="mt-4 p-3 bg-sage/8 rounded-xl">
              <p className="text-xs text-sage-dark italic">
                💡 {day.daily_notes}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function MealPlan() {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [config, setConfig] = useState({ days: 7, meals_per_day: 3 });
  const [currentDayName, setCurrentDayName] = useState("");

  // Get current day name
  useEffect(() => {
    const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    const today = days[new Date().getDay()];
    setCurrentDayName(today);
  }, []);

  // Load current plan on mount
  useEffect(() => {
    const loadCurrentPlan = async () => {
      try {
        const data = await mealPlanApi.getCurrent();
        setPlan(data);
      } catch (e) {
        // No plan exists yet, that's okay
        if (e.response?.status !== 404) {
          console.error("Failed to load current plan:", e);
        }
      }
    };
    loadCurrentPlan();
  }, []);

  const generate = async () => {
    setLoading(true);
    setError("");
    setPlan(null);
    try {
      const data = await mealPlanApi.generate(config);
      setPlan(data);
    } catch (e) {
      setError(
        e.response?.data?.detail ||
          "Failed to generate plan. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-full relative">
      {/* Header image */}
      <div className="relative h-48 overflow-hidden">
        <img src={BG} alt="" className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-b from-forest/60 to-cream" />
        <div className="absolute bottom-6 left-8">
          <h1 className="font-display text-3xl text-forest">Meal Planner</h1>
          <p className="text-warmGray text-sm">
            AI-generated, condition-aware, zero repetition
          </p>
        </div>
      </div>

      <div className="px-8 pb-12 max-w-3xl">
        {/* Config card */}
        <div className="card -mt-4 mb-8">
          <p className="text-sm font-medium text-forest mb-4">
            Configure your plan
          </p>
          <div className="grid grid-cols-2 gap-4 mb-5">
            <div>
              <label className="text-xs text-warmGray block mb-1.5">
                Number of days
              </label>
              <select
                value={config.days}
                onChange={(e) =>
                  setConfig((c) => ({ ...c, days: +e.target.value }))
                }
                className="input-field"
              >
                {[3, 5, 7, 10, 14].map((d) => (
                  <option key={d} value={d}>
                    {d} days
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-warmGray block mb-1.5">
                Meals per day
              </label>
              <select
                value={config.meals_per_day}
                onChange={(e) =>
                  setConfig((c) => ({ ...c, meals_per_day: +e.target.value }))
                }
                className="input-field"
              >
                <option value={2}>2 (Lunch + Dinner)</option>
                <option value={3}>3 (All meals)</option>
                <option value={4}>4 (+ Snack)</option>
              </select>
            </div>
          </div>
          <button
            onClick={generate}
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            <Sparkles size={18} />
            {loading
              ? "Generating your plan…"
              : `Generate ${config.days}-day plan`}
          </button>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="space-y-3 animate-pulse">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-24 bg-warmGray/10 rounded-3xl" />
            ))}
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm px-5 py-4 rounded-2xl mb-6">
            {error}
          </div>
        )}

        {/* Plan output */}
        {plan && !loading && (
          <div className="animate-fade-up">
            {/* Summary */}
            <div className="card mb-6 bg-forest/5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-terra rounded-xl flex items-center justify-center shrink-0">
                    <Utensils size={18} className="text-cream" />
                  </div>
                  <div>
                    <p className="font-display text-lg text-forest mb-1">
                      Your {plan.summary.total_days}-Day Plan
                    </p>
                    <p className="text-xs text-warmGray mb-3">
                      Avg {plan.summary.avg_daily_calories} cal/day ·{" "}
                      {plan.summary.cuisines_included.slice(0, 3).join(", ")}
                    </p>
                    <p className="text-sm text-warmGray-dark leading-relaxed italic">
                      {plan.summary.generation_notes}
                    </p>
                  </div>
                </div>
                <button
                  onClick={generate}
                  disabled={loading}
                  className="btn-secondary flex items-center gap-2 shrink-0"
                  title="Regenerate plan (replaces current)"
                >
                  <RefreshCw size={16} />
                  Regenerate
                </button>
              </div>
            </div>

            {/* Day cards */}
            <div className="flex flex-col gap-4 stagger">
              {plan.days.map((day, i) => (
                <DayCard
                  key={day.day}
                  day={day}
                  defaultOpen={day.day_name === currentDayName}
                  isCurrentDay={day.day_name === currentDayName}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
