export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      boxShadow: {
        soft: '0 20px 60px rgba(15, 23, 42, 0.08)',
      },
      colors: {
        primary: '#5b73ff',
        accent: '#7c3aed',
        surface: '#f8fbff',
      },
    },
  },
  plugins: [],
};
