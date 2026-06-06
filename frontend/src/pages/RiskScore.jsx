import { useState } from "react";
import { Activity } from "lucide-react";

export default function RiskScore() {
  const [loading, setLoading] = useState(false);
  const [riskScore, setRiskScore] = useState(null);
  const [error, setError] = useState("");

  const calculateRiskScore = async () => {
    setLoading(true);
    setError("");
    try {
      // TODO: Call API to calculate risk score
      // const data = await riskApi.calculate();
      // setRiskScore(data);
      setRiskScore({
        overall_score: 75,
        risk_factors: [
          { name: "High Blood Pressure", level: "moderate" },
          { name: "Diabetes Risk", level: "low" },
          { name: "Obesity Risk", level: "high" },
        ],
        recommendations: [
          "Reduce sodium intake",
          "Increase physical activity",
          "Maintain balanced diet",
        ],
      });
    } catch (e) {
      setError(
        e.response?.data?.detail ||
          "Failed to calculate risk score. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-12 h-12 bg-terra rounded-2xl flex items-center justify-center">
            <Activity size={24} className="text-cream" />
          </div>
          <div>
            <h1 className="font-display text-2xl text-forest">Meal Risk Score</h1>
            <p className="text-warmGray text-sm">Analyze your meal choices for health risks</p>
          </div>
        </div>

        {!riskScore ? (
          <div className="bg-white rounded-2xl p-8 shadow-sm">
            <div className="text-center">
              <p className="text-warmGray mb-6">
                Calculate your meal risk score based on your health profile and dietary choices.
              </p>
              <button
                onClick={calculateRiskScore}
                disabled={loading}
                className="bg-terra text-cream px-6 py-3 rounded-xl font-medium hover:bg-terra/90 transition-colors disabled:opacity-50"
              >
                {loading ? "Calculating..." : "Calculate Risk Score"}
              </button>
              {error && (
                <p className="text-red-500 mt-4 text-sm">{error}</p>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Overall Score */}
            <div className="bg-white rounded-2xl p-6 shadow-sm">
              <h2 className="font-display text-lg text-forest mb-4">Overall Risk Score</h2>
              <div className="flex items-center gap-4">
                <div className="text-5xl font-bold text-forest">{riskScore.overall_score}</div>
                <div className="text-warmGray">out of 100</div>
              </div>
              <div className="mt-4 h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-terra transition-all"
                  style={{ width: `${riskScore.overall_score}%` }}
                />
              </div>
            </div>

            {/* Risk Factors */}
            <div className="bg-white rounded-2xl p-6 shadow-sm">
              <h2 className="font-display text-lg text-forest mb-4">Risk Factors</h2>
              <div className="space-y-3">
                {riskScore.risk_factors.map((factor, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-xl"
                  >
                    <span className="text-forest">{factor.name}</span>
                    <span
                      className={`px-3 py-1 rounded-full text-sm ${
                        factor.level === "high"
                          ? "bg-red-100 text-red-700"
                          : factor.level === "moderate"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-green-100 text-green-700"
                      }`}
                    >
                      {factor.level}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommendations */}
            <div className="bg-white rounded-2xl p-6 shadow-sm">
              <h2 className="font-display text-lg text-forest mb-4">Recommendations</h2>
              <ul className="space-y-2">
                {riskScore.recommendations.map((rec, index) => (
                  <li key={index} className="flex items-start gap-2">
                    <span className="text-terra mt-1">•</span>
                    <span className="text-warmGray">{rec}</span>
                  </li>
                ))}
              </ul>
            </div>

            <button
              onClick={() => setRiskScore(null)}
              className="w-full bg-gray-100 text-forest px-6 py-3 rounded-xl font-medium hover:bg-gray-200 transition-colors"
            >
              Recalculate
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
