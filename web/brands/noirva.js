// Copyright 2026 Andrei Vorobiev and Virtual Casino Simulator contributors
// SPDX-License-Identifier: Apache-2.0
// NOIRVA's original anime, fantasy and gothic identity; semantic game colors remain readable. (UX-007, PWA-001)
export const noirva = {
  id: "noirva",
  name: "NOIRVA Casino",
  mark: "N",
  venue: "Choose your game",
  direction: "Dark Anime · Fantasy · Goth",
  tokens: {
    "--brand": "#d44555",
    "--brand-strong": "#a92338",
    "--accent": "#d8b979",
    "--accent-2": "#81c3af",
    "--bg": "#080808",
    "--felt": "#131313",
    "--felt2": "#202020",
    "--panel": "rgba(20, 20, 20, 0.94)",
    "--panel-strong": "rgba(8, 8, 8, 0.98)",
    "--border": "rgba(216, 185, 121, 0.22)",
    "--border-soft": "rgba(216, 185, 121, 0.14)",
    "--text": "#f4f0e8",
    "--muted": "#b5b3ae",
    "--radius": "12px",
    "--gold": "#d8b979",
    "--gold-deep": "#ae8747",
    "--glow": "0 8px 24px rgba(169, 35, 56, 0.18)",
  },
  themeColor: "#080808",
};

// Only reviewed original portraits can supply decorative asset paths. (UX-014)
export const NOIRVA_WORLDS = Object.freeze(['witch', 'knight', 'dragon', 'vampire', 'angel', 'spirit', 'dice', 'arcade']);

// Match each game's actual mechanics to its casino props, consistently across all locales.
export function noirvaWorldFor(gameId) {
  if (gameId === 'slots') return 'dragon';
  if (['roulette', 'big_six_wheel', 'color_wheel', 'boule'].includes(gameId)) return 'knight';
  if (['craps', 'sic_bo', 'chuck_a_luck', 'crown_and_anchor', 'over_under_7', 'poker_dice'].includes(gameId)) return 'dice';
  if (['plinko', 'pachinko', 'coin_pusher', 'marble_race'].includes(gameId)) return 'arcade';
  if (['bingo', 'daily_draw_lab'].includes(gameId)) return 'angel';
  if (['keno', 'pattern_draw', 'lucky_grid', 'scratch_cards'].includes(gameId)) return 'spirit';
  if (['baccarat', 'dragon_tiger', 'andar_bahar', 'fan_tan'].includes(gameId)) return 'vampire';
  if (gameId === 'blackjack') return 'witch';
  // Card-table variants alternate between two hosts; both illustrations contain standard cards.
  const seed = [...String(gameId || '')].reduce((total, letter) => total + letter.charCodeAt(0), 0);
  return seed % 2 ? 'witch' : 'vampire';
}
