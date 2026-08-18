/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{html,ts}"],
  theme: {
    extend: {
      colors: {
        citi: {
          headerFrom: "#1D5FE0",
          headerTo: "#0A3B94",
          surface: "#FFFFFF",
          page: "#F5FAFF",
          text: "#0B1B3A",
          muted: "#6B7280",
        },
      },
      boxShadow: {
        card: "0 10px 25px rgba(9, 30, 66, 0.08)",
        soft: "0 6px 18px rgba(9, 30, 66, 0.10)",
      },
      borderRadius: {
        xl2: "1rem",
      },
    },
  },
  plugins: [],
};
