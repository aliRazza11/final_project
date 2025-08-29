import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";

export default function LoginPage() {
  const [email, setEmail] = useState(""); 
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

 useEffect(() => {
  (async () => {
    try {
      const res = await fetch("http://localhost:8000/auth/me", {
        credentials: "include",
      });
      if (res.ok) {
        console.log("Already logged in, clearing session");
        await fetch("http://localhost:8000/auth/logout", {
          method: "POST",
          credentials: "include",
        });
        localStorage.removeItem("token");
        sessionStorage.removeItem("token");
      }
    } catch (err) {
      console.error("Error checking session:", err);
    }
  })();
}, []);


  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }), 
        credentials: "include",
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error("Invalid username / Password" || errData.detail);
      }

      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
      <div className="w-full max-w-xl bg-white rounded-2xl shadow-xl p-8 sm:p-12 border border-gray-200">
        <h1 className="text-3xl md:text-4xl font-bold text-center text-gray-900">
          Welcome Back
        </h1>
        <p className="text-center text-gray-500 mt-2 text-base md:text-lg">
          Enter your credentials to continue
        </p>

        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          <div>
            <label className="block text-gray-700 font-medium mb-2 text-base">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#233975ff] text-base"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 font-medium mb-2 text-base">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#233975ff] text-base"
              required
            />
          </div>

          {error && <p className="text-red-500 text-sm text-center">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gray-900 text-white py-3 rounded-lg font-semibold hover:bg-gray-800 transition-colors text-base disabled:opacity-50"
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
}
