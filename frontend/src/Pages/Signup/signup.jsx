import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");   // ✅ new state
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const res = await fetch("http://localhost:8000/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, username, password }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Signup failed");
      }

      navigate("/login");
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
          Create Account
        </h1>
        <p className="text-center text-gray-500 mt-2 text-base md:text-lg">
          Get started with image diffusion today
        </p>

        <form className="mt-8 space-y-4" onSubmit={handleSignup}>
          {error && (
            <p className="text-red-500 text-center font-medium">{error}</p>
          )}

          {/* ✅ Username field */}
          <div>
            <label className="block text-gray-700 font-medium mb-2 text-base">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#233975ff] text-base"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 font-medium mb-2 text-base">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter email"
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

          <div>
            <label className="block text-gray-700 font-medium mb-2 text-base">
              Confirm Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm password"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#233975ff] text-base"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gray-900 text-white py-3 rounded-lg font-semibold hover:bg-gray-800 transition-colors text-base"
          >
            {loading ? "Signing up..." : "Sign Up"}
          </button>
        </form>

        <p className="text-center text-gray-500 mt-6 text-base">
          Already have an account?{" "}
          <button
            onClick={() => navigate("/login")}
            className="text-[#233975ff] hover:underline"
          >
            Login
          </button>
        </p>
        <p className="text-center text-gray-500 mt-4 text-base">
          Back to{" "}
          <button
            onClick={() => navigate("/")}
            className="text-[#233975ff] hover:underline"
          >
            Homepage
          </button>
        </p>
      </div>
    </div>
  );
}
