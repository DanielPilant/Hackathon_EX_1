import React from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "../hooks/useTheme";
import { motion } from "framer-motion";

export const ThemeToggle = () => {
  const [theme, setTheme] = useTheme();

  return (
    <motion.button
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="p-2 rounded-full bg-white/80 dark:bg-white/10 border border-gray-200 dark:border-white/10 backdrop-blur-md shadow-lg hover:bg-gray-100 dark:hover:bg-white/20 transition-colors relative overflow-hidden group"
    >
      <div className="relative z-10">
        {theme === "dark" ? (
          <Moon className="w-5 h-5 text-blue-300" />
        ) : (
          <Sun className="w-5 h-5 text-amber-500" />
        )}
      </div>
      <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/20 to-purple-500/20 opacity-0 group-hover:opacity-100 transition-opacity" />
    </motion.button>
  );
};
