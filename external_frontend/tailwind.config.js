/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontSize: {
                'xs': '0.875rem',     // 14px
                'sm': '1rem',         // 16px
                'base': '1.125rem',   // 18px
                'lg': '1.25rem',      // 20px
                'xl': '1.5rem',       // 24px
                '2xl': '1.75rem',     // 28px
                '3xl': '2rem',        // 32px
                '4xl': '2.5rem',      // 40px
                '5xl': '3.5rem',      // 56px
                '6xl': '4rem',        // 64px
            },
            colors: {
                background: '#0B0014', // Deep Violet - Gen Z Base
                surface: '#1A0B2E',    // Lighter Violet
                primary: '#C084FC',    // Soft Lilac / Purple
                secondary: '#2dd4bf',  // Teal
                accent: '#FF719A',     // Pink
                'neon-blue': '#4F46E5', // Electric Blue
                'neon-mint': '#4ADE80',
                'neon-peach': '#F472B6',
                'neon-purple': '#A855F7', // Neon Purple
            },
            fontFamily: {
                sans: ['Outfit', 'sans-serif'],
                display: ['Unbounded', 'sans-serif'], // For headers "Gen-Z Style"
            },
            animation: {
                'blob': 'blob 10s infinite',
                'float': 'float 6s ease-in-out infinite',
                'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'spin-slow': 'spin 8s linear infinite',
            },
            keyframes: {
                blob: {
                    '0%': { transform: 'translate(0px, 0px) scale(1)' },
                    '33%': { transform: 'translate(30px, -50px) scale(1.1)' },
                    '66%': { transform: 'translate(-20px, 20px) scale(0.9)' },
                    '100%': { transform: 'translate(0px, 0px) scale(1)' },
                },
                float: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-20px)' },
                }
            },
            boxShadow: {
                'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.36)',
                'neon': '0 0 10px rgba(192, 132, 252, 0.5), 0 0 20px rgba(192, 132, 252, 0.3)',
            },
        },
    },
    plugins: [],
}
