/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                chalkboard: {
                    dark: '#1a1f2e',
                    DEFAULT: '#2a3447',
                    light: '#3d4b65',
                },
                accent: {
                    yellow: '#f0c83c',
                    orange: '#ffb450',
                    mint: '#64dcb4',
                }
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
