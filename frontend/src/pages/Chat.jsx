import { useState, useRef, useEffect } from "react";
import { recommendApi } from "../lib/api";
import { Send, Salad, User, Sparkles, Trash2 } from "lucide-react";
import clsx from "clsx";

const BG =
  "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1400&q=75";

const SUGGESTIONS = [
  "I want something light and healthy for dinner",
  "High-protein breakfast ideas that are quick to make",
  "Comfort food that won't spike my blood sugar",
  "What can I eat if I'm craving something Mediterranean?",
];

function TypingDots() {
  return (
    <div className="flex items-center gap-1 px-4 py-3">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="typing-dot w-2 h-2 rounded-full bg-terra/50 block"
          style={{ animationDelay: `${i * 0.2}s` }}
        />
      ))}
    </div>
  );
}

function FoodCard({ food, index }) {
  return (
    <div
      className="glass rounded-2xl p-4 text-sm animate-slide-in"
      style={{ animationDelay: `${index * 0.08}s`, opacity: 0 }}
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <p className="font-display text-base text-forest leading-tight">
          {food.food_name}
        </p>
        <span className="tag bg-sage/10 text-sage-dark shrink-0">
          {Math.round(food.similarity_score * 100)}% match
        </span>
      </div>
      <p className="text-warmGray text-xs leading-relaxed mb-3 line-clamp-2">
        {food.food_description}
      </p>
      <div className="flex flex-wrap gap-1.5">
        <span className="tag bg-terra/8 text-terra">{food.cuisine_type}</span>
        <span className="tag bg-amber/10 text-amber-dark">
          🔥 {food.food_calories_per_serving} cal
        </span>
        {food.cooking_method && (
          <span className="tag bg-warmGray/10 text-warmGray">
            {food.cooking_method}
          </span>
        )}
      </div>
    </div>
  );
}

