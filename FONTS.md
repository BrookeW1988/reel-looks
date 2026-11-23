# Fonts

**No font files are included in this repo.** `_shared/get_fonts.sh <template> <build folder>` downloads what a
template needs, straight from Google Fonts' own repository (or Fontsource, which serves the same fonts one weight at
a time), into that build's `assets/fonts/` folder on your Mac.

| Font | Used by | Licence | Where it comes from |
|---|---|---|---|
| Inter (Bold, ExtraBold, Black, variable) | Just you, Full, Pop-up proof, Before-and-after, Diary of a CEO (optional), Yes... but, default brand font | SIL Open Font Licence 1.1 | https://fonts.google.com/specimen/Inter |
| SF Pro | Just you and Full hooks | Apple's licence: not shared, ever | Copied from your own Mac (`/System/Library/Fonts/SFNS.ttf`) for your own builds only |
| DM Mono | Pop-up proof | SIL OFL 1.1 | https://fonts.google.com/specimen/DM+Mono |
| Bebas Neue | Before-and-after | SIL OFL 1.1 | https://fonts.google.com/specimen/Bebas+Neue |
| JetBrains Mono | Before-and-after, Timestamp vlog | SIL OFL 1.1 | https://fonts.google.com/specimen/JetBrains+Mono |
| Poppins SemiBold | POV skit | SIL OFL 1.1 | https://fonts.google.com/specimen/Poppins |
| EB Garamond (+ italic) | Codie Sanchez | SIL OFL 1.1 | https://fonts.google.com/specimen/EB+Garamond |
| Montserrat | Codie Sanchez (HyperFrames also loads it for the Hormozi looks) | SIL OFL 1.1 | https://fonts.google.com/specimen/Montserrat |
| Anton | Iman Gadzhi, Yes... but | SIL OFL 1.1 | https://fonts.google.com/specimen/Anton |
| Caveat | Iman Gadzhi (installed by `npx hyperframes add hw-write-title`) | SIL OFL 1.1 | https://fonts.google.com/specimen/Caveat |
| Inter Tight | Nana Del Rey | SIL OFL 1.1 | https://fonts.google.com/specimen/Inter+Tight |
| Playfair Display Italic | Nick Saraev | SIL OFL 1.1 | https://fonts.google.com/specimen/Playfair+Display |
| Newsreader | Calm luxury | SIL OFL 1.1 | https://fonts.google.com/specimen/Newsreader |
| Archivo + Archivo Black | Serialised episode | SIL OFL 1.1 | https://fonts.google.com/specimen/Archivo |
| Space Grotesk + Space Mono | Green-screen proof | SIL OFL 1.1 | https://fonts.google.com/specimen/Space+Grotesk |
| Instrument Sans | Text over B-roll | SIL OFL 1.1 | https://fonts.google.com/specimen/Instrument+Sans |
| Instrument Serif Italic | Timestamp vlog | SIL OFL 1.1 | https://fonts.google.com/specimen/Instrument+Serif |
| Poppins, Montserrat, Inter (loaded by HyperFrames) | Hormozi classic, Hormozi 2026, Mariah Brunner | SIL OFL 1.1 | HyperFrames fetches them itself |

The SIL Open Font Licence lets you use these fonts in anything, including commercial reels, free of charge.

**Your brand font:** if it's a font you bought or downloaded, it's yours to use under its own licence. Each skill copies
it into its own build folder (and, in the Edits route, imports it into Edits); it never goes into this repo.

**Emoji:** boxed hooks draw emoji with Apple Color Emoji, which is on every Mac. Optional 3D emoji stickers can come from
Microsoft's Fluent Emoji (MIT licence): https://github.com/microsoft/fluentui-emoji
