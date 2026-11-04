# Accessibility and visual design

ProcurePilot is designed for clear reading across public, account and authenticated workflows. Accessibility is a continuous verification process—not a claim of certified WCAG conformance.

## Three signature colours

| Role | Colour | Hex | Usage |
| --- | --- | --- | --- |
| Background | Whitesmoke | `#F5F5F7` | Calm surface behind high-contrast content |
| Interactive accent | Sky Blue | `#38BDF8` | Focused digital identity, non-text decorative accents, icons |
| Warm emphasis | Sweet Yellow | `#FFD66B` | Primary CTA surfaces, hero underline, selected markers, process steps, alerts and highlighting |
| Contrast anchor | Midnight Navy | `#0B1B3D` | Body headings, dark footer/callouts and text on yellow |

Yellow intentionally appears as a **surface or line**, with navy lettering over it. Small yellow text on white would have insufficient contrast and is prohibited by design. Link blue used on white is a darker `#075CA9`, not the lower-contrast bright Sky Blue token.

Our unit-level WCAG contrast calculation checks the following representative pairs using actual sRGB relative luminance:

- Midnight Navy on Sweet Yellow: approximately 12.18:1
- Dark amber `#704D00` on pale warm yellow `#FFF5D7`: approximately 7.01:1
- Main paragraph `#425570` on white: approximately 7.59:1
- Dock label `#3E536B` on white: approximately 7.91:1
- Link blue `#075CA9` on white: approximately 6.75:1 (AA normal text)
- White text on Midnight Navy: exceeds 14:1

The figures describe these pairs alone, not every pixel over photography or a full audited theme.

## Typography and interaction

- Browser root size: **16px**, with rem units for primary content to respond to user zoom and font settings.
- Main paragraphs, descriptions, form inputs and FAQ copy: generally **15–18px**.
- Compact metadata, timestamps, dock labels and supporting details: generally **12–14px**, with the smallest text reserved for space-constrained interface metadata.
- Visible links, keyboard outlines, clear input boundaries, larger button/touch targets and 1.5–1.8 line-height for extended copy.
- Mobile-first dock on public, sign-in and workspace screens below 961px with iOS safe-area spacing; desktop uses conventional navigation.
- Reduced-motion preference disables decorative entrance animations and carousel auto-rotation while preserving manual slideshow controls.
- Font stack uses common system fonts. No remote webfont is required to read the website.

## User experience review checklist

1. Check public root, all policy/legal pages, sign-in and registration, dashboard, procurement creation, discoveries, order approvals, order details and activity.
2. Exercise 320/375/390/430/768/960px widths and at least 200% and 400% page zoom on Chrome/Firefox/Safari. Confirm **no lost actions, obstructed footer, clipped metadata or unexpected horizontal scrolling**.
3. Inspect with keyboard-only navigation (Tab/Shift+Tab/Enter/Space), NVDA on Windows or VoiceOver on Apple devices. Ensure focus is visible on each control and that status changes are not communicated by color alone.
4. Check high-contrast/forced-colors systems and reduced-motion settings. Inspect actual caption contrast over each slide image, because photographs change tonal distribution.
5. Run the full project verifier. The Node-native `scripts/accessibility-brand.test.mjs` checks selected contrast pairs and essential stylesheet conventions; React navigation and carousel tests check DOM behavior.

## Known limits

Source-level automated checks cannot guarantee full accessibility or universal visual compatibility. The project still needs manual zoom, screen-reader, native-browser, assistive-technology and device testing, especially with long dynamic catalogue entries, changing language and error states. Accessibility improvements should be maintained alongside API security and performance work.