function Message({ msg }) {
  const isBot = msg.role === "assistant";
  return (
    <div
      className={clsx(
        "flex gap-3 animate-fade-up",
        isBot ? "items-start" : "items-start flex-row-reverse",
      )}
    >
      <div
        className={clsx(
          "w-8 h-8 rounded-full shrink-0 flex items-center justify-center",
          isBot ? "bg-terra shadow-warm" : "bg-warmGray/20",
        )}
      >
        {isBot ? (
          <Salad size={16} className="text-cream" />
        ) : (
          <User size={16} className="text-warmGray" />
        )}
      </div>

      <div
        className={clsx("max-w-xl flex flex-col gap-3", !isBot && "items-end")}
      >
        <div
          className={clsx(
            "px-5 py-4 rounded-3xl text-sm leading-relaxed",
            isBot
              ? "glass rounded-tl-none text-warmGray-dark"
              : "bg-terra text-cream rounded-tr-none",
          )}
        >
          {msg.content}
        </div>

        {isBot && msg.condition_notes?.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {msg.condition_notes.map((note, i) => (
              <span key={i} className="tag bg-sage/10 text-sage-dark text-xs">
                🩺 {note}
              </span>
            ))}
          </div>
        )}

        {isBot && msg.sources?.length > 0 && (
          <div className="grid gap-2 w-full">
            {msg.sources.map((food, i) => (
              <FoodCard key={food.food_id || i} food={food} index={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // ── Load conversation history on mount ─────────────
  useEffect(() => {
    recommendApi
      .history({ limit: 100 })
      .then((data) => {
        if (data.messages && data.messages.length > 0) {
          // Convert DB messages to display format
          const loaded = data.messages.map((m) => ({
            role: m.role,
            content: m.content,
            sources: m.sources || [],
            condition_notes: [],
          }));
          setMessages(loaded);
        } else {
          // No history — show welcome message
          setMessages([
            {
              role: "assistant",
              content:
                "Hello! 🌿 I'm NutriGuide. Tell me what you're in the mood for, or describe what your body needs right now — I'll find the best food options for you.",
            },
          ]);
        }
      })
      .catch(() => {
        // On error, show welcome message
        setMessages([
          {
            role: "assistant",
            content:
              "Hello! 🌿 I'm NutriGuide. Tell me what you're in the mood for, and I'll find the best food options for you.",
          },
        ]);
      })
      .finally(() => setHistoryLoading(false));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (text) => {
    const query = (text || input).trim();
    if (!query || loading) return;

    setInput("");
    setError("");
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setLoading(true);

    try {
      const data = await recommendApi.chat({ query, n_results: 5 });
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response,
          sources: data.sources,
          condition_notes: data.condition_notes,
          personalized: data.personalized,
        },
      ]);
    } catch (e) {
      setError("Something went wrong. Please try again.");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Sorry, I ran into an issue. Could you try rephrasing your question?",
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const clearHistory = async () => {
    if (!confirm("Clear all conversation history?")) return;
    try {
      await recommendApi.clearHistory();
      setMessages([
        {
          role: "assistant",
          content: "History cleared! 🌿 What can I help you find today?",
        },
      ]);
    } catch {}
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const isFirstMessage =
    messages.length === 1 &&
    messages[0]?.role === "assistant" &&
    !messages[0]?.sources?.length;

  return (
    <div className="h-full flex flex-col relative">
      <div className="absolute inset-0 pointer-events-none">
        <img src={BG} alt="" className="w-full h-full object-cover opacity-5" />
      </div>

      {/* Header */}
      <div className="relative glass border-b border-warmGray/20 px-8 py-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-terra/10 rounded-xl flex items-center justify-center">
            <Sparkles size={18} className="text-terra" />
          </div>
          <div>
            <h1 className="font-display text-xl text-forest">Ask NutriGuide</h1>
            <p className="text-xs text-warmGray">
              Powered by Llama 3.1 · Remembers your conversation
            </p>
          </div>
        </div>

        {messages.length > 1 && (
          <button
            onClick={clearHistory}
            className="flex items-center gap-1.5 text-xs text-warmGray hover:text-terra transition-colors px-3 py-1.5 rounded-xl hover:bg-terra/8"
          >
            <Trash2 size={14} /> Clear history
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="relative flex-1 overflow-y-auto px-8 py-6 flex flex-col gap-6">
        {historyLoading ? (
          <div className="flex justify-center pt-10">
            <div className="flex gap-1.5">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-2 h-2 rounded-full bg-terra/30 animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
          </div>
        ) : (
          <>
            {/* Suggestion chips — only show when no real history */}
            {isFirstMessage && (
              <div className="animate-fade-up">
                <p className="text-xs text-warmGray uppercase tracking-widest mb-3">
                  Try asking
                </p>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => send(s)}
                      className="text-sm glass px-4 py-2.5 rounded-2xl text-warmGray-dark hover:text-terra hover:border-terra/30 transition-all"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <Message key={i} msg={msg} />
            ))}
          </>
        )}

        {loading && (
          <div className="flex gap-3 items-start animate-fade-in">
            <div className="w-8 h-8 rounded-full bg-terra flex items-center justify-center shadow-warm">
              <Salad size={16} className="text-cream" />
            </div>
            <div className="glass rounded-3xl rounded-tl-none">
              <TypingDots />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="relative glass border-t border-warmGray/20 px-6 py-4">
        <div className="flex gap-3 items-end max-w-4xl mx-auto">
          <textarea
            ref={inputRef}
            rows={1}
            className="input-field resize-none flex-1 min-h-[48px] max-h-36"
            placeholder="Ask about a food, ingredient, craving, or health goal…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            onInput={(e) => {
              e.target.style.height = "auto";
              e.target.style.height = e.target.scrollHeight + "px";
            }}
          />
          <button
            onClick={() => send()}
            disabled={!input.trim() || loading}
            className="btn-primary h-12 w-12 flex items-center justify-center p-0 shrink-0"
          >
            <Send size={18} />
          </button>
        </div>
        {error && (
          <p className="text-xs text-red-500 text-center mt-2">{error}</p>
        )}
      </div>
    </div>
  );
}
