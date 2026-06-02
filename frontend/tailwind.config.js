import daisyui from 'daisyui'
import typography from '@tailwindcss/typography'

export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  plugins: [typography, daisyui],
  daisyui: {
    themes: ['night'],
  },
}
