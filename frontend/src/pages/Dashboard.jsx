import { useQuery } from "@tanstack/react-query";
import { analyticsApi, profileApi } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useState } from "react";
import { Shield, Target, Activity, Edit3, Check, X } from "lucide-react";

const BG =
  "https://images.unsplash.com/photo-1543339308-43e59d6b73a6?w=1400&q=75";

function StatCard({ label, value, sub, icon: Icon, color = "terra" }) {
  const colors = {
    terra: "bg-terra/10 text-terra",
    sage: "bg-sage/10 text-sage",
    amber: "bg-amber/10 text-amber-dark",
  };
  return (
    <div className="card">
      <div
        className={`w-10 h-10 ${colors[color]} rounded-xl flex items-center justify-center mb-4`}
      >
        <Icon size={20} />
      </div>
      <p className="font-display text-3xl text-forest mb-1">{value ?? "—"}</p>
      <p className="text-sm font-medium text-warmGray-dark">{label}</p>
      {sub && <p className="text-xs text-warmGray mt-0.5">{sub}</p>}
    </div>
  );
}

function RuleCard({ rule }) {
  return (
    <div className="card">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-9 h-9 bg-terra/10 rounded-xl flex items-center justify-center">
          <Shield size={16} className="text-terra" />
        </div>
        <p className="font-display text-base text-forest capitalize">
          {rule.condition.replace(/_/g, " ")}
        </p>
      </div>
      <p className="text-xs text-warmGray italic mb-4 leading-relaxed">
        {rule.notes}
      </p>
      <div className="space-y-2">
        <div>
          <p className="text-xs font-medium text-sage mb-1.5">
            ✅ Prioritised foods
          </p>
          <div className="flex flex-wrap gap-1">
            {rule.foods_prioritized.map((f) => (
              <span
                key={f}
                className="tag bg-sage/10 text-sage-dark"
                style={{ fontSize: "10px" }}
              >
                {f}
              </span>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs font-medium text-terra mb-1.5">
            ⚠️ Limited foods
          </p>
          <div className="flex flex-wrap gap-1">
            {rule.foods_limited.map((f) => (
              <span
                key={f}
                className="tag bg-terra/8 text-terra"
                style={{ fontSize: "10px" }}
              >
                {f}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const { data: summary, isLoading } = useQuery({
    queryKey: ["analytics-summary"],
    queryFn: analyticsApi.summary,
  });

  const bmiColor =
    summary?.bmi < 18.5 ? "amber" : summary?.bmi < 25 ? "sage" : "terra";

  return (
    <div className="min-h-full">
      {/* Header image */}
      <div className="relative h-48 overflow-hidden">
        <img src={BG} alt="" className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-b from-forest/50 to-cream" />
        <div className="absolute bottom-6 left-8">
          <p className="text-warmGray/80 text-sm">Welcome back,</p>
          <h1 className="font-display text-3xl text-forest">
            {user?.full_name}
          </h1>
        </div>
      </div>

      <div className="px-8 pb-12 max-w-4xl">
        {isLoading ? (
          <div className="grid grid-cols-3 gap-4 mt-6 animate-pulse">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 bg-warmGray/10 rounded-3xl" />
            ))}
          </div>
        ) : summary ? (
          <div className="animate-fade-up">
            {/* Stats row */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-6 mb-8 stagger">
              <StatCard
                label="Daily calorie target"
                value={
                  summary.daily_calorie_target
                    ? `${summary.daily_calorie_target}`
                    : "Auto"
                }
                sub="calories per day"
                icon={Target}
              />
              <StatCard
                label="BMI"
                value={summary.bmi}
                sub={summary.bmi_category}
                icon={Activity}
                color={bmiColor}
              />
              <StatCard
                label="Active conditions"
                value={summary.conditions?.length || 0}
                sub={
                  summary.personalisation_active
                    ? "Personalisation on"
                    : "No conditions set"
                }
                icon={Shield}
                color="sage"
              />
            </div>

            {/* Profile overview */}
            <div className="card mb-6">
              <p className="font-display text-xl text-forest mb-5">
                Your health profile
              </p>
              <div className="grid md:grid-cols-2 gap-6 text-sm">
                {[
                  { label: "Conditions", values: summary.conditions },
                  {
                    label: "Dietary restrictions",
                    values: summary.dietary_restrictions,
                  },
                  { label: "Allergies", values: summary.allergies },
                  {
                    label: "Preferred cuisines",
                    values: summary.preferred_cuisines,
                  },
                ].map(({ label, values }) => (
                  <div key={label}>
                    <p className="text-xs text-warmGray uppercase tracking-wide mb-2">
                      {label}
                    </p>
                    {values?.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {values.map((v) => (
                          <span
                            key={v}
                            className="tag bg-terra/8 text-terra capitalize"
                          >
                            {v.replace(/_/g, " ")}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p className="text-warmGray italic">Not set</p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Clinical rules in effect */}
            {summary.active_clinical_rules?.length > 0 && (
              <div>
                <p className="font-display text-xl text-forest mb-4">
                  Active nutrition rules
                  <span className="text-sm font-body font-normal text-warmGray ml-2">
                    — how your conditions affect recommendations
                  </span>
                </p>
                <div className="grid md:grid-cols-2 gap-4 stagger">
                  {summary.active_clinical_rules.map((rule) => (
                    <RuleCard key={rule.condition} rule={rule} />
                  ))}
                </div>
              </div>
            )}

            {!summary.personalisation_active && (
              <div className="card text-center py-10">
                <p className="font-display text-xl text-forest mb-2">
                  No conditions set
                </p>
                <p className="text-warmGray text-sm mb-5">
                  Add your health conditions in onboarding to get personalised
                  clinical filtering.
                </p>
                <a href="/app/onboarding" className="btn-primary inline-flex">
                  Update my profile
                </a>
              </div>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
